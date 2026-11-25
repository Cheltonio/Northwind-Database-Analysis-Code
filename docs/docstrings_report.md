# Docstrings report

Generated from the current code in `src/` after running the `python-docstrings` skill. Style: Google, lines at most 72 characters.


## src/common.py

#### `module` — [src/common.py:1](src/common.py:1)
```python
"""Shared constants, plot style and table helpers."""
```

#### `apply_style` — [src/common.py:27](src/common.py:27)
```python
"""Set matplotlib rcParams to the project chart style.

Args:
    None.

Returns:
    None. Updates ``matplotlib.pyplot.rcParams`` in place.
"""
```

#### `ensure_dirs` — [src/common.py:51](src/common.py:51)
```python
"""Create the output table and figure folders if missing.

Args:
    None.

Returns:
    None. Creates ``TABLE_DIR`` and ``FIG_DIR``.
"""
```

#### `save_table` — [src/common.py:64](src/common.py:64)
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

#### `save_fig` — [src/common.py:79](src/common.py:79)
```python
"""Save a figure as a PNG in ``FIG_DIR`` and close it.

Args:
    fig (matplotlib.figure.Figure): Figure to save.
    name (str): File name without the ``.png`` extension.

Returns:
    None. Writes ``FIG_DIR/<name>.png``.
"""
```

#### `build_lines` — [src/common.py:94](src/common.py:94)
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

#### `module` — [src/extract_data.py:1](src/extract_data.py:1)
```python
"""Extract the Northwind tables from the source PDF into CSV files."""
```

#### `table_name_from_header` — [src/extract_data.py:32](src/extract_data.py:32)
```python
"""Identify which Northwind table a header row belongs to.

Args:
    header (list[str]): Cell texts of the table's first row.

Returns:
    str | None: Table name, or None if the header is unrecognized.
"""
```

#### `clean_cell` — [src/extract_data.py:55](src/extract_data.py:55)
```python
"""Collapse whitespace in a table cell.

Args:
    value (Any): Raw cell value from pdfplumber, possibly None.

Returns:
    str | None: Cleaned text, or None if empty or missing.
"""
```

#### `extract_pdf_tables` — [src/extract_data.py:70](src/extract_data.py:70)
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

#### `parse_employees` — [src/extract_data.py:101](src/extract_data.py:101)
```python
"""Parse the employees table from the PDF page text.

Args:
    pdf_path (str | pathlib.Path): Path of the Northwind PDF.

Returns:
    pandas.DataFrame: One row per employee with name, title,
    dates, location and ``ReportsTo``.
"""
```

#### `main` — [src/extract_data.py:143](src/extract_data.py:143)
```python
"""Extract all tables from the PDF and write them as CSV files.

Args:
    None. Reads ``--pdf`` and ``--out`` from the command line.

Returns:
    None. Writes one CSV per table and prints row counts.
"""
```


## src/load_data.py

#### `module` — [src/load_data.py:1](src/load_data.py:1)
```python
"""Load the extracted Northwind CSV files and convert column types."""
```

#### `to_number` — [src/load_data.py:18](src/load_data.py:18)
```python
"""Convert text to numbers, removing thousands separators.

Args:
    series (pandas.Series): Values such as ``"1,234.50"``.

Returns:
    pandas.Series: Float values; unparseable entries are NaN.
"""
```

#### `load_tables` — [src/load_data.py:30](src/load_data.py:30)
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

#### `module` — [src/q1_inventory.py:1](src/q1_inventory.py:1)
```python
"""Question 1: how well reorder levels and stock match recent demand."""
```

#### `monthly_units` — [src/q1_inventory.py:23](src/q1_inventory.py:23)
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

#### `build_product_table` — [src/q1_inventory.py:41](src/q1_inventory.py:41)
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

#### `reorder_correlations` — [src/q1_inventory.py:72](src/q1_inventory.py:72)
```python
"""Compute Spearman correlations of demand with stock fields.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    pandas.DataFrame: Rho and p-value for each window and each of
    reorder level, units in stock and units on order.
"""
```

