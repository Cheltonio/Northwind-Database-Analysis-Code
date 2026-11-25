"""Load the extracted Northwind CSV files and convert column types."""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "extracted"

PRODUCT_COLUMNS = [
    "ProductID", "ProductName", "SupplierID", "CategoryID", "QuantityPerUnit",
    "ListPrice", "CheapFlag", "NewPrice1", "CheapBit", "UnitsInStock",
    "UnitsOnOrder", "ReorderLevel", "Discontinued", "IsCheap", "Blank", "NewPrice2",
    "Extra",
]


def to_number(series):
    """Convert text to numbers, removing thousands separators.

    Args:
        series (pandas.Series): Values such as ``"1,234.50"``.

    Returns:
        pandas.Series: Float values; unparseable entries are NaN.
    """
    return pd.to_numeric(series.astype(str).str.replace(",", "", regex=False), errors="coerce")


def load_tables(data_dir=DATA_DIR):
    """Read every extracted CSV and type the columns used downstream.

    Args:
        data_dir (pathlib.Path): Folder holding the extracted CSVs.

    Returns:
        dict[str, pandas.DataFrame]: Tables keyed by file name stem
        (``orders``, ``order_details``, ``products``, ...).
        ``order_details`` gains ``LineRevenue`` and ``LineFullPrice``.
    """
    t = {p.stem: pd.read_csv(p, dtype=str) for p in Path(data_dir).glob("*.csv")}

    od = t["order_details"]
    for col in ["OrderID", "ProductID", "Quantity"]:
        od[col] = od[col].astype(int)
    od["UnitPrice"] = to_number(od["UnitPrice"])
    od["Discount"] = to_number(od["Discount"]).round(2)
    od["LineRevenue"] = od["UnitPrice"] * od["Quantity"] * (1 - od["Discount"])
    od["LineFullPrice"] = od["UnitPrice"] * od["Quantity"]

    o = t["orders"]
    o["OrderID"] = o["OrderID"].astype(int)
    o["EmployeeID"] = o["EmployeeID"].astype(int)
    o["ShipVia"] = o["ShipVia"].astype(int)
    for col in ["OrderDate", "RequiredDate", "ShippedDate"]:
        o[col] = pd.to_datetime(o[col], format="%m/%d/%Y", errors="coerce")
    o["Freight"] = to_number(o["Freight"])

    p = t["products"]
    p.columns = PRODUCT_COLUMNS[: p.shape[1]]
    for col in ["ProductID", "SupplierID", "CategoryID", "UnitsInStock", "UnitsOnOrder", "ReorderLevel"]:
        p[col] = p[col].astype(int)
    p["ListPrice"] = to_number(p["ListPrice"])
    p["Discontinued"] = p["Discontinued"].str.upper().eq("TRUE")

    e = t["employees"]
    e["EmployeeID"] = e["EmployeeID"].astype(int)
    e["HireDate"] = pd.to_datetime(e["HireDate"], format="%m/%d/%Y")

    t["customers"] = t["customers"]
    t["suppliers"]["SupplierID"] = t["suppliers"]["SupplierID"].astype(int)
    t["categories"]["CategoryID"] = t["categories"]["CategoryID"].astype(int)
    t["shippers"]["ShipperID"] = t["shippers"]["ShipperID"].astype(int)
    return t
