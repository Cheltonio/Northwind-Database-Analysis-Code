"""Question 3: do discounts lift sales enough to pay for themselves?"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from scipy.stats import chi2_contingency, kruskal, spearmanr

from common import (BLUE, INK, INK_2, ORANGE, PRICE_CUTOVER, apply_style,
                    build_lines, save_fig, save_table)
from load_data import load_tables

TIERS = [0.05, 0.10, 0.15, 0.20, 0.25]
TIER_LABELS = [f"{int(round(k * 100))}%" for k in TIERS]
ANOMALOUS_ORDER = 11077  # carries the only off-tier discounts (1-6%)
N_BOOT = 1000
SEED = 0
SPECS = {
    "product_fe": "Product + before/after price increase",
    "customer_fe": "Product + customer + before/after price increase",
    "month_fe": "Product + calendar month",
}


def tier_data(lines):
    """Prepare order lines for the discount-tier models.

    Drops the order with off-tier discounts and adds ``post`` (1 on
    or after the price increase) and ``log_qty``.

    Args:
        lines (pandas.DataFrame): Order lines from ``build_lines``.

    Returns:
        pandas.DataFrame: Lines on the standard discount tiers.
    """
    d = lines[lines["OrderID"] != ANOMALOUS_ORDER].copy().reset_index(drop=True)
    assert d["Discount"].isin([0.0] + TIERS).all(), "unexpected discount value"
    d["post"] = (d["OrderDate"] >= PRICE_CUTOVER).astype(float)
    d["log_qty"] = np.log(d["Quantity"])
    return d


def design_matrix(d, spec):
    """Build the regression design matrix for a specification.

    Columns: constant, five discount-tier dummies, product dummies,
    then the controls the specification adds.

    Args:
        d (pandas.DataFrame): Output of ``tier_data``.
        spec (str): ``product_fe``, ``customer_fe`` or ``month_fe``.

    Returns:
        numpy.ndarray: Matrix with one row per line.
    """
    parts = [(d["Discount"] == k).astype(float).rename(f"tier_{lab}")
             for k, lab in zip(TIERS, TIER_LABELS)]
    parts.append(pd.get_dummies(d["ProductID"], prefix="p", drop_first=True).astype(float))
    if spec in ("product_fe", "customer_fe"):
        parts.append(d["post"].rename("post"))
    if spec == "customer_fe":
        parts.append(pd.get_dummies(d["CustomerID"], prefix="c", drop_first=True).astype(float))
    if spec == "month_fe":
        parts.append(pd.get_dummies(d["Month"].astype(str), prefix="m", drop_first=True).astype(float))
    x = pd.concat(parts, axis=1)
    x.insert(0, "const", 1.0)
    return x.values


def fit_tiers(x, y):
    """Fit least squares and return the discount-tier coefficients.

    Args:
        x (numpy.ndarray): Design matrix from ``design_matrix``.
        y (numpy.ndarray): Log quantity for each row.

    Returns:
        numpy.ndarray: Five coefficients (5% to 25% tiers) in log units.
    """
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    return beta[1:6]


def revenue_components(price, qty, disc, lifts):
    """Split discount revenue into given up and gained amounts.

    Counterfactual units without the discount are observed units
    divided by (1 + lift), which assumes the whole estimated lift is
    caused by the discount.

    Args:
        price (numpy.ndarray): Pre-discount unit price charged per
            line (``UnitPrice``, not ``ListPrice``).
        qty (numpy.ndarray): Units sold per line.
        disc (numpy.ndarray): Discount rate per line.
        lifts (numpy.ndarray): Fractional unit lift for each tier.

    Returns:
        tuple[numpy.ndarray, numpy.ndarray]: Per tier, revenue given
        up on units that would sell anyway (negative) and revenue
        gained on the extra units.
    """
    given_up = np.zeros(len(TIERS))
    gained = np.zeros(len(TIERS))
    for i, k in enumerate(TIERS):
        m = np.isclose(disc, k)
        q_cf = qty[m] / (1 + lifts[i])
        given_up[i] = -(price[m] * q_cf * k).sum()
        gained[i] = (price[m] * (qty[m] - q_cf) * (1 - k)).sum()
    return given_up, gained


def bootstrap(d, spec, with_revenue=False):
    """Estimate tier lifts with an order-level bootstrap.

    Args:
        d (pandas.DataFrame): Output of ``tier_data``.
        spec (str): Specification name for ``design_matrix``.
        with_revenue (bool): Also compute revenue components.

    Returns:
        dict[str, numpy.ndarray]: ``point`` and ``boot`` coefficients;
        with ``with_revenue``, also ``give_point``, ``gain_point``,
        ``give_boot`` and ``gain_boot``.
    """
    x = design_matrix(d, spec)
    y = d["log_qty"].values
    price, qty, disc = d["UnitPrice"].values, d["Quantity"].values.astype(float), d["Discount"].values
    by_order = d.groupby("OrderID").indices
    order_ids = np.array(list(by_order.keys()))
    rng = np.random.default_rng(SEED)
    coefs, nets, gives, gains = [], [], [], []
    for _ in range(N_BOOT):
        pick = rng.choice(order_ids, len(order_ids))
        ii = np.concatenate([by_order[o] for o in pick])
        b = fit_tiers(x[ii], y[ii])
        coefs.append(b)
        if with_revenue:
            g, a = revenue_components(price[ii], qty[ii], disc[ii], np.exp(b) - 1)
            gives.append(g)
            gains.append(a)
    point = fit_tiers(x, y)
    out = {"point": point, "boot": np.array(coefs)}
    if with_revenue:
        g, a = revenue_components(price, qty, disc, np.exp(point) - 1)
        out.update(give_point=g, gain_point=a, give_boot=np.array(gives), gain_boot=np.array(gains))
    return out


def lift_table(res):
    """Convert tier coefficients to percent lifts with intervals.

    Args:
        res (dict[str, numpy.ndarray]): Output of ``bootstrap``.

    Returns:
        pandas.DataFrame: Per tier: lift, 95% interval bounds and
        break-even lift, all in percent.
    """
    pct = lambda v: (np.exp(v) - 1) * 100
    table = pd.DataFrame({
        "lift_pct": pct(res["point"]),
        "ci_low_pct": pct(np.percentile(res["boot"], 2.5, axis=0)),
        "ci_high_pct": pct(np.percentile(res["boot"], 97.5, axis=0)),
        "break_even_pct": [k / (1 - k) * 100 for k in TIERS],
    }, index=TIER_LABELS)
    table.index.name = "discount_tier"
    return table


def raw_tier_summary(d):
    """Summarize units per line by discount level.

    Args:
        d (pandas.DataFrame): Output of ``tier_data``.

    Returns:
        pandas.DataFrame: Line count, mean and median units, and raw
        lift versus no discount, by discount.
    """
    g = d.groupby("Discount")["Quantity"].agg(lines="count", mean_units="mean", median_units="median")
    g["raw_lift_vs_no_discount_pct"] = (g["mean_units"] / g.loc[0.0, "mean_units"] - 1) * 100
    return g


def revenue_effect_table(res):
    """Tabulate net revenue effect by tier, with a total row.

    Args:
        res (dict[str, numpy.ndarray]): ``bootstrap`` output computed
            with ``with_revenue=True``.

    Returns:
        pandas.DataFrame: Revenue given up, gained, net and its 95%
        interval for each tier and for ``All tiers``.
    """
    give, gain = res["give_point"], res["gain_point"]
    net = give + gain
    net_boot = res["give_boot"] + res["gain_boot"]
    table = pd.DataFrame({
        "given_up_on_baseline_units": give,
        "gained_on_extra_units": gain,
        "net_revenue_effect": net,
        "net_ci_low": np.percentile(net_boot, 2.5, axis=0),
        "net_ci_high": np.percentile(net_boot, 97.5, axis=0),
    }, index=TIER_LABELS)
    total_boot = net_boot.sum(axis=1)
    table.loc["All tiers"] = [give.sum(), gain.sum(), net.sum(),
                              np.percentile(total_boot, 2.5), np.percentile(total_boot, 97.5)]
    table.index.name = "discount_tier"
    return table


def selection_tables(d):
    """Measure who receives discounts.

    The customer correlation uses customers with at least 10 lines.

    Args:
        d (pandas.DataFrame): Output of ``tier_data``.

    Returns:
        tuple[pandas.DataFrame, pandas.DataFrame, float, float, float]:
        Customers, lines and discounted share per customer-volume
        quartile; lines, discounted share and mean depth when
        discounted per employee; Spearman rho of customer units vs.
        discounted share; chi-square p-value of discounting across
        employees; Spearman rho of pre-discount order value vs. mean
        discount.
    """
    d = d.copy()
    d["discounted"] = d["Discount"] > 0
    cust = d.groupby("CustomerID").agg(units=("Quantity", "sum"), lines=("Quantity", "count"),
                                       discounted_share=("discounted", "mean"))
    cust["volume_quartile"] = pd.qcut(cust["units"], 4, labels=["Q1 (smallest)", "Q2", "Q3", "Q4 (largest)"])
    lines_q = d.merge(cust[["volume_quartile"]], left_on="CustomerID", right_index=True)
    by_quartile = lines_q.groupby("volume_quartile", observed=True).agg(
        customers=("CustomerID", "nunique"), lines=("discounted", "size"),
        discounted_share=("discounted", "mean"))
    by_emp = d.groupby("EmployeeID").agg(lines=("discounted", "size"),
                                         discounted_share=("discounted", "mean"))
    by_emp["avg_depth_when_discounted"] = d[d["discounted"]].groupby("EmployeeID")["Discount"].mean()
    big = cust[cust["lines"] >= 10]
    rho = spearmanr(big["units"], big["discounted_share"])[0]
    table = pd.crosstab(d["EmployeeID"], d["discounted"])
    chi_p = chi2_contingency(table)[1]
    order = d.groupby("OrderID").agg(full=("LineFullPrice", "sum"), mean_disc=("Discount", "mean"))
    rho_order = spearmanr(order["full"], order["mean_disc"])[0]
    return by_quartile, by_emp, rho, chi_p, rho_order


SCENARIO_LABELS = {"product_fe": "Same product", "customer_fe": "Same product and same customer"}
SCENARIO_COLORS = {"product_fe": BLUE, "customer_fe": ORANGE}


def point_range(ax, x, point, low, high, color, label, offset):
    """Draw point estimates with vertical interval bars.

    Args:
        ax (matplotlib.axes.Axes): Axes to draw on.
        x (numpy.ndarray): Base x positions.
        point (numpy.ndarray): Point estimates.
        low (numpy.ndarray): Lower interval bounds.
        high (numpy.ndarray): Upper interval bounds.
        color (str): Marker and bar color.
        label (str): Legend label.
        offset (float): Horizontal shift applied to ``x``.

    Returns:
        None. Adds the markers to ``ax``.
    """
    ax.errorbar(x + offset, point, yerr=[point - low, high - point], fmt="o", color=color, ms=7,
                ecolor=color, elinewidth=1.6, capsize=4, label=label, zorder=3)


def plot_lift(tables):
    """Plot estimated unit lift by tier against break-even.

    Args:
        tables (dict[str, pandas.DataFrame]): ``lift_table`` output
            for ``product_fe`` and ``customer_fe``.

    Returns:
        None. Saves ``q3_discount_lift_vs_break_even.png``.
    """
    fig, ax = plt.subplots(figsize=(9, 5.4))
    x = np.arange(len(TIERS))
    for spec, offset in [("product_fe", -0.14), ("customer_fe", 0.14)]:
        tb = tables[spec]
        point_range(ax, x, tb["lift_pct"].values, tb["ci_low_pct"].values, tb["ci_high_pct"].values,
                    SCENARIO_COLORS[spec], f"Compared within: {SCENARIO_LABELS[spec].lower()}", offset)
    be = tables["product_fe"]["break_even_pct"].values
    ax.scatter(x, be, marker="D", s=70, facecolor="none", edgecolor=INK, linewidth=1.4, zorder=4,
               label="Lift needed to break even on revenue")
    for xi, v in zip(x, be):
        ax.annotate(f"{v:.0f}%", (xi, v), xytext=(0, 11), textcoords="offset points", ha="center",
                    fontsize=8.5, color=INK_2, va="center")
    ax.axhline(0, color=INK_2, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(TIER_LABELS)
    ax.set_xlabel("Discount depth")
    ax.set_ylabel("Extra units sold vs. no discount (%, 95% interval)")
    ax.set_title("The unit lift mostly disappears when comparing the same customer")
    ax.legend(loc="upper left", fontsize=8.5)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(-25, 85)
    save_fig(fig, "q3_discount_lift_vs_break_even")


def plot_revenue(rev_by_spec):
    """Plot net revenue effect by tier under two lift estimates.

    Args:
        rev_by_spec (dict[str, pandas.DataFrame]): Revenue effect
            tables, without the total row, for ``product_fe`` and
            ``customer_fe``.

    Returns:
        None. Saves ``q3_revenue_effect.png``.
    """
    labels = list(rev_by_spec["product_fe"].index)
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for spec, offset in [("product_fe", -0.14), ("customer_fe", 0.14)]:
        r = rev_by_spec[spec]
        point_range(ax, x, r["net_revenue_effect"].values / 1000, r["net_ci_low"].values / 1000,
                    r["net_ci_high"].values / 1000, SCENARIO_COLORS[spec],
                    f"Assuming the lift measured within: {SCENARIO_LABELS[spec].lower()}", offset)
        for xi, v in zip(x, r["net_revenue_effect"].values / 1000):
            ax.annotate(f"{v:+.0f}K", (xi + offset, v), xytext=(9 if offset > 0 else -9, 0),
                        textcoords="offset points", va="center",
                        ha="left" if offset > 0 else "right", fontsize=8.5, color=INK_2)
    ax.axhline(0, color=INK_2, lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Discount depth")
    ax.set_ylabel("Revenue vs. selling the same lines with no discount (thousand USD)")
    ax.set_title("Do discounts pay for themselves? It depends on how much lift is real")
    ax.legend(loc="lower left", fontsize=8.5)
    ax.grid(axis="x", visible=False)
    save_fig(fig, "q3_revenue_effect")


def plot_selection(by_quartile, by_emp, overall):
    """Plot discount share by customer size and by employee.

    Args:
        by_quartile (pandas.DataFrame): Discount share per customer
            volume quartile.
        by_emp (pandas.DataFrame): Discount share per employee.
        overall (float): Share of all lines discounted, in 0 to 1.

    Returns:
        None. Saves ``q3_discount_selection.png``.
    """
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.5]})
    q_labels = [str(i) for i in by_quartile.index]
    a1.bar(q_labels, by_quartile["discounted_share"] * 100, color=BLUE, width=0.6, zorder=2)
    for xi, v in enumerate(by_quartile["discounted_share"] * 100):
        a1.text(xi, v + 1, f"{v:.0f}%", ha="center", fontsize=9, color=INK_2)
    a1.set_ylabel("Share of order lines with a discount (%)")
    a1.set_xlabel("Customer size (total units bought)")
    a1.set_title("Bigger customers are discounted more")
    a1.set_ylim(0, 60)
    a1.tick_params(axis="x", labelsize=8)
    a1.grid(axis="x", visible=False)
    emp = by_emp.copy()
    a2.bar([f"Emp {i}" for i in emp.index], emp["discounted_share"] * 100, color=BLUE, width=0.6, zorder=2)
    for xi, v in enumerate(emp["discounted_share"] * 100):
        a2.text(xi, v + 1, f"{v:.0f}%", ha="center", fontsize=9, color=INK_2)
    a2.axhline(overall * 100, color=ORANGE, lw=1.5, ls=(0, (4, 3)), zorder=3)
    a2.text(-0.4, 57, f"Dashed line: all lines, {overall * 100:.0f}%", ha="left", va="center",
            fontsize=8.5, color=INK_2)
    a2.set_xlabel("Employee who took the order")
    a2.set_title("Discount rate varies by employee")
    a2.set_ylim(0, 60)
    a2.grid(axis="x", visible=False)
    save_fig(fig, "q3_discount_selection")


def main():
    """Run the Question 3 analysis, then save tables and figures.

    Args:
        None.

    Returns:
        None. Writes ``q3_*`` tables and figures; prints key numbers.
    """
    apply_style()
    t = load_tables()
    lines = build_lines(t)
    d = tier_data(lines)

    raw = raw_tier_summary(d)
    kw_p = kruskal(*[g["Quantity"].values for _, g in d.groupby("Discount")]).pvalue
    primary = bootstrap(d, "product_fe", with_revenue=True)
    lifts = lift_table(primary)
    rev = revenue_effect_table(primary)

    robust_rows, robust_results = [], {}
    for spec, label in SPECS.items():
        res = primary if spec == "product_fe" else bootstrap(d, spec, with_revenue=(spec == "customer_fe"))
        robust_results[spec] = res
        tab = lift_table(res)
        for tier in TIER_LABELS:
            robust_rows.append({"specification": label, "discount_tier": tier,
                                "lift_pct": tab.loc[tier, "lift_pct"],
                                "ci_low_pct": tab.loc[tier, "ci_low_pct"],
                                "ci_high_pct": tab.loc[tier, "ci_high_pct"]})
    robust = pd.DataFrame(robust_rows)
    lifts_cust = lift_table(robust_results["customer_fe"])
    rev_cust = revenue_effect_table(robust_results["customer_fe"])

    diff_boot = primary["boot"][:, 4] - primary["boot"][:, 0]
    diff_point = primary["point"][4] - primary["point"][0]
    by_quartile, by_emp, rho_customer, chi_p, rho_order = selection_tables(d)
    overall_share = (d["Discount"] > 0).mean()

    gross = lines["LineFullPrice"].sum()
    given_up_all = (lines["LineFullPrice"] - lines["LineRevenue"]).sum()
    key = {
        "order_lines": len(lines),
        "lines_in_tier_analysis": len(d),
        "share_of_lines_discounted": (lines["Discount"] > 0).mean(),
        "gross_revenue_at_listed_prices": gross,
        "revenue_given_up_all_lines": given_up_all,
        "revenue_given_up_share_of_gross": given_up_all / gross,
        "mean_units_no_discount": raw.loc[0.0, "mean_units"],
        "mean_units_discounted": d.loc[d["Discount"] > 0, "Quantity"].mean(),
        "kruskal_wallis_p": kw_p,
        "lift_5pct": lifts.loc["5%", "lift_pct"], "lift_25pct": lifts.loc["25%", "lift_pct"],
        "lift_25_minus_5_pts_log": diff_point,
        "lift_25_minus_5_ci_low_log": np.percentile(diff_boot, 2.5),
        "lift_25_minus_5_ci_high_log": np.percentile(diff_boot, 97.5),
        "net_revenue_effect_all_tiers": rev.loc["All tiers", "net_revenue_effect"],
        "net_revenue_effect_ci_low": rev.loc["All tiers", "net_ci_low"],
        "net_revenue_effect_ci_high": rev.loc["All tiers", "net_ci_high"],
        "net_revenue_effect_customer_fe": rev_cust.loc["All tiers", "net_revenue_effect"],
        "net_revenue_effect_customer_fe_ci_low": rev_cust.loc["All tiers", "net_ci_low"],
        "net_revenue_effect_customer_fe_ci_high": rev_cust.loc["All tiers", "net_ci_high"],
        "tiers_where_ci_low_below_break_even": int((lifts["ci_low_pct"] < lifts["break_even_pct"]).sum()),
        "spearman_customer_units_vs_discount_share": rho_customer,
        "spearman_order_value_vs_mean_discount": rho_order,
        "employee_discount_share_min": by_emp["discounted_share"].min(),
        "employee_discount_share_max": by_emp["discounted_share"].max(),
        "employee_chi2_p_lines_not_clustered": chi_p,
        "bootstrap_reps": N_BOOT,
    }
    save_table(raw, "q3_raw_tier_summary")
    save_table(lifts, "q3_lift_primary")
    save_table(robust, "q3_lift_robustness", index=False)
    save_table(rev, "q3_revenue_effect")
    save_table(rev_cust, "q3_revenue_effect_customer_fe")
    save_table(by_quartile, "q3_discount_share_by_customer_size")
    save_table(by_emp, "q3_discount_share_by_employee")
    save_table(pd.Series(key, name="value").to_frame(), "q3_key_numbers")
    plot_lift({"product_fe": lifts, "customer_fe": lifts_cust})
    plot_revenue({"product_fe": rev.drop(index="All tiers"), "customer_fe": rev_cust.drop(index="All tiers")})
    plot_selection(by_quartile, by_emp, overall_share)
    for k, v in key.items():
        print(f"{k}: {v:.4g}" if isinstance(v, (float, np.floating)) else f"{k}: {v}")
    print(lifts.round(1).to_string())
    print(robust.round(1).to_string(index=False))
    print(rev.round(0).to_string())
    print(rev_cust.round(0).to_string())


if __name__ == "__main__":
    main()
