# Docstrings written (python-docstrings skill)

## src/common.py

#### module — [src/common.py:1](src/common.py:1)
```python
"""Shared constants, plot style and table helpers."""
```

#### `apply_style` — [src/common.py:26](src/common.py:26)
```python
"""Set matplotlib rcParams to the project chart style.

Args:
    None.

Returns:
    None. Updates ``matplotlib.pyplot.rcParams`` in place.
"""
```

#### `ensure_dirs` — [src/common.py:50](src/common.py:50)
```python
"""Create the output table and figure folders if missing.

Args:
    None.

Returns:
    None. Creates ``TABLE_DIR`` and ``FIG_DIR``.
"""
```

#### `save_table` — [src/common.py:63](src/common.py:63)
```python
"""Write a DataFrame to ``TABLE_DIR`` as a CSV file.

Args:
    df (pandas.DataFrame): Table to save.
    name (str): File name without the ``.csv`` extension.
    index (bool): Whether to write the index column.

Returns:
    None. Writes ``TABLE_DIR/<name>.csv``.
"""
```

#### `save_fig` — [src/common.py:78](src/common.py:78)
```python
"""Save a figure as a PNG in ``FIG_DIR`` and close it.

Args:
    fig (matplotlib.figure.Figure): Figure to save.
    name (str): File name without the ``.png`` extension.

Returns:
    None. Writes ``FIG_DIR/<name>.png``.
"""
```

#### `build_lines` — [src/common.py:93](src/common.py:93)
```python
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
```

## src/extract_data.py

#### module — [src/extract_data.py:1](src/extract_data.py:1)
```python
"""Extract the Northwind tables from the source PDF into CSV files."""
```

#### `table_name_from_header` — [src/extract_data.py:31](src/extract_data.py:31)
```python
"""Identify which Northwind table a header row belongs to.

Args:
    header (list[str]): Cell texts of the table's first row.

Returns:
    str | None: Table name, or None if the header is unrecognized.
"""
```

#### `clean_cell` — [src/extract_data.py:54](src/extract_data.py:54)
```python
"""Collapse whitespace in a table cell.

Args:
    value (Any): Raw cell value from pdfplumber, possibly None.

Returns:
    str | None: Cleaned text, or None if empty or missing.
"""
```

#### `extract_pdf_tables` — [src/extract_data.py:69](src/extract_data.py:69)
```python
"""Collect the rows of each table found in the PDF.

Rows continue the most recent header's table across pages; the
employees table is skipped.

Args:
    pdf_path (str | pathlib.Path): Path of the Northwind PDF.

Returns:
    tuple[dict[str, list[list]], dict[str, list]]: Rows per table
    name, and the header row per table name.
"""
```

#### `parse_employees` — [src/extract_data.py:100](src/extract_data.py:100)
```python
"""Parse the employees table from the PDF page text.

Args:
    pdf_path (str | pathlib.Path): Path of the Northwind PDF.

Returns:
    pandas.DataFrame: One row per employee with name, title,
    dates, location and ``ReportsTo``.
"""
```

#### `main` — [src/extract_data.py:142](src/extract_data.py:142)
```python
"""Extract all tables from the PDF and write them as CSV files.

Args:
    None. Reads ``--pdf`` and ``--out`` from the command line.

Returns:
    None. Writes one CSV per table and prints row counts.
"""
```

## src/load_data.py

#### module — [src/load_data.py:1](src/load_data.py:1)
```python
"""Load the extracted Northwind CSV files and convert column types."""
```

#### `to_number` — [src/load_data.py:17](src/load_data.py:17)
```python
"""Convert text to numbers, removing thousands separators.

Args:
    series (pandas.Series): Values such as ``"1,234.50"``.

Returns:
    pandas.Series: Float values; unparseable entries are NaN.
"""
```

#### `load_tables` — [src/load_data.py:29](src/load_data.py:29)
```python
"""Read every extracted CSV and type the columns used downstream.

Args:
    data_dir (pathlib.Path): Folder holding the extracted CSVs.

Returns:
    dict[str, pandas.DataFrame]: Tables keyed by file name stem
    (``orders``, ``order_details``, ``products``, ...).
    ``order_details`` gains ``LineRevenue`` and ``LineFullPrice``.
"""
```

