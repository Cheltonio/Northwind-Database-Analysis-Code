"""Question 2: sources of revenue growth by market."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

from common import (AQUA, BLUE, INK, INK_2, MUTED, ORANGE, WINDOW_A, WINDOW_B,
                    apply_style, build_lines, save_fig, save_table)
from load_data import load_tables

TOP_N = 8
DRIVERS = ["customers", "orders_per_customer", "order_size"]
DRIVER_LABELS = {"customers": "More active customers",
                 "orders_per_customer": "More orders per customer",
                 "order_size": "Larger orders (revenue per order)"}


def in_window(lines, window):
    """Select order lines whose order date falls inside a window.

    Args:
        lines (pandas.DataFrame): Order lines with ``OrderDate``.
        window (tuple[pandas.Timestamp, pandas.Timestamp]): First and
            last date, inclusive.

    Returns:
        pandas.DataFrame: The matching rows.
    """
    return lines[(lines["OrderDate"] >= window[0]) & (lines["OrderDate"] <= window[1])]


def window_stats(lines, group_col):
    """Compute revenue, orders and customers for each group.

    Args:
        lines (pandas.DataFrame): Order lines with ``CPRev``.
        group_col (str): Column to group by, such as ``Country``.

    Returns:
        pandas.DataFrame: Per group: revenue, orders, customers,
        orders per customer and revenue per order.
    """
    orders = (lines.groupby([group_col, "OrderID", "CustomerID"])["CPRev"]
              .sum().reset_index())
    g = orders.groupby(group_col).agg(revenue=("CPRev", "sum"),
                                      orders=("OrderID", "nunique"),
                                      customers=("CustomerID", "nunique"))
    g["orders_per_customer"] = g["orders"] / g["customers"]
    g["order_size"] = g["revenue"] / g["orders"]
    return g


def decompose(lines, group_col):
    """Split each group's revenue change between windows by driver.

    Revenue = customers x orders per customer x revenue per order, so
    the log change splits exactly into three parts. Weighting each part
    by the logarithmic mean of the two revenues gives dollars that sum
    to the total change.

    Args:
        lines (pandas.DataFrame): Order lines with ``CPRev``.
        group_col (str): Column to group by, such as ``Country``.

    Returns:
        pandas.DataFrame: Window A and B statistics, dollar change by
        driver, growth, shares, and ``gap_vs_company_growth``.
    """
    a = window_stats(in_window(lines, WINDOW_A), group_col)
    b = window_stats(in_window(lines, WINDOW_B), group_col)
    both = a.join(b, lsuffix="_A", rsuffix="_B", how="outer")
    assert not both.isna().any().any(), "a group is missing from one window"
    out = both.copy()
    log_total = np.log(out["revenue_B"] / out["revenue_A"])
    weight = (out["revenue_B"] - out["revenue_A"]) / log_total
    for k in DRIVERS:
        out[f"log_{k}"] = np.log(out[f"{k}_B"] / out[f"{k}_A"])
        out[f"usd_{k}"] = weight * out[f"log_{k}"]
    out["usd_change"] = out["revenue_B"] - out["revenue_A"]
    out["growth"] = out["revenue_B"] / out["revenue_A"] - 1
    out["share_A"] = out["revenue_A"] / out["revenue_A"].sum()
    out["share_B"] = out["revenue_B"] / out["revenue_B"].sum()
    company_growth = out["revenue_B"].sum() / out["revenue_A"].sum() - 1
    out["gap_vs_company_growth"] = out["revenue_B"] - out["revenue_A"] * (1 + company_growth)
    return out


def quarterly(lines):
    """Count orders and customers by quarter, Jul 1996 to Mar 1998.

    Args:
        lines (pandas.DataFrame): Order lines from ``build_lines``.

    Returns:
        pandas.DataFrame: Per quarter: orders, active customers, units,
        new customers and customers who have ever ordered.
    """
    q = lines[(lines["OrderDate"] >= "1996-07-01") & (lines["OrderDate"] <= "1998-03-31")].copy()
    q["Quarter"] = q["OrderDate"].dt.to_period("Q")
    g = q.groupby("Quarter").agg(orders=("OrderID", "nunique"),
                                 active_customers=("CustomerID", "nunique"),
                                 units=("Quantity", "sum"))
    first_quarter = (q.groupby("CustomerID")["OrderDate"].min().dt.to_period("Q")
                     .value_counts().sort_index())
    g["new_customers"] = first_quarter.reindex(g.index).fillna(0).astype(int)
    g["customers_ever_ordered"] = g["new_customers"].cumsum()
    return g


def cohort_check(lines):
    """Compare early customers with later joiners across windows.

    Early customers placed their first order before 1 October 1996.

    Args:
        lines (pandas.DataFrame): Order lines with ``CPRev``.

    Returns:
        pandas.DataFrame: One row each for all customers, early
        customers and later joiners, with growth metrics and share of
        company growth.
    """
    first = lines.groupby("CustomerID")["OrderDate"].min()
    early = lines["CustomerID"].map(first) < "1996-10-01"
    rows = {}
    for name, sub in [("all customers", lines),
                      ("ordering from 1996 Q3", lines[early]),
                      ("joined after 1996 Q3", lines[~early])]:
        stats = {}
        for label, window in [("A", WINDOW_A), ("B", WINDOW_B)]:
            s = in_window(sub, window)
            per_order = s.groupby("OrderID")["CPRev"].sum()
            stats[f"customers_{label}"] = s["CustomerID"].nunique()
            stats[f"orders_{label}"] = len(per_order)
            stats[f"revenue_{label}"] = per_order.sum()
        stats["orders_per_customer_A"] = stats["orders_A"] / stats["customers_A"]
        stats["orders_per_customer_B"] = stats["orders_B"] / stats["customers_B"]
        stats["orders_per_customer_growth"] = stats["orders_per_customer_B"] / stats["orders_per_customer_A"] - 1
        stats["revenue_per_order_A"] = stats["revenue_A"] / stats["orders_A"]
        stats["revenue_per_order_B"] = stats["revenue_B"] / stats["orders_B"]
        stats["revenue_per_order_growth"] = stats["revenue_per_order_B"] / stats["revenue_per_order_A"] - 1
        stats["revenue_growth"] = stats["revenue_B"] / stats["revenue_A"] - 1
        stats["usd_change"] = stats["revenue_B"] - stats["revenue_A"]
        rows[name] = stats
    out = pd.DataFrame(rows).T
    out["share_of_company_growth"] = out["usd_change"] / out.loc["all customers", "usd_change"]
    return out


def customer_concentration(lines, customers):
    """Rank customers by revenue with each customer's share.

    Args:
        lines (pandas.DataFrame): Order lines with ``CPRev``.
        customers (pandas.DataFrame): Customers with ``CustomerID``,
            ``CompanyName`` and ``Country``.

    Returns:
        pandas.DataFrame: Customers sorted by revenue with share and
        cumulative share.
    """
    rev = lines.groupby("CustomerID")["CPRev"].sum().sort_values(ascending=False)
    table = rev.to_frame("revenue").join(customers.set_index("CustomerID")[["CompanyName", "Country"]])
    table["share"] = table["revenue"] / table["revenue"].sum()
    table["cumulative_share"] = table["share"].cumsum()
    return table


def shipcountry_sensitivity(lines):
    """Compare customer-country and ship-country market attribution.

    Args:
        lines (pandas.DataFrame): Order lines with ``Country`` and
            ``ShipCountry``.

    Returns:
        pandas.DataFrame: Per country: revenue under each attribution
        for both windows, absolute differences and growth gaps.
    """
    alt = lines.copy()
    alt["Country"] = alt["ShipCountry"]
    base = decompose(lines, "Country")
    other = decompose(alt, "Country")
    idx = base.index.union(other.index)
    diff = pd.DataFrame(index=idx)
    for label in ["A", "B"]:
        diff[f"revenue_{label}_customer_country"] = base[f"revenue_{label}"].reindex(idx).fillna(0)
        diff[f"revenue_{label}_ship_country"] = other[f"revenue_{label}"].reindex(idx).fillna(0)
    diff["abs_diff_A"] = (diff["revenue_A_customer_country"] - diff["revenue_A_ship_country"]).abs()
    diff["abs_diff_B"] = (diff["revenue_B_customer_country"] - diff["revenue_B_ship_country"]).abs()
    diff["gap_customer_country"] = base["gap_vs_company_growth"].reindex(idx)
    diff["gap_ship_country"] = other["gap_vs_company_growth"].reindex(idx)
    return diff


def plot_drivers(grouped):
    """Plot revenue change by market, split by growth driver.

    Args:
        grouped (pandas.DataFrame): Output of ``decompose`` by market
            group.

    Returns:
        None. Saves ``q2_growth_drivers_by_market.png``.
    """
    other = [name for name in grouped.index if name.startswith("Other")]
    order = pd.concat([grouped.loc[other],
                       grouped.drop(index=other).sort_values("usd_change")])
    labels = list(order.index)
    fig, ax = plt.subplots(figsize=(9, 5.6))
    pos_left = np.zeros(len(order))
    neg_left = np.zeros(len(order))
    colors = {"customers": BLUE, "orders_per_customer": ORANGE, "order_size": AQUA}
    y = np.arange(len(order))
    for k in DRIVERS:
        vals = order[f"usd_{k}"].values / 1000
        left = np.where(vals >= 0, pos_left, neg_left)
        ax.barh(y, vals, left=left, color=colors[k], height=0.62, edgecolor=ax.get_facecolor(), linewidth=1.2)
        pos_left += np.where(vals >= 0, vals, 0)
        neg_left += np.where(vals < 0, vals, 0)
    ax.scatter(order["usd_change"] / 1000, y, marker="D", s=46, color=INK, zorder=4)
    for yi, v in zip(y, order["usd_change"] / 1000):
        ax.annotate(f"{v:+.0f}K", (v, yi), xytext=(8 if v >= 0 else -8, 0), textcoords="offset points",
                    va="center", ha="left" if v >= 0 else "right", fontsize=8.5, color=INK_2)
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Change in constant-price revenue, Jul 1996-Apr 1997 to Jul 1997-Apr 1998 (thousand USD)")
    ax.set_title("Growth came mostly from more orders per customer, not larger orders")
    handles = [Patch(color=colors[k], label=DRIVER_LABELS[k]) for k in DRIVERS]
    handles.append(plt.Line2D([0], [0], marker="D", color="none", markerfacecolor=INK,
                              markeredgecolor=INK, label="Net change", markersize=6))
    ax.legend(handles=handles, loc="center right", bbox_to_anchor=(1.0, 0.45))
    ax.grid(axis="y", visible=False)
    save_fig(fig, "q2_growth_drivers_by_market")


def plot_gap(full, cust_counts):
    """Plot each country's revenue gap versus company growth.

    Args:
        full (pandas.DataFrame): Output of ``decompose`` by country.
        cust_counts (pandas.Series): Customers on file per country.

    Returns:
        None. Saves ``q2_gap_vs_company_growth.png``.
    """
    d = full.sort_values("gap_vs_company_growth")
    fig, ax = plt.subplots(figsize=(8.8, 6.8))
    colors = [BLUE if v >= 0 else ORANGE for v in d["gap_vs_company_growth"]]
    tick_labels = [f"{name} ({cust_counts[name]})" for name in d.index]
    ax.barh(tick_labels, d["gap_vs_company_growth"] / 1000, color=colors, height=0.66)
    ax.axvline(0, color=INK_2, lw=0.8)
    for yi, (name, r) in enumerate(d.iterrows()):
        v = r["gap_vs_company_growth"] / 1000
        ax.annotate(f"{v:+.1f}K ({r['growth']:+.0%})", (v, yi), xytext=(6 if v >= 0 else -6, 0),
                    textcoords="offset points", va="center",
                    ha="left" if v >= 0 else "right", fontsize=8, color=INK_2)
    ax.set_xlim(d["gap_vs_company_growth"].min() / 1000 * 1.5, d["gap_vs_company_growth"].max() / 1000 * 1.45)
    ax.set_xlabel("Revenue gap vs. growing at the company-wide rate (thousand USD, constant prices)\n"
                  "Number in brackets = customers on file in that country")
    ax.set_title("France is the biggest shortfall; Germany and the USA pull ahead")
    ax.legend(handles=[Patch(color=BLUE, label="Ahead of company growth"),
                       Patch(color=ORANGE, label="Behind company growth")], loc="lower right")
    ax.grid(axis="y", visible=False)
    save_fig(fig, "q2_gap_vs_company_growth")


def plot_quarterly(q):
    """Plot quarterly orders against customers who have ordered.

    Args:
        q (pandas.DataFrame): Output of ``quarterly``.

    Returns:
        None. Saves ``q2_orders_vs_customer_base.png``.
    """
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    x = [str(p) for p in q.index]
    ax.plot(x, q["orders"], color=ORANGE, lw=2, marker="o", ms=6, label="Orders placed in the quarter")
    ax.plot(x, q["customers_ever_ordered"], color=BLUE, lw=2, marker="o", ms=6,
            label="Customers who have ordered at least once (cumulative)")
    for series, color in [("orders", ORANGE), ("customers_ever_ordered", BLUE)]:
        ax.annotate(f"{q[series].iloc[-1]:.0f}", (x[-1], q[series].iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", color=color, fontsize=10)
    ax.set_ylabel("Count")
    ax.set_title("The customer base filled in by mid-1997; orders kept climbing")
    ax.legend(loc="upper left")
    ax.set_ylim(0, None)
    save_fig(fig, "q2_orders_vs_customer_base")


def main():
    """Run the Question 2 analysis, then save tables and figures.

    Args:
        None.

    Returns:
        None. Writes ``q2_*`` tables and figures; prints key numbers.
    """
    apply_style()
    t = load_tables()
    lines = build_lines(t)
    full = decompose(lines, "Country")
    top = list(full.sort_values("revenue_B", ascending=False).head(TOP_N).index)
    other_label = f"Other ({len(full) - TOP_N} countries)"
    lines["Group"] = lines["Country"].where(lines["Country"].isin(top), other_label)
    grouped = decompose(lines, "Group")
    company = decompose(lines.assign(All="Company"), "All").iloc[0]
    quarters = quarterly(lines)
    conc = customer_concentration(lines, t["customers"])
    sens = shipcountry_sensitivity(lines)
    cohorts = cohort_check(lines)
    early = cohorts.loc["ordering from 1996 Q3"]
    later = cohorts.loc["joined after 1996 Q3"]
    gap_flips = int((np.sign(sens["gap_customer_country"]) != np.sign(sens["gap_ship_country"])).sum())

    nominal = lines.assign(Rev=lines["LineRevenue"])
    nom_a = in_window(nominal, WINDOW_A)["Rev"].sum()
    nom_b = in_window(nominal, WINDOW_B)["Rev"].sum()
    units_a = in_window(lines, WINDOW_A)["Quantity"].sum()
    units_b = in_window(lines, WINDOW_B)["Quantity"].sum()
    cust_counts = t["customers"].groupby("Country").size()
    austria_b = in_window(lines[lines["Country"] == "Austria"], WINDOW_B)
    ernsh_share = austria_b[austria_b["CustomerID"] == "ERNSH"]["CPRev"].sum() / austria_b["CPRev"].sum()

    key = {
        "revenue_A_constant_price": company["revenue_A"],
        "revenue_B_constant_price": company["revenue_B"],
        "growth_constant_price": company["growth"],
        "growth_nominal": nom_b / nom_a - 1,
        "growth_units": units_b / units_a - 1,
        "orders_A": company["orders_A"], "orders_B": company["orders_B"],
        "orders_growth": company["orders_B"] / company["orders_A"] - 1,
        "active_customers_A": company["customers_A"], "active_customers_B": company["customers_B"],
        "active_customers_growth": company["customers_B"] / company["customers_A"] - 1,
        "orders_per_customer_A": company["orders_per_customer_A"],
        "orders_per_customer_B": company["orders_per_customer_B"],
        "revenue_per_order_A": company["order_size_A"], "revenue_per_order_B": company["order_size_B"],
        "usd_from_customers": company["usd_customers"],
        "usd_from_orders_per_customer": company["usd_orders_per_customer"],
        "usd_from_order_size": company["usd_order_size"],
        "countries": len(full),
        "countries_with_5plus_customers": int((cust_counts >= 5).sum()),
        "countries_declining": int((full["growth"] < 0).sum()),
        "top1_customer_share": conc["share"].iloc[0],
        "top5_customer_share": conc["share"].iloc[:5].sum(),
        "top10_customer_share": conc["share"].iloc[:10].sum(),
        "ernsh_share_of_austria_B": ernsh_share,
        "customers_ordered_by_end_1997Q2": int(quarters.loc[pd.Period("1997Q2"), "customers_ever_ordered"]),
        "customers_ever_ordered": int(quarters["customers_ever_ordered"].iloc[-1]),
        "like_for_like_customers": int(early["customers_A"]),
        "like_for_like_orders_per_customer_growth": early["orders_per_customer_growth"],
        "like_for_like_revenue_per_order_growth": early["revenue_per_order_growth"],
        "like_for_like_revenue_growth": early["revenue_growth"],
        "like_for_like_share_of_company_growth": early["share_of_company_growth"],
        "later_joiners_share_of_company_growth": later["share_of_company_growth"],
        "shipcountry_max_abs_diff_either_window": max(sens["abs_diff_A"].max(), sens["abs_diff_B"].max()),
        "shipcountry_total_reassigned_both_windows": (sens["abs_diff_A"].sum() + sens["abs_diff_B"].sum()) / 2,
        "shipcountry_gap_sign_flips": gap_flips,
    }
    save_table(full, "q2_country_decomposition")
    save_table(grouped, "q2_group_decomposition")
    save_table(quarters, "q2_quarterly")
    save_table(cohorts, "q2_cohort_check")
    save_table(conc.head(15), "q2_top_customers")
    save_table(sens, "q2_shipcountry_sensitivity")
    save_table(pd.Series(key, name="value").to_frame(), "q2_key_numbers")
    plot_drivers(grouped)
    plot_gap(full, cust_counts)
    plot_quarterly(quarters)
    for k, v in key.items():
        print(f"{k}: {v:.4g}" if isinstance(v, (float, np.floating)) else f"{k}: {v}")


if __name__ == "__main__":
    main()
