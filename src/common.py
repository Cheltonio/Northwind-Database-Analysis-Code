"""Shared constants, plot style and table helpers."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from load_data import load_tables

ROOT = Path(__file__).resolve().parent.parent
TABLE_DIR = ROOT / "outputs" / "tables"
FIG_DIR = ROOT / "outputs" / "figures"

PRICE_CUTOVER = pd.Timestamp("1997-04-07")
LAST_FULL_MONTH = pd.Period("1998-04", freq="M")
WINDOW_A = (pd.Timestamp("1996-07-01"), pd.Timestamp("1997-04-30"))
WINDOW_B = (pd.Timestamp("1997-07-01"), pd.Timestamp("1998-04-30"))

# Validated categorical slots 1-3 (light surface); see dataviz palette notes.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK_2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
RED = "#e34948"


def apply_style():
    """Set matplotlib rcParams to the project chart style.

    Args:
        None.

    Returns:
        None. Updates ``matplotlib.pyplot.rcParams`` in place.
    """
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "figure.dpi": 150,
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10, "text.color": INK, "axes.labelcolor": INK_2,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.edgecolor": BASELINE, "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.axisbelow": True,
        "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "legend.frameon": False,
    })


def ensure_dirs():
    """Create the output table and figure folders if missing.

    Args:
        None.

    Returns:
        None. Creates ``TABLE_DIR`` and ``FIG_DIR``.
    """
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)


def save_table(df, name, index=True):
    """Write a DataFrame to ``TABLE_DIR`` as a CSV file.

    Args:
        df (pandas.DataFrame): Table to save.
        name (str): File name without the ``.csv`` extension.
        index (bool): Whether to write the index column.

    Returns:
        None. Writes ``TABLE_DIR/<name>.csv``.
    """
    ensure_dirs()
    df.to_csv(TABLE_DIR / f"{name}.csv", index=index)


def save_fig(fig, name):
    """Save a figure as a PNG in ``FIG_DIR`` and close it.

    Args:
        fig (matplotlib.figure.Figure): Figure to save.
        name (str): File name without the ``.png`` extension.

    Returns:
        None. Writes ``FIG_DIR/<name>.png``.
    """
    ensure_dirs()
    fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def build_lines(tables=None):
    """Build one row per order line, joined to order details.

    Adds ``Month`` and ``CPRev``, the constant-price revenue
    (list price x quantity x (1 - discount)), so the April 1997
    price increase does not look like growth.

    Args:
        tables (dict[str, pandas.DataFrame] | None): Tables from
            ``load_tables``; loaded from disk when None.

    Returns:
        pandas.DataFrame: Order lines joined to orders, products
        and customers.
    """
    t = tables if tables is not None else load_tables()
    lines = (
        t["order_details"]
        .merge(t["orders"][["OrderID", "CustomerID", "EmployeeID", "OrderDate", "ShipCountry"]], on="OrderID")
        .merge(t["products"][["ProductID", "ProductName", "SupplierID", "CategoryID", "ListPrice"]], on="ProductID")
        .merge(t["customers"][["CustomerID", "CompanyName", "Country"]], on="CustomerID")
    )
    lines["Month"] = lines["OrderDate"].dt.to_period("M")
    # Constant-price revenue: every line valued at the current list price, so
    # the April 1997 price increase does not look like growth.
    lines["CPRev"] = lines["ListPrice"] * lines["Quantity"] * (1 - lines["Discount"])
    return lines