#### `flag_stability` — [src/q1_inventory.py:91](src/q1_inventory.py:91)
```python
"""Count active products under 30 days of cover in each window.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    pandas.DataFrame: Flagged-product count per window, plus the
    number flagged in all windows (repeated on every row).
"""
```

#### `supplier_rollup` — [src/q1_inventory.py:113](src/q1_inventory.py:113)
```python
"""Summarize recent revenue and low-cover exposure by supplier.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    pandas.DataFrame: One row per supplier, sorted by recent
    revenue.
"""
```

#### `plot_cover` — [src/q1_inventory.py:135](src/q1_inventory.py:135)
```python
"""Plot days of cover for the 15 highest-revenue products.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.

Returns:
    None. Saves ``q1_cover_top_products.png``.
"""
```

#### `plot_reorder` — [src/q1_inventory.py:175](src/q1_inventory.py:175)
```python
"""Plot reorder level against recent monthly demand.

Args:
    d (pandas.DataFrame): Output of ``build_product_table``.
    rho (float): Spearman correlation shown in the title.

Returns:
    None. Saves ``q1_reorder_vs_demand.png``.
"""
```

#### `main` — [src/q1_inventory.py:215](src/q1_inventory.py:215)
```python
"""Run the Question 1 analysis, then save tables and figures.

Args:
    None.

Returns:
    None. Writes ``q1_*`` tables and figures; prints key numbers.
"""
```


## src/q2_growth.py

#### `module` — [src/q2_growth.py:1](src/q2_growth.py:1)
```python
"""Question 2: where revenue growth came from."""
```

#### `in_window` — [src/q2_growth.py:17](src/q2_growth.py:17)
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

#### `quarterly` — [src/q2_growth.py:31](src/q2_growth.py:31)
```python
"""Count orders and customers by quarter, Jul 1996 to Mar 1998.

Args:
    lines (pandas.DataFrame): Order lines from ``build_lines``.

Returns:
    pandas.DataFrame: Per quarter: orders, active customers, units,
    new customers and customers who have ever ordered.
"""
```

#### `cohort_check` — [src/q2_growth.py:53](src/q2_growth.py:53)
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

#### `customer_concentration` — [src/q2_growth.py:93](src/q2_growth.py:93)
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

#### `plot_quarterly` — [src/q2_growth.py:112](src/q2_growth.py:112)
```python
"""Plot quarterly orders against customers who have ordered.

Args:
    q (pandas.DataFrame): Output of ``quarterly``.

Returns:
    None. Saves ``q2_orders_vs_customer_base.png``.
"""
```

#### `driver_summary` — [src/q2_growth.py:136](src/q2_growth.py:136)
```python
"""Compare the two windows on revenue and its three building blocks.

Revenue = customers x orders per customer x revenue per order, so
the three percent changes multiply to the revenue change.

Args:
    lines (pandas.DataFrame): Order lines with ``CPRev``.

Returns:
    pandas.DataFrame: One row per measure with its value in each
    window and the percent change between them.
"""
```

#### `plot_drivers` — [src/q2_growth.py:162](src/q2_growth.py:162)
```python
"""Plot the percent change in revenue and its three building blocks.

Args:
    summary (pandas.DataFrame): Output of ``driver_summary``.

Returns:
    None. Saves ``q2_growth_drivers.png``.
"""
```

#### `main` — [src/q2_growth.py:192](src/q2_growth.py:192)
```python
"""Run the Question 2 analysis, then save tables and figures.

Args:
    None.

Returns:
    None. Writes ``q2_*`` tables and figures; prints key numbers.
"""
```


## src/q3_discounts.py

#### `module` — [src/q3_discounts.py:1](src/q3_discounts.py:1)
```python
"""Question 3: do discounts bring in enough extra sales to pay off?"""
```

