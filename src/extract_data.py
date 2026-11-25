"""Extract the Northwind tables from the source PDF into CSV files."""

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber
from pypdf import PdfReader

EMPLOYEES_PAGE = 4
TITLES = [
    "Vice President, Sales",
    "Inside Sales Coordinator",
    "Sales Representative",
    "Sales Manager",
]
CITIES = ["Seattle", "Tacoma", "Kirkland", "Redmond", "London"]
KEEP_COLS = {"suppliers": 11}  # phone/fax cells are scrambled past col 11
ROW_KEY = {
    "categories": r"^\d+$",
    "customers": r"^[A-Z]{5}$",
    "order_details": r"^\d{5}$",
    "orders": r"^\d{5}$",
    "shippers": r"^\d$",
    "products": r"^\d+$",
    "suppliers": r"^\d+$",
}


def table_name_from_header(header):
    """Identify which Northwind table a header row belongs to.

    Args:
        header (list[str]): Cell texts of the table's first row.

    Returns:
        str | None: Table name, or None if the header is unrecognized.
    """
    first = header[0]
    if first.startswith("EmployeeID"):
        return "employees"
    if first == "OrderID":
        return "orders" if header[1] == "CustomerID" else "order_details"
    return {
        "CategoryID": "categories",
        "CustomerID": "customers",
        "ShipperID": "shippers",
        "ProductID": "products",
        "SupplierID": "suppliers",
    }.get(first)


def clean_cell(value):
    """Collapse whitespace in a table cell.

    Args:
        value (Any): Raw cell value from pdfplumber, possibly None.

    Returns:
        str | None: Cleaned text, or None if empty or missing.
    """
    if value is None:
        return None
    value = " ".join(str(value).split())
    return value if value else None


def extract_pdf_tables(pdf_path):
    """Collect the rows of each table found in the PDF.

    Rows continue the most recent header's table across pages; the
    employees table is skipped.

    Args:
        pdf_path (str | pathlib.Path): Path of the Northwind PDF.

    Returns:
        tuple[dict[str, list[list]], dict[str, list]]: Rows per table
        name, and the header row per table name.
    """
    tables, headers, current = {}, {}, None
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            for raw in page.extract_tables():
                rows = [[clean_cell(c) for c in row] for row in raw]
                if not rows:
                    continue
                name = table_name_from_header([c or "" for c in rows[0]])
                if name is not None:
                    current = name
                    headers[current] = rows[0]
                    rows = rows[1:]
                if current is None or current == "employees":
                    continue
                tables.setdefault(current, []).extend(rows)
    return tables, headers


def parse_employees(pdf_path):
    """Parse the employees table from the PDF page text.

    Args:
        pdf_path (str | pathlib.Path): Path of the Northwind PDF.

    Returns:
        pandas.DataFrame: One row per employee with name, title,
        dates, location and ``ReportsTo``.
    """
    text = PdfReader(str(pdf_path)).pages[EMPLOYEES_PAGE - 1].extract_text()
    body = text.split("\n", 1)[1]
    starts = [m.start() for m in re.finditer(r"(?m)^[1-9] [A-Z][a-z]+ [A-Z][a-z]+ ", body)]
    starts.append(len(body))
    title_re = "|".join(re.escape(t) for t in TITLES)
    city_re = "|".join(CITIES)
    records = []
    for a, b in zip(starts, starts[1:]):
        block = " ".join(body[a:b].split())
        head = re.match(
            rf"(\d) (\w+) (\w+) ({title_re}) (Ms\.|Mrs\.|Dr\.|Mr\.) "
            r"(\d+/\d+/\d{4}) (\d+/\d+/\d{4}) ",
            block,
        )
        tail = re.search(rf"({city_re}) (?:([A-Z]{{2}}) )?(\S+(?: \S+)?) (USA|UK) ", block)
        reports_to = re.search(r"[.\s](\d)$", block)
        records.append({
            "EmployeeID": int(head.group(1)),
            "LastName": head.group(2),
            "FirstName": head.group(3),
            "Title": head.group(4),
            "TitleOfCourtesy": head.group(5),
            "BirthDate": head.group(6),
            "HireDate": head.group(7),
            "City": tail.group(1),
            "Region": tail.group(2),
            "Country": tail.group(4),
            "ReportsTo": int(reports_to.group(1)) if reports_to else None,
        })
    return pd.DataFrame(records)


def main():
    """Extract all tables from the PDF and write them as CSV files.

    Args:
        None. Reads ``--pdf`` and ``--out`` from the command line.

    Returns:
        None. Writes one CSV per table and prints row counts.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="data/raw/Northwind_Database.pdf")
    parser.add_argument("--out", default="data/extracted")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables, headers = extract_pdf_tables(args.pdf)
    for name, rows in tables.items():
        header = [h if h else f"col{i}" for i, h in enumerate(headers[name])]
        width = KEEP_COLS.get(name, len(header))
        header = header[:width]
        fixed = [(r + [None] * width)[:width] for r in rows]
        df = pd.DataFrame(fixed, columns=header)
        keep = df[header[0]].fillna("").str.match(ROW_KEY[name])
        dropped = int((~keep).sum())
        df = df[keep]
        df.to_csv(out_dir / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} rows x {width} cols (dropped {dropped} junk rows)")

    employees = parse_employees(args.pdf)
    employees.to_csv(out_dir / "employees.csv", index=False)
    print(f"employees: {len(employees)} rows x {employees.shape[1]} cols")


if __name__ == "__main__":
    main()
