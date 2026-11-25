"""Question 2: where revenue growth came from."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import (BLUE, INK_2, ORANGE, WINDOW_A, WINDOW_B,
                    apply_style, build_lines, save_fig, save_table)
from load_data import load_tables

DRIVERS = {"customers": "Customers who ordered",
           "orders_per_customer": "Orders per customer",
           "order_size": "Revenue per order"}


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


def driver_summary(lines):
    """Compare the two windows on revenue and its three building blocks.

    Revenue = customers x orders per customer x revenue per order, so
    the three percent changes multiply to the revenue change.

    Args:
        lines (pandas.DataFrame): Order lines with ``CPRev``.

    Returns:
        pandas.DataFrame: One row per measure with its value in each
        window and the percent change between them.
    """
    stats = {}
    for label, window in [("A", WINDOW_A), ("B", WINDOW_B)]:
        s = in_window(lines, window)
        per_order = s.groupby("OrderID")["CPRev"].sum()
        stats[label] = {"revenue": per_order.sum(), "orders": len(per_order),
                        "customers": s["CustomerID"].nunique()}
        stats[label]["orders_per_customer"] = stats[label]["orders"] / stats[label]["customers"]
        stats[label]["order_size"] = stats[label]["revenue"] / stats[label]["orders"]
    out = pd.DataFrame(stats)
    out["change_pct"] = (out["B"] / out["A"] - 1) * 100
    return out.rename(columns={"A": "window_A", "B": "window_B"})


def plot_drivers(summary):
    """Plot the percent change in revenue and its three building blocks.

    Args:
        summary (pandas.DataFrame): Output of ``driver_summary``.

    Returns:
        None. Saves ``q2_growth_drivers.png``.
    """
    names = ["Total revenue"] + list(DRIVERS.values())
    keys = ["revenue"] + list(DRIVERS)
    vals = [summary.loc[k, "change_pct"] for k in keys]
    colors = [INK_2] + [ORANGE if k == "orders_per_customer" else BLUE for k in DRIVERS]
    fig, ax = plt.subplots(figsize=(8, 3.9))
    y = np.arange(len(names))[::-1]
    ax.barh(y, vals, color=colors, height=0.55)
    for yi, v in zip(y, vals):
        ax.annotate(f"{v:+.0f}%".replace("-", "\u2212"), (v, yi), xytext=(6 if v >= 0 else -6, 0),
                    textcoords="offset points", va="center", ha="left" if v >= 0 else "right",
                    fontsize=11, color=INK_2)
    ax.axvline(0, color=INK_2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlim(-25, 80)
    ax.set_xlabel("Change from Jul 1996-Apr 1997 to Jul 1997-Apr 1998")
    ax.set_title("Revenue grew mostly because customers ordered more often")
    ax.grid(axis="y", visible=False)
    save_fig(fig, "q2_growth_drivers")


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
    summary = driver_summary(lines)
    quarters = quarterly(lines)
    conc = customer_concentration(lines, t["customers"])
    cohorts = cohort_check(lines)
    early = cohorts.loc["ordering from 1996 Q3"]
    later = cohorts.loc["joined after 1996 Q3"]
    nom_a = in_window(lines.assign(Rev=lines["LineRevenue"]), WINDOW_A)["Rev"].sum()
    nom_b = in_window(lines.assign(Rev=lines["LineRevenue"]), WINDOW_B)["Rev"].sum()

    key = {
        "revenue_A_constant_price": summary.loc["revenue", "window_A"],
        "revenue_B_constant_price": summary.loc["revenue", "window_B"],
        "growth_constant_price": summary.loc["revenue", "change_pct"] / 100,
        "growth_nominal": nom_b / nom_a - 1,
        "customers_A": summary.loc["customers", "window_A"],
        "customers_B": summary.loc["customers", "window_B"],
        "customers_change": summary.loc["customers", "change_pct"] / 100,
        "orders_A": summary.loc["orders", "window_A"], "orders_B": summary.loc["orders", "window_B"],
        "orders_per_customer_A": summary.loc["orders_per_customer", "window_A"],
        "orders_per_customer_B": summary.loc["orders_per_customer", "window_B"],
        "orders_per_customer_change": summary.loc["orders_per_customer", "change_pct"] / 100,
        "revenue_per_order_A": summary.loc["order_size", "window_A"],
        "revenue_per_order_B": summary.loc["order_size", "window_B"],
        "revenue_per_order_change": summary.loc["order_size", "change_pct"] / 100,
        "top1_customer_share": conc["share"].iloc[0],
        "top10_customer_share": conc["share"].iloc[:10].sum(),
        "customers_ordered_by_end_1997Q2": int(quarters.loc[pd.Period("1997Q2"), "customers_ever_ordered"]),
        "customers_ever_ordered": int(quarters["customers_ever_ordered"].iloc[-1]),
        "like_for_like_customers": int(early["customers_A"]),
        "like_for_like_orders_per_customer_growth": early["orders_per_customer_growth"],
        "like_for_like_revenue_per_order_growth": early["revenue_per_order_growth"],
        "like_for_like_revenue_growth": early["revenue_growth"],
        "like_for_like_share_of_company_growth": early["share_of_company_growth"],
        "later_joiners_share_of_company_growth": later["share_of_company_growth"],
    }
    save_table(summary, "q2_driver_summary")
    save_table(quarters, "q2_quarterly")
    save_table(cohorts, "q2_cohort_check")
    save_table(conc.head(15), "q2_top_customers")
    save_table(pd.Series(key, name="value").to_frame(), "q2_key_numbers")
    plot_drivers(summary)
    plot_quarterly(quarters)
    for k, v in key.items():
        print(f"{k}: {v:.4g}" if isinstance(v, (float, np.floating)) else f"{k}: {v}")


if __name__ == "__main__":
    main()
