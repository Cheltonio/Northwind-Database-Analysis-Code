"""Question 1: how well reorder levels and stock match recent demand."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy.stats import spearmanr

from common import (BLUE, INK, INK_2, LAST_FULL_MONTH, ORANGE, SURFACE,
                    apply_style, build_lines, save_fig, save_table)
from load_data import load_tables

WINDOWS = {
    "6mo": (pd.Period("1997-11", freq="M"), LAST_FULL_MONTH),
    "3mo": (pd.Period("1998-02", freq="M"), LAST_FULL_MONTH),
    "all": (pd.Period("1996-07", freq="M"), LAST_FULL_MONTH),
}
MAIN = "6mo"
DAYS_PER_MONTH = 30.4


def monthly_units(lines):
    """Total units per product and month, to the last full month.

    Args:
        lines (pandas.DataFrame): Order lines from ``build_lines``.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame]: Units by ProductID
        (rows) and month (columns, zero-filled), and the order lines
        up to the last full month.
    """
    months = pd.period_range("1996-07", LAST_FULL_MONTH, freq="M")
    full = lines[lines["Month"] <= LAST_FULL_MONTH]
    units = full.pivot_table(index="ProductID", columns="Month",
                             values="Quantity", aggfunc="sum")
    return units.reindex(columns=months).fillna(0), full


def build_product_table(t, lines):
    """Build the per-product demand, cover and revenue table.

    Args:
        t (dict[str, pandas.DataFrame]): Tables from ``load_tables``.
        lines (pandas.DataFrame): Order lines from ``build_lines``.

    Returns:
        pandas.DataFrame: One row per product, sorted by recent
        revenue, with demand and cover days for each window.
    """
    units, full = monthly_units(lines)
    p = t["products"].set_index("ProductID")
    sup = t["suppliers"].set_index("SupplierID")["CompanyName"]
    cat = t["categories"].set_index("CategoryID")["CategoryName"]
    d = p[["ProductName", "SupplierID", "CategoryID", "UnitsInStock",
           "UnitsOnOrder", "ReorderLevel", "Discontinued"]].copy()
    d["Supplier"] = d["SupplierID"].map(sup)
    d["Category"] = d["CategoryID"].map(cat)
    for name, (start, end) in WINDOWS.items():
        d[f"demand_{name}"] = units.loc[:, start:end].mean(axis=1)
        demand = d[f"demand_{name}"].replace(0, np.nan)
        d[f"cover_days_{name}"] = d["UnitsInStock"] / demand * DAYS_PER_MONTH
    start, end = WINDOWS[MAIN]
    recent = full[(full["Month"] >= start) & (full["Month"] <= end)]
    d["revenue_6mo"] = recent.groupby("ProductID")["CPRev"].sum()
    d["revenue_6mo"] = d["revenue_6mo"].fillna(0.0)
    d["revenue_share"] = d["revenue_6mo"] / d["revenue_6mo"].sum()
    return d.sort_values("revenue_6mo", ascending=False)


def reorder_correlations(d):
    """Compute Spearman correlations of demand with stock fields.

    Args:
        d (pandas.DataFrame): Output of ``build_product_table``.

    Returns:
        pandas.DataFrame: Rho and p-value for each window and each of
        reorder level, units in stock and units on order.
    """
    rows = []
    for name in WINDOWS:
        for target in ["ReorderLevel", "UnitsInStock", "UnitsOnOrder"]:
            rho, pval = spearmanr(d[f"demand_{name}"], d[target])
            rows.append({"window": name, "versus": target,
                         "spearman_rho": rho, "p_value": pval})
    return pd.DataFrame(rows)


def flag_stability(d):
    """Count active products under 30 days of cover in each window.

    Args:
        d (pandas.DataFrame): Output of ``build_product_table``.

    Returns:
        pandas.DataFrame: Flagged-product count per window, plus the
        number flagged in all windows (repeated on every row).
    """
    active = d[~d["Discontinued"]]
    rows, sets = [], {}
    for name in WINDOWS:
        flagged = set(active.index[active[f"cover_days_{name}"] < DAYS_PER_MONTH])
        sets[name] = flagged
        rows.append({"window": name, "active_products_under_30_days_cover": len(flagged)})
    common = set.intersection(*sets.values())
    out = pd.DataFrame(rows)
    out["in_all_windows"] = len(common)
    return out


def supplier_rollup(d):
    """Summarize recent revenue and low-cover exposure by supplier.

    Args:
        d (pandas.DataFrame): Output of ``build_product_table``.

    Returns:
        pandas.DataFrame: One row per supplier, sorted by recent
        revenue.
    """
    g = d.groupby("Supplier").agg(
        products=("ProductName", "count"),
        revenue_6mo=("revenue_6mo", "sum"),
        under_30_days=("cover_days_6mo", lambda s: int((s < DAYS_PER_MONTH).sum())),
    )
    risky = d[d["cover_days_6mo"] < DAYS_PER_MONTH].groupby("Supplier")["revenue_6mo"].sum()
    g["revenue_under_30_days"] = risky.reindex(g.index).fillna(0.0)
    g["revenue_share"] = g["revenue_6mo"] / g["revenue_6mo"].sum()
    g["share_of_supplier_under_30_days"] = g["revenue_under_30_days"] / g["revenue_6mo"].replace(0, np.nan)
    return g.sort_values("revenue_6mo", ascending=False)


def plot_cover(d):
    """Plot days of cover for the 15 highest-revenue products.

    Args:
        d (pandas.DataFrame): Output of ``build_product_table``.

    Returns:
        None. Saves ``q1_cover_top_products.png``.
    """
    top = d.head(15).iloc[::-1]
    n_under = int((d.head(15)["cover_days_6mo"] < DAYS_PER_MONTH).sum())
    fig, ax = plt.subplots(figsize=(9, 6.2))
    colors = [ORANGE if x else BLUE for x in top["Discontinued"]]
    ax.barh(top["ProductName"], top["cover_days_6mo"], color=colors, height=0.62, zorder=2)
    ax.axvline(DAYS_PER_MONTH, color=INK_2, lw=1, ls=(0, (4, 3)), zorder=1)
    ax.annotate("30 days of cover", (DAYS_PER_MONTH + 0.6, 0.985),
                xycoords=("data", "axes fraction"), color=INK_2, fontsize=8.5, va="top")
    label_box = dict(facecolor=SURFACE, edgecolor="none", pad=1.0)
    for y, (_, r) in enumerate(top.iterrows()):
        note = f"stock {r.UnitsInStock:.0f} | reorder level {r.ReorderLevel:.0f}"
        cover = r.cover_days_6mo
        if r.UnitsInStock == 0:
            ax.scatter([0], [y], marker="D", s=40, color=ORANGE if r.Discontinued else BLUE,
                       zorder=3, clip_on=False)
        if cover > 45:
            ax.text(cover - 0.8, y, note, va="center", ha="right", fontsize=8, color="white", zorder=3)
        else:
            ax.text(max(cover, 0) + 1.2, y, note, va="center", fontsize=8, color=INK_2,
                    zorder=3, bbox=label_box)
    ax.set_xlabel("Days of cover at last-6-month demand (units in stock / units sold per day)")
    ax.set_xlim(0, 75)
    ax.set_title(f"{n_under} of the 15 biggest revenue products have under 30 days of stock")
    ax.legend(handles=[Patch(color=BLUE, label="Active"), Patch(color=ORANGE, label="Discontinued")],
              loc="upper right", bbox_to_anchor=(1.0, 0.93))
    ax.grid(axis="y", visible=False)
    save_fig(fig, "q1_cover_top_products")


def plot_reorder(d, rho):
    """Plot reorder level against recent monthly demand.

    Args:
        d (pandas.DataFrame): Output of ``build_product_table``.
        rho (float): Spearman correlation shown in the title.

    Returns:
        None. Saves ``q1_reorder_vs_demand.png``.
    """
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    zero = d["ReorderLevel"] == 0
    ax.scatter(d.loc[~zero, "demand_6mo"], d.loc[~zero, "ReorderLevel"], s=34, color=BLUE,
               edgecolor=INK, linewidth=0.4, alpha=0.85, zorder=3, label="Reorder level above 0")
    ax.scatter(d.loc[zero, "demand_6mo"], d.loc[zero, "ReorderLevel"], s=34, color=ORANGE,
               edgecolor=INK, linewidth=0.4, alpha=0.85, zorder=3,
               label=f"Reorder level = 0 ({int(zero.sum())} products)")
    offsets = {  # name: (dx, dy, horizontal alignment), offsets in points
        "Raclette Courdavault": (-2, -15, "left"),
        "Camembert Pierrot": (2, -15, "right"),
        "Tarte au sucre": (0, -15, "center"),
        "Côte de Blaye": (6, 6, "left"),
        "Gnocchi di nonna Alice": (6, 6, "left"),
        "Rhönbräu Klosterbier": (6, 6, "left"),
    }
    for name, (dx, dy, ha) in offsets.items():
        row = d[d["ProductName"] == name]
        if row.empty:
            continue
        r = row.iloc[0]
        ax.annotate(name, (r["demand_6mo"], r["ReorderLevel"]), xytext=(dx, dy), ha=ha,
                    textcoords="offset points", fontsize=8.5, color=INK_2)
    ax.set_ylim(-4, 32)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.set_xlabel("Average units sold per month, Nov 1997 to Apr 1998")
    ax.set_ylabel("Reorder level (units)")
    ax.set_title(f"Reorder levels do not follow demand (Spearman rho = {rho:.2f})")
    save_fig(fig, "q1_reorder_vs_demand")


def main():
    """Run the Question 1 analysis, then save tables and figures.

    Args:
        None.

    Returns:
        None. Writes ``q1_*`` tables and figures; prints key numbers.
    """
    apply_style()
    t = load_tables()
    lines = build_lines(t)
    d = build_product_table(t, lines)
    corr = reorder_correlations(d)
    stability = flag_stability(d)
    suppliers = supplier_rollup(d)

    cum = d["revenue_share"].cumsum()
    sup_cum = suppliers["revenue_share"].cumsum()
    zero_rl = d[d["ReorderLevel"] == 0]
    rl_rho = corr[(corr.window == MAIN) & (corr.versus == "ReorderLevel")]["spearman_rho"].iloc[0]
    under30 = d["cover_days_6mo"] < DAYS_PER_MONTH
    discontinued = d[d["Discontinued"]]
    key = {
        "products": len(d),
        "products_with_sales_in_6mo": int((d["demand_6mo"] > 0).sum()),
        "median_cover_days_6mo": d["cover_days_6mo"].median(),
        "products_under_30_days_cover": int(under30.sum()),
        "products_over_365_days_cover": int((d["cover_days_6mo"] > 365).sum()),
        "reorder_level_zero_products": len(zero_rl),
        "reorder_level_zero_share_of_revenue": zero_rl["revenue_share"].sum(),
        "reorder_level_spearman_rho_6mo": rl_rho,
        "revenue_share_under_30_days_cover": d.loc[under30, "revenue_share"].sum(),
        "products_for_50pct_revenue": int((cum < 0.5).sum() + 1),
        "products_for_80pct_revenue": int((cum < 0.8).sum() + 1),
        "suppliers_for_50pct_revenue": int((sup_cum < 0.5).sum() + 1),
        "suppliers_for_80pct_revenue": int((sup_cum < 0.8).sum() + 1),
        "discontinued_products": len(discontinued),
        "discontinued_share_of_revenue_6mo": discontinued["revenue_share"].sum(),
        "stock_below_reorder_level_no_order": int(((d["UnitsInStock"] < d["ReorderLevel"])
                                                   & (d["UnitsOnOrder"] == 0)
                                                   & (d["ReorderLevel"] > 0)).sum()),
    }
    save_table(d, "q1_product_table")
    save_table(corr, "q1_reorder_correlations", index=False)
    save_table(stability, "q1_flag_stability", index=False)
    save_table(suppliers, "q1_supplier_rollup")
    save_table(discontinued[["ProductName", "UnitsInStock", "demand_6mo", "revenue_6mo",
                             "revenue_share"]].sort_values("revenue_6mo", ascending=False),
               "q1_discontinued_products")
    save_table(pd.Series(key, name="value").to_frame(), "q1_key_numbers")
    plot_cover(d)
    plot_reorder(d, rl_rho)
    for k, v in key.items():
        print(f"{k}: {v:.4g}" if isinstance(v, float) else f"{k}: {v}")


if __name__ == "__main__":
    main()
