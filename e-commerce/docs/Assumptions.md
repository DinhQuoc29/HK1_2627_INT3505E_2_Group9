# Marketplace requirements

## Assumptions (ASM)

An assumption is a condition the marketplace relies on about its users, business practices, or operating environment. The following assumptions are proposed for validation with the project team. The IDs in the last column refer to [Marketplace use cases](Use_Cases.md). V1 assumptions continue to apply in V2 unless the team revises them.

### V1 — Marketplace and recommendations

| ID | Assumption | Related use cases |
| --- | --- | --- |
| ASM-01 | A buyer signing in through Google controls the Google account they select. This sign-in path depends on Google's identity service being reachable. | B01 |
| ASM-02 | The marketplace operator can identify which people may administer the marketplace and which shop a seller is authorized to manage. This information is available before those users manage listings, orders, or categories. | S01, S02, S03, A01 |
| ASM-03 | Sellers know the products they offer and can supply representative photos, accurate descriptions, prices, and shop locations. Brand-based discovery depends on sellers supplying brand information where applicable. | B02, B03, S01, S02 |
| ASM-04 | A listing represents an offer from one shop, even when another shop sells the same product. That shop is responsible for the units ordered from its listing. | B05, B06, B07, S01, S03 |
| ASM-05 | Sellers can determine how many units are available to marketplace buyers and report changes caused outside the platform, such as damaged stock or an in-store sale. Physical availability depends on the accuracy and timeliness of those reports. | B02, B03, B05, B06, S01, S02 |
| ASM-06 | For V1, sellers quote prices and buyers express budgets in one marketplace currency. A buyer's stated recommendation budget is the maximum price for one item. | B03, B05, B06 |
| ASM-07 | A signed-in account represents one shopper for personalization purposes. Its saved preference applies when that shopper uses the account on another device. People sharing an account are assumed to share that preference. | B01, B03, B04 |
| ASM-08 | V1 purchases use simulated money. Buyers and sellers can complete the purchase workflow without a bank transfer, card charge, or payout to the shop. | B06, B07, S03 |
| ASM-09 | The team can agree on which order statuses permit cancellation and when canceled units are available for resale. The use cases leave the exact cancellation cutoff open. | B07, S03 |
| ASM-10 | Sellers handle physical dispatch and can report fulfillment milestones accurately. Buyer-visible tracking therefore depends on the seller knowing and reporting the current status. | B07, S03 |
| ASM-11 | A marketplace administrator can define a category hierarchy and decide where a new category belongs. Sellers can identify an appropriate category for the products they list. | A01, S01, B02 |
| ASM-16 | The team can collect representative shopper queries and independently judge how relevant candidate listings are to each query. These judgments are available for evaluating search before sufficient shopper activity exists. | B02 |

### V2 — Shopping assistant, reviews, and moderation

| ID | Assumption | Related use cases |
| --- | --- | --- |
| ASM-12 | A shopper may describe a need in everyday language and clarify it when asked. Whether a recommendation can be explained depends on the relevant facts being present in the seller's catalog data. | B08 |
| ASM-13 | The team can define when a purchase counts as completed, and the person reporting fulfillment has enough information to distinguish dispatch from completion. Review eligibility relies on that distinction. | S03, B10 |
| ASM-14 | Buyers contribute ratings voluntarily. Some products may have no published ratings, so the team must account for unrated products when defining rating-based discovery. | B09, B10 |
| ASM-15 | Administrators have agreed moderation criteria and a source of reports or flags that identifies the review or listing in question. The use cases leave the reporting channel open. | A02, A03 |