#### `lift_overall` — [src/q3_discounts.py:17](src/q3_discounts.py:17)
```python
"""Compare average units on discounted and full-price lines.

Args:
    d (pandas.DataFrame): Order lines with ``Quantity`` and the
        boolean column ``discounted``.

Returns:
    float: Extra units on discounted lines, as a fraction
    (0.26 = 26% more).
"""
```

#### `lift_within` — [src/q3_discounts.py:32](src/q3_discounts.py:32)
```python
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
```

#### `revenue_effect` — [src/q3_discounts.py:57](src/q3_discounts.py:57)
```python
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
```

#### `break_even_lift` — [src/q3_discounts.py:78](src/q3_discounts.py:78)
```python
"""Return the extra sales a discount needs to cover its cost.

Args:
    depth (float): Discount as a fraction (0.15 = 15% off).

Returns:
    float: Required extra units as a fraction.
"""
```

#### `bootstrap` — [src/q3_discounts.py:90](src/q3_discounts.py:90)
```python
"""Re-run the comparisons on resampled orders.

Args:
    d (pandas.DataFrame): Order lines with ``OrderID``.
    reps (int): Number of resamples.
    seed (int): Random seed, so results repeat.

Returns:
    pandas.DataFrame: 2.5th and 97.5th percentile of the overall,
    same-product and same-customer lift.
"""
```

#### `size_table` — [src/q3_discounts.py:115](src/q3_discounts.py:115)
```python
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
```

#### `plot_lift` — [src/q3_discounts.py:137](src/q3_discounts.py:137)
```python
"""Plot extra units for three comparisons vs. break-even.

Args:
    estimates (dict[str, float]): Extra units as a fraction for
        ``All lines``, ``Same product`` and ``Same customer``.
    needed (float): Extra units a typical discount needs,
        as a fraction.

Returns:
    None. Saves ``q3_more_units_by_comparison.png``.
"""
```

#### `plot_revenue` — [src/q3_discounts.py:165](src/q3_discounts.py:165)
```python
"""Plot net revenue effect of discounts under three assumed lifts.

Args:
    effects (dict[str, float]): Net revenue effect in dollars per
        scenario label.

Returns:
    None. Saves ``q3_revenue_effect.png``.
"""
```

#### `plot_size` — [src/q3_discounts.py:192](src/q3_discounts.py:192)
```python
"""Plot how often each customer size group gets a discount.

Args:
    by_size (pandas.DataFrame): Output of ``size_table``.

Returns:
    None. Saves ``q3_discount_by_customer_size.png``.
"""
```

#### `main` — [src/q3_discounts.py:214](src/q3_discounts.py:214)
```python
"""Run the Question 3 analysis, then save tables and figures.

Args:
    None.

Returns:
    None. Writes ``q3_*`` tables and figures; prints key numbers.
"""
```


## src/run_all.py

#### `module` — [src/run_all.py:1](src/run_all.py:1)
```python
"""Run the full pipeline: extraction, then every table and figure."""
```

#### `main` — [src/run_all.py:13](src/run_all.py:13)
```python
"""Run extraction and all three analyses, then copy the figures.

Args:
    None.

Returns:
    None. Stops with an error if any step fails.
"""
```


46 docstrings in total.

## Assumptions to check

1. `lift_within` / `key`: groups are compared only when they have at least 3 discounted and 3 full-price lines (`MIN_LINES`), and each group's ratio is weighted by its number of discounted lines.
2. `revenue_effect` / `lift`: assumed that without the discount a discounted line would have sold `1 / (1 + lift)` of its units at the full `UnitPrice`.
3. `break_even_lift` / `depth`: called with the average discount depth on discounted lines, so the break-even is approximate.
4. `driver_summary`: windows come from `common.WINDOW_A` and `WINDOW_B`, and revenue is constant-price (`CPRev`).
5. `bootstrap`: resamples whole orders with replacement, 300 times, seed 0, and returns the 2.5th and 97.5th percentiles.

## Also noticed

- Nothing in the code was changed by the docstring pass.
