# Northwind: three business questions

Analysis of the Northwind database (HW3, 15.561 "AI-Assisted Business Data Analysis"). Webpage: `docs/index.html`
(published with GitHub Pages from the `docs/` folder). All code is Python.

## Questions
1. **Inventory.** Do reorder levels and stock positions reflect demand, and which high-revenue products are least protected?
2. **Market growth.** Is growth coming from more customers, more orders per customer, or larger orders, and where should sales focus?
3. **Discounts.** Do discounts lift sales enough to justify the revenue given up?

## Reproduce everything
Tested with Python 3.13.

```bash
pip install -r requirements.txt
python src/run_all.py
```

`run_all.py` runs, in order:

| Step | Script | Produces |
|---|---|---|
| 1 | `src/extract_data.py` | `data/extracted/*.csv` from `data/raw/Northwind_Database.pdf` |
| 2 | `src/q1_inventory.py` | `outputs/tables/q1_*.csv`, `outputs/figures/q1_*.png` |
| 3 | `src/q2_markets.py` | `outputs/tables/q2_*.csv`, `outputs/figures/q2_*.png` |
| 4 | `src/q3_discounts.py` | `outputs/tables/q3_*.csv`, `outputs/figures/q3_*.png` |

It then copies the figures into `docs/figures/` for the webpage. Each script can also be run alone from `src/`
(`cd src && python q1_inventory.py`) once `data/extracted/` exists. Every number quoted on the webpage appears in a
`*_key_numbers.csv` or another table in `outputs/tables/`. Q3 uses a bootstrap with a fixed seed (0, 1000 resamples),
so results are identical across runs; it takes about 25 seconds.

## Code layout
- `extract_data.py`: reads tables from the PDF with pdfplumber; the employees page is garbled, so it is parsed from page text with pypdf.
- `load_data.py`: loads the CSVs and types the columns.
- `common.py`: shared constants (analysis windows, price-increase date), plot style, table/figure saving, and `build_lines` (one row per order line).
- `q1_inventory.py`, `q2_markets.py`, `q3_discounts.py`: one script per question.
- `run_all.py`: runs the full pipeline.

## Method choices that matter
- **Constant-price revenue** = list price × quantity × (1 − discount). Prices rose a uniform 25% on 1997-04-07, so nominal revenue would overstate growth.
- **Windows.** Data ends 1998-05-06, so May 1998 is dropped. Q1 uses Nov 1997 to Apr 1998 for demand (3-month and all-time as sensitivity); Q2 compares Jul 1996 to Apr 1997 with Jul 1997 to Apr 1998.
- **Q2 decomposition:** revenue = customers × orders per customer × revenue per order, with dollar attribution by logarithmic-mean weights.
- **Q3:** regressions of log quantity on discount-tier indicators with product fixed effects, with customer and month fixed effects as robustness checks; order-level bootstrap intervals. Order 11077 has off-tier discounts and is excluded from the tier models.

## Limitations
- Stock levels are one undated snapshot. There is no cost, margin or lead-time data, so results are about revenue, not profit.
- Discounts were not randomized, so Q3 reports associations; the same-customer comparison shows much of the raw lift reflects which customers get discounts.
- Some countries have only a few customers, so country-level gaps are noisy.
- Phone and fax columns in the suppliers table are scrambled in the PDF and are dropped.

## Use of AI
Code was written with Claude. Docstrings follow the python-docstrings skill (`SKILL.md`).
