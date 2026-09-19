# Food Delivery Order Processor

A Python program that processes a batch of food orders, calculates totals
with tiered discounts and delivery charges, handles invalid orders without
crashing, finds the highest-value order, and writes a daily sales report to
a file. Standard library only — no external packages or frameworks.

## Files

```
.
├── food_delivery.py     # the program
├── sample_orders.json   # 12 sample orders (2 deliberately invalid)
├── sales_summary.txt    # generated daily sales report (produced by running the program)
├── obstacle_log.md      # issues hit while building this, and how they were solved
└── README.md
```

## Run it

```bash
python3 food_delivery.py
```

It processes every order in `sample_orders.json`, prints an itemized bill
(or a rejection reason) for each one, prints a daily summary, and writes
the full report to `sales_summary.txt`.

## Business rules, in case you want to tweak them

All defined as constants at the top of `food_delivery.py`:

- **Discount tiers** (`DISCOUNT_TIERS`): 5% off ≥ ₹300, 10% off ≥ ₹500,
  15% off ≥ ₹1000 — based on the pre-discount subtotal, best tier wins.
- **Delivery charge** (`DELIVERY_CHARGE`, `FREE_DELIVERY_THRESHOLD`): flat
  ₹40, waived on subtotals ≥ ₹500.
- **Menu** (`MENU`): 6 items, edit directly in the script or point
  `load_sample_orders` at your own catalog.

See `obstacle_log.md` for the reasoning behind these choices and a few bugs
that came up while building it — including one around partially-invalid
orders and one around which total the "highest value" order should
actually be sorted by.

## Push to GitHub

```bash
git init
git add .
git commit -m "Food delivery order processor"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
