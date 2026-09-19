"""
Food Delivery Order Processor
--------------------------------
Processes a batch of food orders against a menu, applies value-based
discounts and delivery charges, flags invalid orders without crashing,
finds the highest-value order and writes a sales summary to a file.

Standard library only, no external packages or frameworks.

Run it with:
    python3 food_delivery.py
"""

import json
import os
from datetime import datetime

# --------------------------------------------------------------------------
# Step 1: Menu and sample orders
# --------------------------------------------------------------------------
#
# `MENU` is a dict of {item_name: price}. Using a dict (rather than a list
# of item dicts) makes item lookups O(1) which matters once we're
# validating every line of every order against it.
#
# Each order is a dict:
#   {
#       "order_id": int,
#       "customer": str,
#       "items": [{"item": str, "quantity": int}, ...]
#   }
#
# A couple of the sample orders are deliberately broken (an empty order, an
# order naming a dish that isn't on the menu) so Step 3's error handling has
# something real to catch.

MENU = {
    "Margherita Pizza": 250.0,
    "Veggie Burger": 150.0,
    "Chicken Biryani": 220.0,
    "Caesar Salad": 180.0,
    "Cold Coffee": 90.0,
    "Garlic Bread": 100.0,
}

SAMPLE_ORDERS_FILE = "sample_orders.json"
SUMMARY_OUTPUT_FILE = "sales_summary.txt"

# Discount tiers, highest threshold first: (minimum subtotal, discount %)
DISCOUNT_TIERS = [
    (1000.0, 0.15),
    (500.0, 0.10),
    (300.0, 0.05),
]

DELIVERY_CHARGE = 40.0
FREE_DELIVERY_THRESHOLD = 500.0


