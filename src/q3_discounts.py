"""Question 3: do discounts bring in enough extra sales to pay off?"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import BLUE, INK_2, ORANGE, apply_style, build_lines, save_fig, save_table
from load_data import load_tables

MIN_LINES = 3  # lines needed on each side (discounted, full price) to compare a group
N_BOOT = 300
SEED = 0
SIZE_LABELS = ["Smallest", "Small", "Large", "Largest"]


def lift_overall(d):
    """Compare average units on discounted and full-price lines.

    Args:
        d (pandas.DataFrame): Order lines with ``Quantity`` and the
            boolean column ``discounted``.

    Returns:
        float: Extra units on discounted lines, as a fraction
        (0.26 = 26% more).
    """
    means = d.groupby("discounted")["Quantity"].mean()
    return means[True] / means[False] - 1


def lift_within(d, key):
    """Compare discounted and full-price lines within each group.

    Groups (for example one product) need at least ``MIN_LINES`` lines
    of each kind. Each group's ratio is weighted by its number of
    discounted lines.

    Args:
        d (pandas.DataFrame): Order lines with ``Quantity`` and
            ``discounted``.
        key (str): Column defining the groups, e.g. ``ProductID``.

    Returns:
        tuple[float, int]: Average extra units as a fraction, and the
        number of groups compared.
    """
    ratios, weights = [], []
    for _, g in d.groupby(key):
        on, off = g[g["discounted"]]["Quantity"], g[~g["discounted"]]["Quantity"]
        if len(on) >= MIN_LINES and len(off) >= MIN_LINES:
            ratios.append(on.mean() / off.mean())
            weights.append(len(on))
    return np.average(ratios, weights=weights) - 1, len(ratios)


def revenue_effect(d, lift):
    """Estimate the net revenue effect of discounts for an assumed lift.

    Without discounts, a discounted line would have sold
    ``1 / (1 + lift)`` of its units at full price. The effect is
    actual revenue minus that.

    Args:
        d (pandas.DataFrame): Order lines with ``UnitPrice``,
            ``Quantity``, ``Discount`` and ``discounted``.
        lift (float): Assumed extra units caused by discounts
            (0.1 = 10%).

    Returns:
        float: Net revenue effect in dollars (negative = revenue lost).
    """
    x = d[d["discounted"]]
    full = x["UnitPrice"] * x["Quantity"]
    return (full * (1 - x["Discount"])).sum() - (full / (1 + lift)).sum()


def break_even_lift(depth):
    """Return the extra sales a discount needs to cover its cost.

    Args:
        depth (float): Discount as a fraction (0.15 = 15% off).

    Returns:
        float: Required extra units as a fraction.
    """
    return depth / (1 - depth)


def bootstrap(d, reps=N_BOOT, seed=SEED):
    """Re-run the comparisons on resampled orders.

    Args:
        d (pandas.DataFrame): Order lines with ``OrderID``.
        reps (int): Number of resamples.
        seed (int): Random seed, so results repeat.

    Returns:
        pandas.DataFrame: 2.5th and 97.5th percentile of the overall,
        same-product and same-customer lift.
    """
    rng = np.random.default_rng(seed)
    groups = {k: g for k, g in d.groupby("OrderID")}
    ids = np.array(list(groups))
    rows = []
    for _ in range(reps):
        pick = rng.choice(ids, size=len(ids), replace=True)
        s = pd.concat([groups[i] for i in pick], ignore_index=True)
        rows.append({"all_lines": lift_overall(s),
                     "same_product": lift_within(s, "ProductID")[0],
                     "same_customer": lift_within(s, "CustomerID")[0]})
    return pd.DataFrame(rows).quantile([0.025, 0.975])


def size_table(d):
    """Measure how often each size of customer gets a discount.

    Customers are split into four equal groups by total units bought.

    Args:
        d (pandas.DataFrame): Order lines with ``CustomerID``,
            ``Quantity``
            and ``discounted``.

    Returns:
        pandas.DataFrame: Customers, lines and discounted share
        per group.
    """
    cust = d.groupby("CustomerID")["Quantity"].sum()
    group = pd.qcut(cust, 4, labels=SIZE_LABELS).rename("size")
    x = d.merge(group, left_on="CustomerID", right_index=True)
    return x.groupby("size", observed=True).agg(
        customers=("CustomerID", "nunique"), lines=("discounted", "size"),
        discounted_share=("discounted", "mean"))


def plot_lift(estimates, needed):
    """Plot extra units for three comparisons vs. break-even.

    Args:
        estimates (dict[str, float]): Extra units as a fraction for
            ``All lines``, ``Same product`` and ``Same customer``.
        needed (float): Extra units a typical discount needs,
            as a fraction.

    Returns:
        None. Saves ``q3_more_units_by_comparison.png``.
    """
    names = list(estimates)
    vals = [v * 100 for v in estimates.values()]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(names, vals, color=[INK_2, BLUE, ORANGE], width=0.55, zorder=2)
    for x, v in enumerate(vals):
        ax.text(x, v + 1, f"+{v:.0f}%", ha="center", fontsize=12, color=INK_2)
    ax.axhline(needed * 100, color="black", lw=1.4, ls=(0, (4, 3)), zorder=3)
    ax.text(2.45, needed * 100 + 1.2, f"Needed to break even: about {needed * 100:.0f}%", ha="right",
            fontsize=10, color="black")
    ax.set_ylabel("Extra units sold on discounted lines (%)")
    ax.set_ylim(0, 40)
    ax.set_title("Extra sales shrink to almost nothing when we compare the same customer")
    ax.grid(axis="x", visible=False)
    save_fig(fig, "q3_more_units_by_comparison")


def plot_revenue(effects):
    """Plot net revenue effect of discounts under three assumed lifts.

    Args:
        effects (dict[str, float]): Net revenue effect in dollars per
            scenario label.

    Returns:
        None. Saves ``q3_revenue_effect.png``.
    """
    names = list(effects)
    vals = [v / 1000 for v in effects.values()]
    colors = [INK_2, ORANGE, BLUE]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(names, vals, color=colors, width=0.55, zorder=2)
    for x, v in enumerate(vals):
        ax.text(x, v + (2 if v >= 0 else -2), f"{v:+.0f}K".replace("-", "−"), ha="center",
                va="bottom" if v >= 0 else "top", fontsize=12, color=INK_2)
    ax.axhline(0, color=INK_2, lw=0.8)
    ax.set_ylabel("Revenue gained or lost from discounting (thousand USD)")
    ax.set_ylim(-110, 75)
    ax.set_title("Do discounts pay for themselves? It depends which lift is real")
    ax.tick_params(axis="x", labelsize=9)
    ax.grid(axis="x", visible=False)
    save_fig(fig, "q3_revenue_effect")


def plot_size(by_size):
    """Plot how often each customer size group gets a discount.

    Args:
        by_size (pandas.DataFrame): Output of ``size_table``.

    Returns:
        None. Saves ``q3_discount_by_customer_size.png``.
    """
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    vals = by_size["discounted_share"] * 100
    ax.bar([str(i) for i in by_size.index], vals, color=BLUE, width=0.55, zorder=2)
    for x, v in enumerate(vals):
        ax.text(x, v + 1, f"{v:.0f}%", ha="center", fontsize=12, color=INK_2)
    ax.set_ylabel("Share of order lines with a discount (%)")
    ax.set_xlabel("Customer size (by total units bought, in four equal groups)")
    ax.set_ylim(0, 60)
    ax.set_title("Bigger customers get discounts more often")
    ax.grid(axis="x", visible=False)
    save_fig(fig, "q3_discount_by_customer_size")


def main():
    """Run the Question 3 analysis, then save tables and figures.

    Args:
        None.

    Returns:
        None. Writes ``q3_*`` tables and figures; prints key numbers.
    """
    apply_style()
    t = load_tables()
    d = build_lines(t)
    d["discounted"] = d["Discount"] > 0
    disc = d[d["discounted"]]
    depth = disc["Discount"].mean()
    needed = break_even_lift(depth)
    all_lines = lift_overall(d)
    same_product, n_products = lift_within(d, "ProductID")
    same_customer, n_customers = lift_within(d, "CustomerID")
    ranges = bootstrap(d)
    by_size = size_table(d)
    given_up = (disc["LineFullPrice"] * disc["Discount"]).sum()
    gross = d["LineFullPrice"].sum()
    effects = {"No extra sales": revenue_effect(d, 0.0),
               f"Same-customer lift (+{same_customer * 100:.0f}%)": revenue_effect(d, same_customer),
               f"Same-product lift (+{same_product * 100:.0f}%)": revenue_effect(d, same_product)}
    avg_units = d.groupby("discounted")["Quantity"].mean()

    key = {
        "order_lines": len(d),
        "share_of_lines_discounted": d["discounted"].mean(),
        "average_discount_when_discounted": depth,
        "break_even_extra_units": needed,
        "avg_units_discounted_lines": avg_units[True],
        "avg_units_full_price_lines": avg_units[False],
        "lift_all_lines": all_lines,
        "lift_same_product": same_product, "products_compared": n_products,
        "lift_same_customer": same_customer, "customers_compared": n_customers,
        "lift_all_lines_low": ranges.loc[0.025, "all_lines"], "lift_all_lines_high": ranges.loc[0.975, "all_lines"],
        "lift_same_product_low": ranges.loc[0.025, "same_product"],
        "lift_same_product_high": ranges.loc[0.975, "same_product"],
        "lift_same_customer_low": ranges.loc[0.025, "same_customer"],
        "lift_same_customer_high": ranges.loc[0.975, "same_customer"],
        "gross_revenue_at_listed_prices": gross,
        "revenue_given_up": given_up, "revenue_given_up_share": given_up / gross,
        "net_effect_no_extra_sales": effects["No extra sales"],
        "net_effect_same_customer_lift": list(effects.values())[1],
        "net_effect_same_product_lift": list(effects.values())[2],
    }
    save_table(by_size, "q3_discount_share_by_customer_size")
    save_table(pd.Series(key, name="value").to_frame(), "q3_key_numbers")
    plot_lift({"All lines": all_lines, "Same product": same_product, "Same customer": same_customer}, needed)
    plot_revenue(effects)
    plot_size(by_size)
    for k, v in key.items():
        print(f"{k}: {v:.4g}" if isinstance(v, (float, np.floating)) else f"{k}: {v}")


if __name__ == "__main__":
    main()
