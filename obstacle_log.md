# Obstacle Log — Food Delivery Order Processor

Notes on the issues I ran into while building this, and how I worked through them.

## 1. What to do with an order that's *partly* invalid

The brief says to handle invalid menu items gracefully, but it doesn't say
whether one bad line item should sink the whole order. My first version
rejected the entire order the moment it hit an unrecognized item name —
which felt too harsh: Order #7 (Devika) ordered 2 valid burgers and 1 item
that doesn't exist ("Mango Lassi"). Throwing away the whole order loses two
perfectly billable items over one typo.

**Fix:** `calculate_subtotal()` returns three things — the running subtotal,
the valid line items, and a list of invalid-item warnings — instead of
stopping at the first bad line. `process_order()` then only rejects the
*whole* order if there are zero valid items left (see Order #11, where
every item was invalid). Otherwise it bills what's valid and attaches the
warnings to the bill so the customer still sees what got dropped and why.

## 2. Discount tiers stacking instead of picking the best one

My first pass at `apply_discount()` checked tiers from lowest to highest
threshold and didn't stop at the first match — so an order over ₹1000 was
briefly getting the 5% tier's discount amount because the loop kept
overwriting the result as it worked upward.

**Fix:** listed `DISCOUNT_TIERS` highest-threshold-first and `return`
immediately on the first (best) match, rather than falling through and
recalculating. Also wrote the tiers as a list of `(threshold, rate)` tuples
instead of a chain of `if/elif` statements, so adding a new tier later is a
one-line change instead of restructuring conditionals.

## 3. Free delivery threshold vs. discount threshold — using the wrong number

I originally applied the free-delivery check to the *discounted* total
rather than the subtotal. That created a strange edge case: an order that
was exactly at the free-delivery line before the discount would drop below
it after the discount was subtracted, and lose free delivery it should have
kept — which felt backwards from a customer's perspective (a bigger order
getting penalized after already earning a discount).

**Fix:** both `apply_discount()` and `calculate_delivery_charge()` are
computed against the same `subtotal` value, before either adjustment is
applied to the running total. Keeping both checks anchored to one
unambiguous number made the final total calculation easier to reason about
and to test by hand.

## 4. Empty orders vs. orders with only invalid items

These looked like the same bug at first ("no billable items"), but they
needed different messages to actually be useful. An empty `items: []` list
usually means something upstream never attached items to the order. An
order with items that are all invalid usually means a typo or a
discontinued menu item. Collapsing both into one generic "invalid order"
message would have made debugging real data harder.

**Fix:** `process_order()` checks for an empty `items` list first with its
own specific message ("Order has no items — nothing to bill"), and only
falls through to the "no valid items" check after `calculate_subtotal()`
has actually tried to match every line against the menu.

## 5. Finding the highest-value order after discounts, not before

Early on I sorted orders by `subtotal` to find the "highest-value" order,
which is wrong — two orders with the same subtotal can end up with
different final totals depending on which discount tier and delivery
charge apply. The customer-facing "value" of an order is what they end up
paying, not the pre-discount total.

**Fix:** `find_highest_value_order()` sorts by `final_total`, computed
after both the discount and the delivery charge are applied — the number
that actually appears on the bill.