## src/q1_inventory.py

#### module — [src/q1_inventory.py:1](src/q1_inventory.py:1)
```python
"""Question 1: how well reorder levels and stock match recent demand."""
```

#### `monthly_units` — [src/q1_inventory.py:22](src/q1_inventory.py:22)
```python
"""Total units per product and month, to the last full month.

Args:
    lines (pandas.DataFrame): Order lines from ``build_lines``.

Returns:
    tuple[pandas.DataFrame, pandas.DataFrame]: Units by ProductID
    (rows) and month (columns, zero-filled), and the order lines
    up to the last full month.
"""
```

#### `build_product_table` — [src/q1_inventory.py:40](src/q1_inventory.py:40)
```python
"""Build the per-product demand, cover and revenue table.

Args:
    t (dict[str, pandas.DataFrame]): Tables from ``load_tables``.
    lines (pandas.DataFrame): Order lines from ``build_lines``.

Returns:
    pandas.DataFrame: One row per product, sorted by recent
    revenue, with demand and cover days for each window.
"""
```

#### `reorder_correlations` — [src/q1_inventory.py:71](src/q1_inventory.py:71)
```python
"""Compute Spearman correlations of demand with stock fields.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    pandas.DataFrame: Rho and p-value for each window and each of
    reorder level, units in stock and units on order.
"""
```

#### `flag_stability` — [src/q1_inventory.py:90](src/q1_inventory.py:90)
```python
"""Count active products under 30 days of cover in each window.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    pandas.DataFrame: Flagged-product count per window, plus the
    number flagged in all windows (repeated on every row).
"""
```

#### `supplier_rollup` — [src/q1_inventory.py:112](src/q1_inventory.py:112)
```python
"""Summarize recent revenue and low-cover exposure by supplier.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    pandas.DataFrame: One row per supplier, sorted by recent
    revenue.
"""
```

#### `plot_cover` — [src/q1_inventory.py:134](src/q1_inventory.py:134)
```python
"""Plot days of cover for the 15 highest-revenue products.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    None. Saves ``q1_cover_top_products.png``.
"""
```

#### `plot_reorder` — [src/q1_inventory.py:172](src/q1_inventory.py:172)
```python
"""Plot reorder level against recent monthly demand.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.
    rho (float): Spearman correlation shown in the title.

Returns:
    None. Saves ``q1_reorder_vs_demand.png``.
"""
```

#### `main` — [src/q1_inventory.py:212](src/q1_inventory.py:212)
```python
"""Run the Question 1 analysis, then save tables and figures.

Args:
    None.

Returns:
    None. Writes ``q1_*`` tables and figures; prints key numbers.
"""
```

## src/q2_markets.py

#### module — [src/q2_markets.py:1](src/q2_markets.py:1)
```python
"""Question 2: sources of revenue growth by market."""
```

#### `in_window` — [src/q2_markets.py:19](src/q2_markets.py:19)
```python
"""Select order lines whose order date falls inside a window.

Args:
    lines (pandas.DataFrame): Order lines with ``OrderDate``.
    window (tuple[pandas.Timestamp, pandas.Timestamp]): First and
        last date, inclusive.

Returns:
    pandas.DataFrame: The matching rows.
"""
```

#### `window_stats` — [src/q2_markets.py:33](src/q2_markets.py:33)
```python
"""Compute revenue, orders and customers for each group.

Args:
    lines (pandas.DataFrame): Order lines with ``CPRev``.
    group_col (str): Column to group by, such as ``Country``.

Returns:
    pandas.DataFrame: Per group: revenue, orders, customers,
    orders per customer and revenue per order.
"""
```

#### `decompose` — [src/q2_markets.py:54](src/q2_markets.py:54)
```python
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
```

#### `quarterly` — [src/q2_markets.py:89](src/q2_markets.py:89)
```python
"""Count orders and customers by quarter, Jul 1996 to Mar 1998.

Args:
    lines (pandas.DataFrame): Order lines from ``build_lines``.

Returns:
    pandas.DataFrame: Per quarter: orders, active customers, units,
    new customers and customers who have ever ordered.
"""
```

