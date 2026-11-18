from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fpdf import FPDF

NAVY = (16, 42, 67)
INK = (15, 23, 42)
MUTED = (100, 116, 139)
LINE = (226, 232, 240)
TEAL = (15, 118, 110)
TEAL_BG = (231, 246, 244)
CANVAS = (248, 250, 252)
DECLARATION = "We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct."
TERMS = "Please make payment by the due date mentioned above."
ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def build_pdf(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 11 Tf", "48 800 Td", "14 TL"]
    for index, line in enumerate(lines[:45]):
        safe = line.encode("latin-1", "replace").decode("latin-1")
        safe = safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            commands.append("T*")
        commands.append(f"({safe}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return bytes(output)


def _text(value) -> str:
    return str(value or "").encode("latin-1", "replace").decode("latin-1")


def _money(value) -> str:
    try:
        number = Decimal(str(value if value not in (None, "") else "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        number = Decimal("0.00")
    sign = "-" if number < 0 else ""
    whole, fraction = f"{abs(number):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while head:
            groups.append(head[-2:])
            head = head[:-2]
        whole = ",".join(reversed(groups)) + "," + tail
    return f"{sign}{whole}.{fraction}"


def _below_thousand(value: int) -> str:
    hundred, rest = divmod(value, 100)
    parts = []
    if hundred:
        parts.append(f"{ONES[hundred]} hundred")
    if rest:
        parts.append(ONES[rest] if rest < 20 else f"{TENS[rest // 10]} {ONES[rest % 10]}".strip())
    return " ".join(parts)


def _words(value) -> str:
    try:
        number = Decimal(str(value or "0")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        number = Decimal("0.00")
    rupees, coins = divmod(int(abs(number) * 100), 100)
    if rupees == 0 and coins == 0:
        return "Rupees Zero Only."
    remaining = rupees
    parts = []
    for scale, name in ((10000000, "crore"), (100000, "lakh"), (1000, "thousand")):
        count, remaining = divmod(remaining, scale)
        if count:
            parts.append(f"{_below_thousand(count)} {name}")
    if remaining:
        parts.append(_below_thousand(remaining))
    titled = " ".join(parts).strip() or "zero"
    titled = " ".join(word if word == "and" else word.capitalize() for word in titled.split())
    coins_text = f" and {_below_thousand(coins).title()} Paise" if coins else ""
    return f"Rupees {titled}{coins_text} Only."


def _rate(value) -> str:
    try:
        number = Decimal(str(value or 0)).normalize()
    except (InvalidOperation, ValueError):
        return "0"
    text = format(number, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _when(value) -> str:
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%d-%b-%Y")
    text = str(value or "")[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%d-%b-%Y")
    except ValueError:
        return text or "—"


def _party(party: dict | None, fallback: str) -> list[str]:
    party = party or {}
    place = ", ".join(part for part in (party.get("city"), party.get("district"), party.get("state")) if part)
    locality = " - ".join(part for part in (place, party.get("postal_code")) if part)
    lines = [
        party.get("name") or fallback,
        party.get("line1"),
        party.get("line2"),
        locality,
        f"GSTIN: {party['gstin']}" if party.get("gstin") else "",
        f"Phone: {party['phone']}" if party.get("phone") else "",
        f"Email: {party['email']}" if party.get("email") else "",
    ]
    return [_text(line) for line in lines if line and str(line).strip()]


def build_invoice_pdf(invoice, customer, items) -> bytes:
    snapshot = invoice.billing_snapshot or {}
    seller = snapshot.get("from") or {}
    buyer = snapshot.get("bill_to") or {}
    ship = snapshot.get("to") or buyer
    show_discount = snapshot.get("show_discount") is not False
    saved_lines = snapshot.get("lines") or []
    business = _text(seller.get("name") or snapshot.get("merchant_name") or "Business").upper()
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(12, 6)
    pdf.cell(110, 8, business, align="L")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(120, 6)
    pdf.cell(78, 8, "TAX INVOICE", align="R")
    pdf.set_font("Helvetica", "", 8)
    header = []
    if seller.get("line1"):
        header.append(seller.get("line1"))
    locality = ", ".join(part for part in (seller.get("city"), seller.get("state"), seller.get("postal_code")) if part)
    if locality:
        header.append(locality)
    contact = " | ".join(part for part in (f"GSTIN: {seller['gstin']}" if seller.get("gstin") else "", f"Phone: {seller['phone']}" if seller.get("phone") else "") if part)
    if contact:
        header.append(contact)
    if seller.get("email"):
        header.append(f"Email: {seller['email']}")
    pdf.set_xy(12, 14)
    pdf.multi_cell(110, 3.4, _text("\n".join(header[:3])))
    pdf.set_xy(120, 15)
    pdf.multi_cell(78, 4, _text(f"Invoice No: {invoice.invoice_no}\nInvoice Date: {_when(invoice.invoice_date)}\nDue Date: {_when(invoice.due_date)}"), align="R")

    y = 32
    blocks = [
        ("FROM / SELLER", _party(seller, business)),
        ("BUYER / BILL TO", _party(buyer, customer.display_name if customer else "Buyer")),
        ("DELIVERY / SHIP TO", _party(ship, buyer.get("name") or "Ship to") + [
            _text(f"Place of Supply: {snapshot.get('place_of_supply') or buyer.get('state') or '—'}"),
            _text(f"Supply Type: {'Inter-state' if snapshot.get('treatment') == 'inter' else 'Exempt' if snapshot.get('treatment') == 'exempt' else 'Intra-state'}"),
        ]),
    ]
    box_w = 62
    pdf.set_draw_color(*LINE)
    pdf.set_fill_color(*CANVAS)
    pdf.rect(12, y, 186, 34, "FD")
    for index, (title, lines) in enumerate(blocks):
        x = 12 + index * box_w
        if index:
            pdf.line(x, y, x, y + 34)
        pdf.set_xy(x + 2, y + 2)
        pdf.set_text_color(*NAVY)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(box_w - 4, 4, title)
        pdf.set_text_color(*INK)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(x + 2, y + 7)
        pdf.multi_cell(box_w - 4, 3.3, "\n".join(lines[:7]))
    y = 70
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(12, y)
    pdf.cell(40, 5, "ITEM DETAILS")
    y += 6
    columns = [12, 58, 22, 16, 24, 22, 32] if show_discount else [12, 78, 24, 18, 26, 28]
    headers = ["S.No", "Description", "HSN/SAC", "Qty", "Rate", "Discount", "Taxable"] if show_discount else ["S.No", "Description", "HSN/SAC", "Qty", "Rate", "Taxable"]
    aligns = ["L", "L", "L", "R", "R", "R", "R"] if show_discount else ["L", "L", "L", "R", "R", "R"]

    def paint_header(top: float) -> float:
        pdf.set_fill_color(*NAVY)
        pdf.rect(12, top, 186, 7, "F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 7.5)
        x = 12
        for header_text, width in zip(headers, columns):
            pdf.set_xy(x, top + 1.5)
            pdf.cell(width, 4, header_text)
            x += width
        return top + 7

    y = paint_header(y)
    rows = saved_lines or [
        {
            "description": item.description,
            "hsn": "—",
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "discount": item.discount_amount,
            "taxable": item.line_total,
            "cgst": "0",
            "sgst": "0",
            "igst": item.tax_amount,
            "gst_rate": "0",
        }
        for item in items
    ]
    discount_total = Decimal("0")
    taxable_total = Decimal("0")
    tax_rows: list[tuple[str, Decimal]] = []
    pdf.set_font("Helvetica", "", 8)
    for index, line in enumerate(rows, start=1):
        if y > 250:
            pdf.add_page()
            y = paint_header(16)
        if index % 2 == 0:
            pdf.set_fill_color(*CANVAS)
            pdf.rect(12, y, 186, 6.5, "F")
        discount = Decimal(str(line.get("discount") or 0))
        taxable = Decimal(str(line.get("taxable") or line.get("total") or 0))
        discount_total += discount
        taxable_total += taxable
        rate = _rate(line.get("gst_rate"))
        half = _rate(Decimal(rate) / 2)
        for label, key in ((f"CGST @ {half}%", "cgst"), (f"SGST @ {half}%", "sgst"), (f"IGST @ {rate}%", "igst")):
            amount = Decimal(str(line.get(key) or 0))
            if amount:
                tax_rows.append((label, amount))
        cells = [str(index), _text(line.get("description") or "Item"), _text(line.get("hsn") or "—"), _text(line.get("quantity")), _money(line.get("unit_price"))]
        if show_discount:
            cells.append(_money(discount))
        cells.append(_money(taxable))
        pdf.set_text_color(*INK)
        x = 12
        for cell, width, align in zip(cells, columns, aligns):
            pdf.set_xy(x + 1, y + 1.2)
            pdf.cell(width - 2, 4, cell[:42], align=align)
            x += width
        y += 6.5
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(12, y, 186, 6.5, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(14, y + 1.2)
    pdf.cell(140, 4, "Subtotal")
    pdf.set_xy(150, y + 1.2)
    pdf.cell(46, 4, _money(taxable_total), align="R")
    y += 12
    grouped: dict[str, Decimal] = {}
    for label, amount in tax_rows:
        grouped[label] = grouped.get(label, Decimal("0")) + amount
    breakup = [f"Taxable Amount: Rs. {_money(taxable_total)}"]
    if show_discount:
        breakup.append(f"Discount: Rs. {_money(discount_total)}")
    breakup.extend(f"{label}: Rs. {_money(amount)}" for label, amount in grouped.items())
    breakup.append(f"Total GST: Rs. {_money(invoice.tax_total)}")
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(12, y)
    pdf.cell(40, 5, "TAX BREAKUP")
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(12, y + 6)
    pdf.multi_cell(90, 4, "\n".join(breakup))
    totals = [("Subtotal", invoice.subtotal)]
    if show_discount:
        totals.extend([("Discount", discount_total or invoice.discount_total), ("Taxable value", taxable_total or invoice.subtotal)])
    totals.extend((label.split(" @ ")[0], amount) for label, amount in grouped.items())
    if Decimal(str(invoice.shipping_amount or 0)):
        totals.append(("Additional charges", invoice.shipping_amount))
    totals.append(("Grand Total", invoice.grand_total))
    totals_y = y
    for label, amount in totals:
        emphasize = label == "Grand Total"
        if emphasize:
            pdf.set_fill_color(*TEAL_BG)
            pdf.rect(118, totals_y, 80, 8, "F")
            pdf.set_text_color(*TEAL)
            pdf.set_font("Helvetica", "B", 11)
        else:
            pdf.set_text_color(*INK)
            pdf.set_font("Helvetica", "", 9)
        pdf.set_xy(120, totals_y + (1.5 if emphasize else 0))
        pdf.cell(40, 5, label)
        pdf.set_xy(150, totals_y + (1.5 if emphasize else 0))
        pdf.cell(46, 5, f"Rs. {_money(amount)}", align="R")
        totals_y += 9 if emphasize else 6
    y = max(y + 8 + len(breakup) * 4, totals_y) + 4
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(12, y)
    pdf.cell(36, 5, "Amount in Words:")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(48, y)
    pdf.multi_cell(150, 5, _text(_words(invoice.grand_total)))
    y = pdf.get_y() + 2
    terms = _text((invoice.notes or "").strip() or TERMS)
    pdf.set_fill_color(*CANVAS)
    pdf.set_draw_color(*LINE)
    pdf.rect(12, y, 186, 28, "FD")
    pdf.set_xy(15, y + 2)
    pdf.set_text_color(*NAVY)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(40, 4, "DECLARATION")
    pdf.set_text_color(*INK)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(15, y + 7)
    pdf.multi_cell(180, 4, _text(DECLARATION))
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(16, 4, "Terms:")
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(164, 4, terms)
    y = max(pdf.get_y() + 8, y + 36)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(12, y)
    pdf.cell(80, 5, "Customer Signature")
    pdf.set_xy(120, y)
    pdf.cell(70, 5, f"For {business}")
    pdf.set_draw_color(51, 65, 85)
    pdf.line(12, y + 16, 70, y + 16)
    pdf.line(120, y + 16, 178, y + 16)
    pdf.set_text_color(*MUTED)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(12, y + 17)
    pdf.cell(60, 4, "Received By")
    pdf.set_xy(120, y + 17)
    pdf.cell(60, 4, "Authorized Signatory")
    pdf.set_text_color(*INK)
    pdf.set_xy(12, y + 24)
    pdf.cell(80, 5, "Thank you for your business!")
    return bytes(pdf.output())
