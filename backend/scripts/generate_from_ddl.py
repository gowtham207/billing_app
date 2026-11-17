"""Generate SQLAlchemy models and Pydantic schemas from database/ddl.sql."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DDL_PATH = ROOT / "database" / "ddl.sql"
MODELS_PATH = ROOT / "backend" / "app" / "models" / "generated.py"
SCHEMAS_PATH = ROOT / "backend" / "app" / "schemas" / "generated.py"

ALWAYS_EXCLUDE_WRITE = {"id", "organization_id", "created_at", "updated_at", "archived_at"}
EXTRA_EXCLUDE_WRITE = {
    "users": {"password_hash", "is_platform_admin", "email_verified_at", "last_login_at"},
}
EXCLUDE_READ = {
    "users": {"password_hash"},
}
CLASS_OVERRIDES = {
    "billing_settings": "BillingSettings",
    "analysis_settings": "AnalysisSettings",
    "warehouses": "Warehouse",
    "expenses": "Expense",
}


def singular(name: str) -> str:
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith(("sses", "xes", "ches", "shes", "ses")):
        return name[:-2]
    if name.endswith("s") and not name.endswith("ss"):
        return name[:-1]
    return name


def class_name(table: str) -> str:
    if table in CLASS_OVERRIDES:
        return CLASS_OVERRIDES[table]
    return "".join(part.capitalize() for part in singular(table).split("_"))


def extract_tables(sql: str) -> list[tuple[str, str]]:
    tables: list[tuple[str, str]] = []
    for match in re.finditer(r"CREATE TABLE app\.(\w+)\s*\(", sql):
        start = match.end()
        depth = 1
        index = start
        while index < len(sql) and depth:
            if sql[index] == "(":
                depth += 1
            elif sql[index] == ")":
                depth -= 1
            index += 1
        tables.append((match.group(1), sql[start : index - 1]))
    return tables


def split_parts(body: str) -> list[str]:
    parts: list[str] = []
    buffer: list[str] = []
    depth = 0
    in_quote = False
    index = 0
    while index < len(body):
        char = body[index]
        if in_quote:
            buffer.append(char)
            if char == "'" and index + 1 < len(body) and body[index + 1] == "'":
                buffer.append("'")
                index += 2
                continue
            if char == "'":
                in_quote = False
            index += 1
            continue
        if char == "'":
            in_quote = True
            buffer.append(char)
        elif char == "(":
            depth += 1
            buffer.append(char)
        elif char == ")":
            depth -= 1
            buffer.append(char)
        elif char == "," and depth == 0:
            part = "".join(buffer).strip()
            if part:
                parts.append(part)
            buffer = []
        else:
            buffer.append(char)
        index += 1
    tail = "".join(buffer).strip()
    if tail:
        parts.append(tail)
    return parts


def extract_paren(text: str, open_index: int) -> tuple[str, int]:
    depth = 0
    for index in range(open_index, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : index], index + 1
    raise ValueError(f"Unbalanced parentheses in {text!r}")


def extract_checks(text: str) -> list[str]:
    checks: list[str] = []
    for match in re.finditer(r"\bCHECK\s*\(", text, flags=re.I):
        expression, _ = extract_paren(text, match.end() - 1)
        checks.append(expression.strip())
    return checks


TYPE_RE = re.compile(
    r"^(uuid|text|boolean|integer|smallint|bigint|bigserial|date|timestamptz|jsonb|inet|"
    r"varchar\(\d+\)|char\(\d+\)|numeric\(\d+,\s*\d+\))",
    re.I,
)


def sqlalchemy_type(sql_type: str) -> tuple[str, str]:
    lowered = re.sub(r"\s+", "", sql_type.lower())
    if lowered == "uuid":
        return "UUID(as_uuid=True)", "uuid.UUID"
    if lowered == "text":
        return "Text()", "str"
    if lowered == "boolean":
        return "Boolean()", "bool"
    if lowered == "integer":
        return "Integer()", "int"
    if lowered == "smallint":
        return "SmallInteger()", "int"
    if lowered == "bigint":
        return "BigInteger()", "int"
    if lowered == "bigserial":
        return "BigInteger()", "int"
    if lowered == "date":
        return "Date()", "date"
    if lowered == "timestamptz":
        return "DateTime(timezone=True)", "datetime"
    if lowered == "jsonb":
        return "JSONB()", "Any"
    if lowered == "inet":
        return "INET()", "str"
    varchar = re.fullmatch(r"varchar\((\d+)\)", lowered)
    if varchar:
        return f"String({varchar.group(1)})", "str"
    char = re.fullmatch(r"char\((\d+)\)", lowered)
    if char:
        return f"CHAR({char.group(1)})", "str"
    numeric = re.fullmatch(r"numeric\((\d+),(\d+)\)", lowered)
    if numeric:
        return f"Numeric({numeric.group(1)}, {numeric.group(2)})", "Decimal"
    raise ValueError(f"Unsupported SQL type {sql_type}")


def literal_for(column: str, checks: list[str]) -> str | None:
    pattern = re.compile(rf"^{re.escape(column)}\s+IN\s*\((.+)\)$", re.I | re.S)
    for check in checks:
        match = pattern.match(re.sub(r"\s+", " ", check).strip())
        if not match:
            continue
        values = re.findall(r"'([^']*)'", match.group(1))
        if values:
            inner = ", ".join(repr(value) for value in values)
            return f"Literal[{inner}]"
    return None


def parse_column(part: str) -> dict:
    match = re.match(r"^(\w+)\s+(.*)$", part, flags=re.S)
    if not match:
        raise ValueError(f"Cannot parse column {part}")
    name = match.group(1)
    rest = match.group(2).strip()
    type_match = TYPE_RE.match(rest)
    if not type_match:
        raise ValueError(f"Cannot parse type for {name}: {rest}")
    sql_type = type_match.group(1)
    tail = rest[type_match.end() :].strip()
    generated = None
    generated_match = re.search(r"GENERATED\s+ALWAYS\s+AS\s*\(", tail, flags=re.I)
    if generated_match:
        generated, end = extract_paren(tail, generated_match.end() - 1)
        tail = (tail[: generated_match.start()] + " " + tail[end:]).strip()
        generated = generated.strip()
    checks = extract_checks(part)
    primary_key = bool(re.search(r"\bPRIMARY\s+KEY\b", tail, flags=re.I))
    not_null = primary_key or bool(re.search(r"\bNOT\s+NULL\b", tail, flags=re.I))
    unique = bool(re.search(r"\bUNIQUE\b", tail, flags=re.I))
    reference = None
    ref_match = re.search(
        r"REFERENCES\s+app\.(\w+)\s*\(([^)]+)\)(?:\s+ON\s+DELETE\s+(CASCADE|RESTRICT|SET\s+NULL|SET\s+DEFAULT))?",
        tail,
        flags=re.I,
    )
    if ref_match:
        reference = {
            "table": ref_match.group(1),
            "columns": [piece.strip() for piece in ref_match.group(2).split(",")],
            "ondelete": re.sub(r"\s+", " ", (ref_match.group(3) or "RESTRICT").upper()),
        }
    default_sql = None
    default_match = re.search(r"\bDEFAULT\b", tail, flags=re.I)
    if default_match:
        default_sql = tail[default_match.end() :].strip()
        for keyword in ("NOT NULL", "NULL", "PRIMARY KEY", "REFERENCES", "UNIQUE", "CHECK"):
            found = re.search(rf"\b{keyword}\b", default_sql, flags=re.I)
            if found:
                default_sql = default_sql[: found.start()].strip()
        default_sql = default_sql.strip()
    return {
        "name": name,
        "sql_type": sql_type,
        "primary_key": primary_key,
        "not_null": not_null,
        "unique": unique,
        "reference": reference,
        "default_sql": default_sql,
        "generated": generated,
        "checks": checks,
        "identity": sql_type.lower() == "bigserial",
    }


def parse_table_constraint(part: str) -> dict | None:
    compact = re.sub(r"\s+", " ", part).strip()
    if re.match(r"PRIMARY\s+KEY\s*\(", compact, flags=re.I):
        columns, _ = extract_paren(compact, compact.index("("))
        return {"kind": "primary", "columns": [c.strip() for c in columns.split(",")]}
    if re.match(r"UNIQUE\s*\(", compact, flags=re.I):
        columns, _ = extract_paren(compact, compact.index("("))
        return {"kind": "unique", "columns": [c.strip() for c in columns.split(",")]}
    if re.match(r"FOREIGN\s+KEY\s*\(", compact, flags=re.I):
        local, after = extract_paren(compact, compact.index("("))
        ref_match = re.search(
            r"REFERENCES\s+app\.(\w+)\s*\(([^)]+)\)(?:\s+ON\s+DELETE\s+(CASCADE|RESTRICT|SET NULL|SET DEFAULT))?",
            compact[after:],
            flags=re.I,
        )
        if not ref_match:
            raise ValueError(f"Bad foreign key {part}")
        return {
            "kind": "foreign",
            "columns": [c.strip() for c in local.split(",")],
            "table": ref_match.group(1),
            "ref_columns": [c.strip() for c in ref_match.group(2).split(",")],
            "ondelete": (ref_match.group(3) or "RESTRICT").upper(),
        }
    if re.match(r"CHECK\s*\(", compact, flags=re.I):
        expression, _ = extract_paren(compact, compact.index("("))
        return {"kind": "check", "expression": expression.strip()}
    return None


def parse_table(name: str, body: str) -> dict:
    columns = []
    constraints = []
    for part in split_parts(body):
        if re.match(r"(PRIMARY\s+KEY|UNIQUE|FOREIGN\s+KEY|CHECK|CONSTRAINT)\b", part, flags=re.I):
            parsed = parse_table_constraint(part)
            if parsed:
                constraints.append(parsed)
            continue
        columns.append(parse_column(part))
    pk_columns = [column["name"] for column in columns if column["primary_key"]]
    for constraint in constraints:
        if constraint["kind"] == "primary":
            pk_columns = constraint["columns"]
            for column in columns:
                column["primary_key"] = column["name"] in pk_columns
    return {"name": name, "class_name": class_name(name), "columns": columns, "constraints": constraints, "primary_key": pk_columns}


def column_expr(column: dict, single_unique: set[str]) -> str:
    sa_type, _ = sqlalchemy_type(column["sql_type"])
    args = [sa_type]
    kwargs: list[str] = []
    if column["primary_key"]:
        kwargs.append("primary_key=True")
    if column["identity"]:
        args.append("Identity()")
    if column["generated"]:
        args.append(f"Computed({column['generated']!r}, persisted=True)")
    elif column["reference"] and len(column["reference"]["columns"]) == 1:
        ref = column["reference"]
        target = f"app.{ref['table']}.{ref['columns'][0]}"
        args.append(f"ForeignKey({target!r}, ondelete={ref['ondelete']!r})")
    if (column["unique"] or column["name"] in single_unique) and not column["primary_key"]:
        kwargs.append("unique=True")
    if not column["not_null"]:
        kwargs.append("nullable=True")
    else:
        kwargs.append("nullable=False")
    if column["default_sql"] and not column["generated"]:
        kwargs.append(f"server_default=text({column['default_sql']!r})")
    if column["default_sql"] and "gen_random_uuid" in column["default_sql"]:
        kwargs.append("default=uuid.uuid4")
    if column["name"] == "updated_at":
        kwargs.append("onupdate=func.now()")
    inner = ", ".join(args + kwargs)
    return f"mapped_column({inner})"


def annotation(column: dict, checks: list[str], *, optional: bool, literals: bool = True) -> str:
    literal = literal_for(column["name"], checks) if literals else None
    _, py_type = sqlalchemy_type(column["sql_type"])
    base = literal or py_type
    if optional or not column["not_null"]:
        if base.endswith("| None"):
            return base
        return f"{base} | None"
    return base


def render_models(tables: list[dict]) -> str:
    lines = [
        '"""SQLAlchemy models generated from database/ddl.sql. Do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
        "import uuid",
        "from datetime import date, datetime",
        "from decimal import Decimal",
        "from typing import Any",
        "",
        "from sqlalchemy import (",
        "    CHAR,",
        "    BigInteger,",
        "    Boolean,",
        "    CheckConstraint,",
        "    Computed,",
        "    Date,",
        "    DateTime,",
        "    ForeignKey,",
        "    ForeignKeyConstraint,",
        "    Identity,",
        "    Integer,",
        "    Numeric,",
        "    SmallInteger,",
        "    String,",
        "    Text,",
        "    UniqueConstraint,",
        "    func,",
        "    text,",
        ")",
        "from sqlalchemy.dialects.postgresql import INET, JSONB, UUID",
        "from sqlalchemy.orm import Mapped, mapped_column",
        "",
        "from app.models.base import Base",
        "",
    ]
    for table in tables:
        single_unique = {
            constraint["columns"][0]
            for constraint in table["constraints"]
            if constraint["kind"] == "unique" and len(constraint["columns"]) == 1
        }
        table_args: list[str] = []
        check_index = 0
        for column in table["columns"]:
            for expression in column["checks"]:
                cname = f"ck_{table['name']}_{column['name']}_{check_index}"[:63]
                table_args.append(f"CheckConstraint({expression!r}, name={cname!r})")
                check_index += 1
        for index, constraint in enumerate(table["constraints"]):
            if constraint["kind"] == "unique" and len(constraint["columns"]) > 1:
                cols = ", ".join(repr(col) for col in constraint["columns"])
                cname = f"uq_{table['name']}_{'_'.join(constraint['columns'])}"[:63]
                table_args.append(f"UniqueConstraint({cols}, name={cname!r})")
            elif constraint["kind"] == "foreign":
                local = ", ".join(repr(col) for col in constraint["columns"])
                remote = ", ".join(
                    repr(f"app.{constraint['table']}.{col}") for col in constraint["ref_columns"]
                )
                cname = f"fk_{table['name']}_{'_'.join(constraint['columns'])}"[:63]
                table_args.append(
                    "ForeignKeyConstraint("
                    f"[{local}], [{remote}], ondelete={constraint['ondelete']!r}, name={cname!r})"
                )
            elif constraint["kind"] == "check":
                cname = f"ck_{table['name']}_{index}"[:63]
                table_args.append(f"CheckConstraint({constraint['expression']!r}, name={cname!r})")
        lines.append(f"class {table['class_name']}(Base):")
        lines.append(f"    __tablename__ = {table['name']!r}")
        if table_args:
            lines.append("    __table_args__ = (")
            for arg in table_args:
                lines.append(f"        {arg},")
            lines.append('        {"schema": "app"},')
            lines.append("    )")
        else:
            lines.append('    __table_args__ = {"schema": "app"}')
        lines.append("")
        for column in table["columns"]:
            lines.append(
                "    "
                + column["name"]
                + ": Mapped["
                + annotation(column, column["checks"], optional=not column["not_null"], literals=False)
                + "] = "
                + column_expr(column, single_unique)
            )
        lines.append("")
        lines.append("")
    lines.append("GENERATED_MODELS = {")
    for table in tables:
        lines.append(f"    {table['name']!r}: {table['class_name']},")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def render_schemas(tables: list[dict]) -> str:
    literal_needed = False
    body: list[str] = []
    for table in tables:
        checks = [column_check for column in table["columns"] for column_check in column["checks"]]
        checks.extend(c["expression"] for c in table["constraints"] if c["kind"] == "check")
        read_fields = []
        create_fields = []
        update_fields = []
        excluded_write = set(ALWAYS_EXCLUDE_WRITE)
        excluded_write.update(EXTRA_EXCLUDE_WRITE.get(table["name"], set()))
        for column in table["columns"]:
            if column["generated"]:
                excluded_write.add(column["name"])
        for column in table["columns"]:
            if column["name"] in EXCLUDE_READ.get(table["name"], set()):
                continue
            optional_read = not column["not_null"]
            read_type = annotation(column, checks, optional=optional_read)
            if read_type.startswith("Literal["):
                literal_needed = True
            read_fields.append(f"    {column['name']}: {read_type}")
            if column["name"] in excluded_write or column["generated"]:
                continue
            has_default = bool(column["default_sql"] or column["identity"])
            required = column["not_null"] and not has_default
            create_type = annotation(column, checks, optional=not required)
            if create_type.startswith("Literal["):
                literal_needed = True
            if required:
                create_fields.append(f"    {column['name']}: {create_type}")
            else:
                create_fields.append(f"    {column['name']}: {create_type} = None")
            update_type = create_type if create_type.endswith("| None") else f"{create_type} | None"
            update_fields.append(f"    {update_type and column['name']}: {update_type} = None".replace(
                f"{update_type and column['name']}", column["name"]
            ) if False else f"    {column['name']}: {update_type} = None")
        cls = table["class_name"]
        body.append(f"class {cls}Read(AppSchema):")
        body.extend(read_fields or ["    pass"])
        body.append("")
        body.append("")
        body.append(f"class {cls}Create(AppSchema):")
        body.extend(create_fields or ["    pass"])
        body.append("")
        body.append("")
        body.append(f"class {cls}Update(AppSchema):")
        body.extend(update_fields or ["    pass"])
        body.append("")
        body.append("")
    header = [
        '"""Pydantic schemas generated from database/ddl.sql. Do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
        "import uuid",
        "from datetime import date, datetime",
        "from decimal import Decimal",
        "from typing import Any" + (", Literal" if literal_needed else ""),
        "",
        "from app.schemas.base import AppSchema",
        "",
    ]
    return "\n".join(header + body)


def main() -> None:
    sql = DDL_PATH.read_text(encoding="utf-8")
    tables = [parse_table(name, body) for name, body in extract_tables(sql)]
    if len(tables) < 80:
        raise SystemExit(f"Expected the full schema, parsed {len(tables)} tables")
    MODELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEMAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODELS_PATH.write_text(render_models(tables), encoding="utf-8")
    SCHEMAS_PATH.write_text(render_schemas(tables), encoding="utf-8")
    print(f"generated {len(tables)} tables -> {MODELS_PATH.name}, {SCHEMAS_PATH.name}")


if __name__ == "__main__":
    main()