#### `cohort_check` — [src/q2_markets.py:111](src/q2_markets.py:111)
```python
"""Compare early customers with later joiners across windows.

Early customers placed their first order before 1 October 1996.

Args:
    lines (pandas.DataFrame): Order lines with ``CPRev``.

Returns:
    pandas.DataFrame: One row each for all customers, early
    customers and later joiners, with growth metrics and share of
    company growth.
"""
```

#### `customer_concentration` — [src/q2_markets.py:151](src/q2_markets.py:151)
```python
"""Rank customers by revenue with each customer's share.

Args:
    lines (pandas.DataFrame): Order lines with ``CPRev``.
    customers (pandas.DataFrame): Customers with ``CustomerID``,
        ``CompanyName`` and ``Country``.

Returns:
    pandas.DataFrame: Customers sorted by revenue with share and
    cumulative share.
"""
```

#### `shipcountry_sensitivity` — [src/q2_markets.py:170](src/q2_markets.py:170)
```python
"""Compare customer-country and ship-country market attribution.

Args:
    lines (pandas.DataFrame): Order lines with ``Country`` and
        ``ShipCountry``.

Returns:
    pandas.DataFrame: Per country: revenue under each attribution
    for both windows, absolute differences and growth gaps.
"""
```

#### `plot_drivers` — [src/q2_markets.py:197](src/q2_markets.py:197)
```python
"""Plot revenue change by market, split by growth driver.

Args:
    grouped (pandas.DataFrame): Output of ``decompose`` by market
        group.

Returns:
    None. Saves ``q2_growth_drivers_by_market.png``.
"""
```

#### `plot_gap` — [src/q2_markets.py:239](src/q2_markets.py:239)
```python
"""Plot each country's revenue gap versus company growth.

Args:
    full (pandas.DataFrame): Output of ``decompose`` by country.
    cust_counts (pandas.Series): Customers on file per country.

Returns:
    None. Saves ``q2_gap_vs_company_growth.png``.
"""
```

#### `plot_quarterly` — [src/q2_markets.py:270](src/q2_markets.py:270)
```python
"""Plot quarterly orders against customers who have ordered.

Args:
    q (pandas.DataFrame): Output of ``quarterly``.

Returns:
    None. Saves ``q2_orders_vs_customer_base.png``.
"""
```

#### `main` — [src/q2_markets.py:294](src/q2_markets.py:294)
```python
"""Run the Question 2 analysis, then save tables and figures.

Args:
    None.

Returns:
    None. Writes ``q2_*`` tables and figures; prints key numbers.
"""
```

## src/q3_discounts.py

#### module — [src/q3_discounts.py:1](src/q3_discounts.py:1)
```python
"""Question 3: do discounts lift sales enough to pay for themselves?"""
```

#### `tier_data` — [src/q3_discounts.py:25](src/q3_discounts.py:25)
```python
"""Prepare order lines for the discount-tier models.

Drops the order with off-tier discounts and adds ``post`` (1 on
or after the price increase) and ``log_qty``.

Args:
    lines (pandas.DataFrame): Order lines from ``build_lines``.

Returns:
    pandas.DataFrame: Lines on the standard discount tiers.
"""
```

#### `design_matrix` — [src/q3_discounts.py:44](src/q3_discounts.py:44)
```python
"""Build the regression design matrix for a specification.

Columns: constant, five discount-tier dummies, product dummies,
then the controls the specification adds.

Args:
    d (pandas.DataFrame): Output of ``tier_data``.
    spec (str): ``product_fe``, ``customer_fe`` or ``month_fe``.

Returns:
    numpy.ndarray: Matrix with one row per line.
"""
```

#### `fit_tiers` — [src/q3_discounts.py:71](src/q3_discounts.py:71)
```python
"""Fit least squares and return the discount-tier coefficients.

Args:
    x (numpy.ndarray): Design matrix from ``design_matrix``.
    y (numpy.ndarray): Log quantity for each row.

Returns:
    numpy.ndarray: Five coefficients (5% to 25% tiers) in log units.
"""
```

