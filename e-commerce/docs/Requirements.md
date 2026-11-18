# Marketplace requirements

Each requirement describes an observable outcome. Use-case IDs refer to [Use Cases](Use_Cases.md) and assumption IDs refer to [Assumptions](Assumptions.md). V2 adds to the V1 requirements.

## V1 — First release

### Accounts and catalog

| ID | Requirement | Use cases | Assumptions |
| --- | --- | --- | --- |
| REQ-01 | Buyers shall be able to register and sign in with email and password. Returning buyers shall also be able to access their account using Google sign-in. | B01 | ASM-01 |
| REQ-02 | All signed-in users shall be able to log out. After logout, the ended session shall no longer grant access to account actions. | B01, S01, A01 | — |
| REQ-03 | Buyers shall have access only to their own carts and orders. Sellers shall manage listings and fulfill orders only for their authorized shops. Only authorized admins shall perform administrative actions. | B05–B07, S01–S03, A01 | ASM-02, ASM-04 |
| REQ-04 | Admins shall be able to create and rename categories and assign parent categories. The resulting hierarchy shall be available for seller classification and buyer browsing. | A01, S01, B02 | ASM-11 |
| REQ-05 | Sellers shall be able to publish listings with a name, description, category, photos, price, and stock quantity, and later update those details or stop selling the listing. | S01, S02 | ASM-03–05, ASM-11 |
| REQ-06 | Buyers shall be able to browse the category tree, search by product name across the marketplace or within a selected category, and filter by price, brand, or seller province. Search shall return matching listings ordered by query relevance and retain all selected filters when ML ranking is unavailable. The team shall establish a rule-based baseline first and evaluate ML against it on the same held-out queries and candidates. | B02 | ASM-03, ASM-11, ASM-16 |
| REQ-07 | Buyers shall be able to open a published listing and view its photos, current price, seller, and availability. A withdrawn listing shall be unavailable for new purchases. | B02, S01, S02 | ASM-03–05 |

### Recommendations and privacy

| ID | Requirement | Use cases | Assumptions |
| --- | --- | --- | --- |
| REQ-08 | Buyers shall receive suggestions on the home page and be able to discover similar products from a listing. Popular products shall be available to new shoppers and as a fallback when ranking fails or times out. | B03 | ASM-03, ASM-07 |
| REQ-09 | Buyers shall be able to supply a maximum price per item. Every recommendation, including a fallback, shall be on sale, in stock, and priced at or below any supplied maximum when suggested. If too few items qualify, the marketplace shall return only those that qualify. | B03 | ASM-05, ASM-06 |
| REQ-10 | Buyers shall be able to read a tracking notice and turn personalization off for their account. While it is off, the marketplace shall stop collecting events for personalization and stop using the buyer's history for suggestions across signed-in devices. Shopping and popular products shall remain available. | B03, B04 | ASM-07 |

### Cart, checkout, and fulfillment

| ID | Requirement | Use cases | Assumptions |
| --- | --- | --- | --- |
| REQ-11 | A signed-in buyer shall be able to add items from multiple shops to one cart, change quantities, remove items, and see the remaining items grouped by shop with current prices. | B05 | ASM-04, ASM-06 |
| REQ-12 | Checkout shall recheck prices and availability for every item. If a price changed since the buyer reviewed it, the buyer shall see the revised price and confirm it before the purchase proceeds. | B06 | ASM-03, ASM-05, ASM-06 |
| REQ-13 | One successful checkout shall create one order per represented shop and deduct the quantities purchased. If any item is unavailable or has insufficient stock, the whole checkout shall fail with no order, payment, or stock deduction. Concurrent purchases shall never sell more units than are available. | B06 | ASM-04, ASM-05 |
| REQ-14 | A successful purchase shall show one simulated payment with an amount allocated to each shop order. The allocations shall sum to the payment total. Repeating the same checkout confirmation shall produce no additional order, payment, or stock deduction. | B06 | ASM-04, ASM-06, ASM-08 |
| REQ-15 | Each order item shall retain its purchased name and price when a seller later edits or withdraws the listing. | B07, S02 | ASM-03, ASM-04 |
| REQ-16 | Sellers shall be able to view the items in incoming shop orders and update delivery status after dispatch. Buyers shall be able to see each shop order and its current status in purchase history. | B07, S03 | ASM-04, ASM-10 |
| REQ-17 | Buyers shall be able to cancel an eligible shop order independently. Cancellation shall restore its stock once and adjust its simulated payment allocation once, including on retry. Other shop orders shall retain their status, stock deductions, and allocations. An ineligible cancellation shall leave the purchase unchanged. | B07 | ASM-04, ASM-08, ASM-09 |

## V2 — Deferred

| ID | Requirement | Use cases | Assumptions |
| --- | --- | --- | --- |
| REQ-18 | Buyers shall be able to describe a need and budget in chat and answer clarifying questions when needed. The assistant shall use the V1 recommendation engine, explain matches using catalog facts, and let the buyer open each suggested listing. REQ-09 applies to every suggestion. | B08 | ASM-03, ASM-06, ASM-12 |
| REQ-19 | Only the purchaser of an item from a completed order shall be able to submit a rating and review for that order item, once. The purchaser shall be able to edit or remove their review. | B10 | ASM-13 |
| REQ-20 | Buyers shall be able to read published reviews and the aggregate rating on the product page and filter search results by rating. The aggregate shall reflect the currently published ratings, including after edits or removals. | B09, B10, A02 | ASM-14 |
| REQ-21 | Admins shall be able to inspect a reported review alongside its product, then retain or remove the review. A removed review shall disappear from public reviews and cease contributing to the aggregate rating. | A02 | ASM-14, ASM-15 |
| REQ-22 | Admins shall be able to inspect a flagged listing and retain or withdraw it. Withdrawal shall prevent new purchases while preserving the item details in existing orders. | A03 | ASM-04, ASM-15 |

**Open business rules.** The team still needs to define the cancellation cutoff for REQ-17, when an order counts as completed for REQ-19, and how rating filters treat unrated products for REQ-20.
