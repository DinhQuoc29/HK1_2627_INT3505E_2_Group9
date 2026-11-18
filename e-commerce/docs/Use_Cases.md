# Marketplace use cases

**Proposed release scope.** V1 lets a buyer complete a multi-shop purchase, a seller fulfill it, and an admin maintain the catalog. It includes search and budget-aware recommendations so the team can demonstrate product discovery end to end. V2 adds conversational shopping, reviews, and the features that depend on reviews. Release labels describe planned capabilities.

Product discovery includes ranked search, homepage suggestions, similar products, and conversational advice. Release commitments are recorded in the [functional requirements](Requirements.md). Each use case names an actor's goal. Its workflow describes how the actor reaches that goal. All signed-in roles can log out to end their session. Seller actions are limited to the seller's shop, buyer order actions to the buyer's own purchases, and admin actions require admin permission.

## Buyer

### V1 — First release

| ID | Use case | Main flow and outcome |
| --- | --- | --- |
| B01 | Access my account | Register with email and password, then sign in. A returning buyer can also sign in with Google and open their account. |
| B02 | Find and inspect a product | Browse the category tree or search by name across the marketplace or within one category. Apply price, brand, or seller province filters, inspect matching listings ordered by relevance to the query, then open a listing to see its photos, price, seller, and availability. |
| B03 | Discover products within my budget | Enter a maximum price per item and browse suggestions on the home page, or open a listing to see similar products. New shoppers can browse popular products. If ranking fails or times out, the system offers popular alternatives. Every result must be on sale, in stock, and within any supplied budget. If few qualify, the buyer sees fewer results. |
| B04 | Control personalization | Read the tracking notice and switch personalization off in account settings. The system stops collecting events for personalization and using the buyer's history for suggestions. The buyer can still shop and browse popular products. |
| B05 | Prepare a multi-shop cart | While signed in, add products from different shops, change quantities, or remove items. Review the current prices and items grouped by shop. |
| B06 | Place and pay for a purchase | Confirm the cart once. The system rechecks prices and stock, creates one order per shop, and shows one simulated payment with an amount allocated to each order. A price change requires confirmation. Insufficient stock rolls back the whole checkout, and retrying the same confirmation cannot duplicate the purchase or payment. |
| B07 | Track or cancel a shop order | Open purchase history to see each shop's order and status. Cancel an eligible order to restore its stock once and adjust its simulated payment allocation. Other shops' orders continue independently. |

### V2 — Deferred

| ID | Use case | Main flow and outcome |
| --- | --- | --- |
| B08 | Ask the shopping assistant for advice | Describe a need and budget in chat, answer a clarifying question if needed, and open a suggested product. The assistant uses the V1 recommendation engine and explains matches using catalog details. |
| B09 | Choose products using customer reviews | Read published reviews and the aggregate rating on a product page, or filter search results by rating. This ships alongside review submission so the filter has real data. |
| B10 | Review a completed purchase | Select an item from a completed order, submit a rating and review, and edit or remove it later. Only the purchaser can submit a review for that order item, once. |

## Seller

### V1 — First release

| ID | Use case | Main flow and outcome |
| --- | --- | --- |
| S01 | Publish a listing | Sign in as a seller, enter the product's details, category, photos, price, and stock, then publish it. Buyers can find the listing and purchase available units. |
| S02 | Maintain a listing | Open a product in the shop, update its details, price, or stock, or stop selling it. New purchases use the updated listing. Existing orders retain the purchased name and price. |
| S03 | Fulfill a shop order | Open an incoming order, review its items, prepare the package, and update the delivery status after dispatch. The buyer sees the updated status for that shop's order. |

### V2 — Deferred

The three identified seller workflows are all in V1. The current requirements specify no additional seller-facing goal for V2.

## Admin

### V1 — First release

| ID | Use case | Main flow and outcome |
| --- | --- | --- |
| A01 | Manage product categories | Create or rename a category, assign its parent where appropriate, and save the tree. Sellers can classify products and buyers can browse the updated categories. |

### V2 — Deferred

| ID | Use case | Main flow and outcome |
| --- | --- | --- |
| A02 | Moderate customer reviews | Inspect a reported review and its product context. Keep it or remove it, then verify that the storefront's reviews and aggregate rating reflect the decision. Release this with B09 and B10. |
| A03 | Moderate a product listing | Inspect a flagged listing and decide whether it may remain on sale. If withdrawn, it becomes unavailable for new purchases while past orders retain their item details. This is a proposed extension from the workflow discussion. |