#### `revenue_components` — [src/q3_discounts.py:85](src/q3_discounts.py:85)
```python
"""Split discount revenue into given up and gained amounts.

Counterfactual units without the discount are observed units
divided by (1 + lift), which assumes the whole estimated lift is
caused by the discount.

Args:
    price (numpy.ndarray): List unit price per line.
    qty (numpy.ndarray): Units sold per line.
    disc (numpy.ndarray): Discount rate per line.
    lifts (numpy.ndarray): Fractional unit lift for each tier.

Returns:
    tuple[numpy.ndarray, numpy.ndarray]: Per tier, revenue given
    up on units that would sell anyway (negative) and revenue
    gained on the extra units.
"""
```

#### `bootstrap` — [src/q3_discounts.py:113](src/q3_discounts.py:113)
```python
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
```

#### `lift_table` — [src/q3_discounts.py:150](src/q3_discounts.py:150)
```python
"""Convert tier coefficients to percent lifts with intervals.

Args:
    res (dict[str, numpy.ndarray]): Output of ``bootstrap``.

Returns:
    pandas.DataFrame: Per tier: lift, 95% interval bounds and
    break-even lift, all in percent.
"""
```

#### `raw_tier_summary` — [src/q3_discounts.py:171](src/q3_discounts.py:171)
```python
"""Summarize units per line by discount level.

Args:
    d (pandas.DataFrame): Output of ``tier_data``.

Returns:
    pandas.DataFrame: Line count, mean and median units, and raw
    lift versus no discount, by discount.
"""
```

#### `revenue_effect_table` — [src/q3_discounts.py:186](src/q3_discounts.py:186)
```python
"""Tabulate net revenue effect by tier, with a total row.

Args:
    res (dict[str, numpy.ndarray]): ``bootstrap`` output computed
        with ``with_revenue=True``.

Returns:
    pandas.DataFrame: Revenue given up, gained, net and its 95%
    interval for each tier and for ``All tiers``.
"""
```

#### `selection_tables` — [src/q3_discounts.py:214](src/q3_discounts.py:214)
```python
"""Measure who receives discounts.

The customer correlation uses customers with at least 10 lines.

Args:
    d (pandas.DataFrame): Output of ``tier_data``.

Returns:
    tuple: Discount share by customer-size quartile; by employee;
    Spearman rho of customer units and discount share; chi-square
    p-value across employees; Spearman rho of order value and mean
    discount.
"""
```

#### `point_range` — [src/q3_discounts.py:253](src/q3_discounts.py:253)
```python
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
```

#### `plot_lift` — [src/q3_discounts.py:273](src/q3_discounts.py:273)
```python
"""Plot estimated unit lift by tier against break-even.

Args:
    tables (dict[str, pandas.DataFrame]): ``lift_table`` output
        for ``product_fe`` and ``customer_fe``.

Returns:
    None. Saves ``q3_discount_lift_vs_break_even.png``.
"""
```

#### `plot_revenue` — [src/q3_discounts.py:307](src/q3_discounts.py:307)
```python
"""Plot net revenue effect by tier under two lift estimates.

Args:
    rev_by_spec (dict[str, pandas.DataFrame]): Revenue effect
        tables, without the total row, for ``product_fe`` and
        ``customer_fe``.

Returns:
    None. Saves ``q3_revenue_effect.png``.
"""
```

#### `plot_selection` — [src/q3_discounts.py:341](src/q3_discounts.py:341)
```python
"""Plot discount share by customer size and by employee.

Args:
    by_quartile (pandas.DataFrame): Discount share per customer
        volume quartile.
    by_emp (pandas.DataFrame): Discount share per employee.
    overall (float): Share of all lines discounted, in 0 to 1.

Returns:
    None. Saves ``q3_discount_selection.png``.
"""
```

#### `main` — [src/q3_discounts.py:378](src/q3_discounts.py:378)
```python
"""Run the Question 3 analysis, then save tables and figures.

Args:
    None.

Returns:
    None. Writes ``q3_*`` tables and figures; prints key numbers.
"""
```

## src/run_all.py

#### module — [src/run_all.py:1](src/run_all.py:1)
```python
"""Run the full pipeline: extraction, then every table and figure."""
```

#### `main` — [src/run_all.py:12](src/run_all.py:12)
```python
"""Run extraction and all three analyses, then copy the figures.

Args:
    None.

Returns:
    None. Stops with an error if any step fails.
"""
```