def load_sample_orders(filepath=SAMPLE_ORDERS_FILE):
    """Load the sample order batch from a JSON file."""
    if not os.path.exists(filepath):
        print(f"[warning] '{filepath}' not found — no orders to process.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------
# Step 2: Core functions — totals, discounts, delivery
# --------------------------------------------------------------------------

def calculate_subtotal(items, menu):
    """Sum the price × quantity for each valid item in an order.

    Returns (subtotal, valid_lines, invalid_lines) rather than raising on
    a bad item name, so one typo doesn't take down the whole order — the
    caller decides what to do with the invalid lines.
    """
    subtotal = 0.0
    valid_lines = []
    invalid_lines = []

    for line in items:
        name = line.get("item", "").strip()
        quantity = line.get("quantity", 0)

        if name not in menu:
            invalid_lines.append(f"'{name}' is not on the menu")
            continue

        if not isinstance(quantity, int) or quantity <= 0:
            invalid_lines.append(f"'{name}' has an invalid quantity ({quantity})")
            continue

        line_total = menu[name] * quantity
        subtotal += line_total
        valid_lines.append({
            "item": name,
            "quantity": quantity,
            "unit_price": menu[name],
            "line_total": line_total,
        })

    return subtotal, valid_lines, invalid_lines


def apply_discount(subtotal):
    """Return (discount_rate, discount_amount) for a given subtotal.
    Checks tiers highest-first so an order only gets the best tier it
    qualifies for, not the first one that happens to match."""
    for threshold, rate in DISCOUNT_TIERS:
        if subtotal >= threshold:
            return rate, round(subtotal * rate, 2)
    return 0.0, 0.0


def calculate_delivery_charge(subtotal):
    """Flat delivery fee, waived above the free-delivery threshold."""
    if subtotal >= FREE_DELIVERY_THRESHOLD:
        return 0.0
    return DELIVERY_CHARGE


# --------------------------------------------------------------------------
# Step 3: Processing a single order — invalid items and empty orders
# --------------------------------------------------------------------------

def process_order(order, menu):
    """Process one order into a full bill.

    Returns a dict either way — never raises and never crashes the batch —
    with a 'valid' flag so the caller can tell a real bill from a rejected
    order, and 'warnings' explaining exactly what went wrong.
    """
    order_id = order.get("order_id")
    customer = order.get("customer", "Unknown")
    items = order.get("items", [])

    result = {
        "order_id": order_id,
        "customer": customer,
        "valid": False,
        "warnings": [],
        "subtotal": 0.0,
        "discount_rate": 0.0,
        "discount_amount": 0.0,
        "delivery_charge": 0.0,
        "final_total": 0.0,
        "valid_lines": [],
    }

    if not items:
        result["warnings"].append("Order has no items — nothing to bill.")
        return result

    subtotal, valid_lines, invalid_lines = calculate_subtotal(items, menu)
    result["valid_lines"] = valid_lines
    result["warnings"].extend(invalid_lines)

    if not valid_lines:
        result["warnings"].append("No valid menu items in this order — order rejected.")
        return result

    discount_rate, discount_amount = apply_discount(subtotal)
    delivery_charge = calculate_delivery_charge(subtotal)
    final_total = round(subtotal - discount_amount + delivery_charge, 2)

    result.update({
        "valid": True,
        "subtotal": round(subtotal, 2),
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "delivery_charge": delivery_charge,
        "final_total": final_total,
    })
    return result


def process_all_orders(orders, menu):
    """Process a full batch. Returns (billed_orders, rejected_orders) —
    invalid orders are reported, never silently dropped."""
    billed_orders = []
    rejected_orders = []

    for order in orders:
        bill = process_order(order, menu)
        if bill["valid"]:
            billed_orders.append(bill)
        else:
            rejected_orders.append(bill)

    return billed_orders, rejected_orders


# --------------------------------------------------------------------------
# Step 4: Highest-value order
# --------------------------------------------------------------------------

def find_highest_value_order(billed_orders):
    """Return the bill dict with the highest final_total, or None if
    nothing was billed."""
    if not billed_orders:
        return None
    return max(billed_orders, key=lambda bill: bill["final_total"])


# --------------------------------------------------------------------------
# Step 5: Sales summary written to a file
# --------------------------------------------------------------------------

def build_sales_summary(billed_orders, rejected_orders):
    """Aggregate the day's numbers into a summary dict."""
    total_revenue = round(sum(bill["final_total"] for bill in billed_orders), 2)
    highest = find_highest_value_order(billed_orders)

    return {
        "total_orders_received": len(billed_orders) + len(rejected_orders),
        "valid_orders": len(billed_orders),
        "rejected_orders": len(rejected_orders),
        "total_revenue": total_revenue,
        "highest_value_order": highest,
    }


def write_sales_report(summary, billed_orders, rejected_orders, filepath=SUMMARY_OUTPUT_FILE):
    """Write the full daily sales report — summary, per-order bills, and
    rejected orders — to a text file."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("FOOD DELIVERY — DAILY SALES SUMMARY\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Total orders received: {summary['total_orders_received']}\n")
        f.write(f"Valid orders billed:   {summary['valid_orders']}\n")
        f.write(f"Rejected orders:       {summary['rejected_orders']}\n")
        f.write(f"Total revenue:         ₹{summary['total_revenue']:.2f}\n\n")

        highest = summary["highest_value_order"]
        if highest:
            f.write("HIGHEST-VALUE ORDER\n")
            f.write("-" * 60 + "\n")
            f.write(f"Order ID:        {highest['order_id']}\n")
            f.write(f"Customer:        {highest['customer']}\n")
            f.write(f"Subtotal:        ₹{highest['subtotal']:.2f}\n")
            f.write(f"Discount:        {int(highest['discount_rate']*100)}% "
                     f"(-₹{highest['discount_amount']:.2f})\n")
            f.write(f"Delivery charge: ₹{highest['delivery_charge']:.2f}\n")
            f.write(f"Final total:     ₹{highest['final_total']:.2f}\n")
        else:
            f.write("No valid orders were billed today.\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("ALL BILLED ORDERS\n")
        f.write("=" * 60 + "\n\n")

        for bill in billed_orders:
            f.write(f"Order #{bill['order_id']} — {bill['customer']}\n")
            for line in bill["valid_lines"]:
                f.write(f"    {line['quantity']} x {line['item']} "
                         f"@ ₹{line['unit_price']:.2f} = ₹{line['line_total']:.2f}\n")
            f.write(f"    Subtotal:        ₹{bill['subtotal']:.2f}\n")
            f.write(f"    Discount ({int(bill['discount_rate']*100)}%):   "
                     f"-₹{bill['discount_amount']:.2f}\n")
            f.write(f"    Delivery charge: ₹{bill['delivery_charge']:.2f}\n")
            f.write(f"    FINAL TOTAL:     ₹{bill['final_total']:.2f}\n")
            if bill["warnings"]:
                for w in bill["warnings"]:
                    f.write(f"    [note] {w}\n")
            f.write("-" * 60 + "\n")

        if rejected_orders:
            f.write("\n" + "=" * 60 + "\n")
            f.write("REJECTED ORDERS\n")
            f.write("=" * 60 + "\n\n")
            for bill in rejected_orders:
                f.write(f"Order #{bill['order_id']} — {bill['customer']}\n")
                for w in bill["warnings"]:
                    f.write(f"    [rejected] {w}\n")
                f.write("-" * 60 + "\n")

    print(f"[saved] Sales report written to '{filepath}'.")


# --------------------------------------------------------------------------
# Console output helpers
# --------------------------------------------------------------------------

def print_bill(bill):
    print(f"\nOrder #{bill['order_id']} — {bill['customer']}")
    if not bill["valid"]:
        for w in bill["warnings"]:
            print(f"  ✘ {w}")
        return
    for line in bill["valid_lines"]:
        print(f"  {line['quantity']} x {line['item']} @ ₹{line['unit_price']:.2f} "
              f"= ₹{line['line_total']:.2f}")
    print(f"  Subtotal:        ₹{bill['subtotal']:.2f}")
    print(f"  Discount ({int(bill['discount_rate']*100)}%):   -₹{bill['discount_amount']:.2f}")
    print(f"  Delivery charge: ₹{bill['delivery_charge']:.2f}")
    print(f"  FINAL TOTAL:     ₹{bill['final_total']:.2f}")
    for w in bill["warnings"]:
        print(f"  [note] {w}")


def run():
    orders = load_sample_orders()
    print(f"Loaded {len(orders)} orders. Processing...\n")
    print("=" * 60)

    billed_orders, rejected_orders = process_all_orders(orders, MENU)

    for bill in billed_orders:
        print_bill(bill)
    for bill in rejected_orders:
        print_bill(bill)

    summary = build_sales_summary(billed_orders, rejected_orders)

    print("\n" + "=" * 60)
    print("DAILY SALES SUMMARY")
    print("=" * 60)
    print(f"Total orders received: {summary['total_orders_received']}")
    print(f"Valid orders billed:   {summary['valid_orders']}")
    print(f"Rejected orders:       {summary['rejected_orders']}")
    print(f"Total revenue:         ₹{summary['total_revenue']:.2f}")

    highest = summary["highest_value_order"]
    if highest:
        print(f"\nHighest-value order: #{highest['order_id']} — {highest['customer']} "
              f"(₹{highest['final_total']:.2f})")

    write_sales_report(summary, billed_orders, rejected_orders)


if __name__ == "__main__":
    run()
