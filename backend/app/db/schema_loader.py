"""Apply the SQL schema files through a superuser connection."""

from __future__ import annotations

import os
import re
from pathlib import Path

_DOLLAR = re.compile(r"\$[A-Za-z0-9_]*\$")


def sql_dir() -> Path:
    configured = os.environ.get("SQL_DIR")
    candidates = []
    if configured:
        candidates.append(Path(configured))
    here = Path(__file__).resolve()
    candidates.extend(
        [
            Path("/database"),
            here.parents[3] / "database",
            here.parents[2] / "database",
        ]
    )
    for candidate in candidates:
        if (candidate / "ddl.sql").exists():
            return candidate
    raise FileNotFoundError("Could not find database/ddl.sql")


def split_sql(script: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    index = 0
    length = len(script)
    in_single = False
    dollar: str | None = None
    while index < length:
        if dollar is not None:
            if script.startswith(dollar, index):
                buffer.append(dollar)
                index += len(dollar)
                dollar = None
                continue
            buffer.append(script[index])
            index += 1
            continue
        if in_single:
            buffer.append(script[index])
            if script[index] == "'":
                if index + 1 < length and script[index + 1] == "'":
                    buffer.append("'")
                    index += 2
                    continue
                in_single = False
            index += 1
            continue
        if script[index] == "'":
            in_single = True
            buffer.append("'")
            index += 1
            continue
        if script[index] == "$":
            match = _DOLLAR.match(script, index)
            if match:
                dollar = match.group(0)
                buffer.append(dollar)
                index += len(dollar)
                continue
        if script.startswith("--", index):
            newline = script.find("\n", index)
            index = length if newline < 0 else newline + 1
            continue
        if script.startswith("\\gexec", index):
            statement = _clean("".join(buffer))
            if statement:
                statements.append(statement)
            buffer = []
            index += len("\\gexec")
            continue
        if script[index] == ";":
            statement = _clean("".join(buffer))
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue
        buffer.append(script[index])
        index += 1
    statement = _clean("".join(buffer))
    if statement:
        statements.append(statement)
    return statements


def _clean(statement: str) -> str:
    statement = statement.replace("\\gexec", "").strip()
    if not statement or statement.startswith("\\"):
        return ""
    return statement


def execute_script(connection, path: Path) -> None:
    for statement in split_sql(path.read_text(encoding="utf-8")):
        connection.exec_driver_sql(statement)


def ensure_app_role(connection) -> None:
    exists = connection.exec_driver_sql("SELECT 1 FROM pg_roles WHERE rolname = 'billing_app'").first()
    if exists is None:
        connection.exec_driver_sql(
            "CREATE ROLE billing_app LOGIN PASSWORD 'billing_app' "
            "NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE"
        )


def apply_initial_schema(connection) -> None:
    directory = sql_dir()
    organizations = connection.exec_driver_sql("SELECT to_regclass('app.organizations')").scalar()
    if organizations is None:
        execute_script(connection, directory / "ddl.sql")
    ensure_app_role(connection)
    execute_script(connection, directory / "app_extras.sql")
