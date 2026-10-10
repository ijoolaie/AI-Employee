# AI Employee World — Economy & Room Progression Design

**Status:** Approved product direction; implementation not yet started
**Branch:** `feat/world-3d-office`
**Scope:** First playable company-world slice, room unlocks, employee placement, upgrades, and hybrid economy
**Decision:** Hybrid economy — virtual currency plus real-money purchases; real-money currency is intentionally undecided.

## Product promise

The customer enters World Mode as the CEO avatar in one private executive office. They can walk around the room, inspect nearby doors, and expand the company one room at a time. The world is a playable management interface over the existing AI Employee platform; it must not invent business execution, employee status, or payment success in the client.

## First playable slice

1. **CEO office (unlocked by default):** one-person office, player avatar, desk, chair, computer, door and a simple interaction prompt. No employee hire is required for the CEO avatar.
2. **One adjacent locked room:** the only purchasable room visible in the first slice. Approaching its door opens a contextual panel showing the room name, one-month room access, one employee slot, included starter equipment, price, and purchase options.
3. **Hire flow:** after choosing a payment method, the customer selects an eligible employee profile/role and confirms. The server validates the room offer, price, tenant, available capacity and employee selection.
4. **Activation:** the room and hire become active only after the authoritative purchase state is confirmed. For real money, that means a verified provider event or a provider status check—not a browser redirect, success toast, or client callback alone. For virtual currency, the server atomically debits the balance and records the purchase.
5. **Arrival scene:** after activation, the selected employee appears in the room with starter desk, chair, computer and role-appropriate essentials. Personality/job-description-derived decor is presentation metadata; it must not grant permissions or silently change the employee's actual capabilities.
6. **Upgrades:** offer optional desk/chair/monitor/equipment/decor tiers for that employee's workspace. Purchases change the authoritative room inventory after payment confirmation. Higher prices and item availability come from the server catalogue.
7. **Expansion:** further rooms (meeting room, restroom, cafeteria, community/assembly hall, gym, engineering/sales/customer-care rooms, etc.) remain locked until their server-defined unlock conditions are met. Do not render all rooms as purchasable in the initial slice.

## Hybrid economy rules

- Support two payment rails: (A) non-cash virtual currency earned through product-defined progression and (B) real-money checkout. The user has not selected a real-money currency or payment provider for World purchases yet.
- Do not hardcode currency symbols, exchange rates, or a USD/Toman assumption. Money amounts are server-side integer minor units paired with an explicit ISO currency code once the business decision is made. Display formatting is client-side only.
- Virtual currency is not cash, is not withdrawable, and cannot be transferred between tenants unless a separate reviewed product decision explicitly adds those features.
- Catalogue offers define whether an item supports virtual currency, real money, or both. The server decides the actual amount payable and accepted rail; never trust client-supplied prices or discount amounts.
- Keep World purchases separate from the existing SaaS subscription plan checkout. Existing Stripe billing handles plan subscriptions; do not repurpose its subscription checkout endpoint as a one-off room or furniture purchase.
- For real-money purchases, integrate through a provider-neutral one-time-purchase service and a provider adapter. Provider webhook signatures, event idempotency, amount/currency/merchant-reference matching and tenant ownership must be checked before fulfilling an order.
- A redirect to a success page is not proof of payment. Pending, failed, canceled, disputed and refunded purchases must be represented explicitly. Refund/reversal policy and chargeback handling must be decided before production launch.
- Monthly room access needs an explicit expiry and renewal policy. On expiry or failed renewal, do not delete employee records, work history or purchased inventory. Mark the room as expired/restricted and show a clear renewal path; employee suspension/reassignment behavior requires a separate product rule before being automated.

## Server-authoritative domain model (proposed)

- **WorldRoomDefinition:** stable room type, display metadata, capacity, catalogue offer, prerequisites and starter-kit template.
- **TenantWorldRoom:** tenant, room definition, status, lease start/end, activation source, and optimistic concurrency/version fields.
- **WorldCatalogueItem:** stable item code, category, compatible roles/rooms, upgrade tier, display metadata and server-owned prices/accepted payment rails.
- **WorldRoomInventory:** tenant room, item code, quantity, placement metadata and purchase/order reference.
- **WorldOrder:** tenant, order status, immutable quote snapshot, chosen rail, currency/amount where applicable, idempotency key, provider reference, and timestamps.
- **WorldWallet / WorldWalletEntry:** tenant-scoped virtual balance represented by an append-only ledger. Never mutate a balance without a corresponding ledger entry; use a transaction/locking strategy to prevent double-spend.
- **WorldPurchaseEvent / audit event:** idempotent record of provider callbacks and fulfillment decisions.
- **Employee placement link:** room assignment references the real employee record. Do not create a fake operational employee solely for rendering. The CEO avatar is a distinct player-controlled avatar, not an employee row.

These are proposed names, not existing database models. Confirm naming and relationships against the current ORM before adding migrations.

## Required API behavior

Expected API surface (names are proposals, not committed contracts):

- Read World state, visible rooms, catalogue offers and the current tenant wallet.
- Create a server-priced quote/order for a room lease, hire package, or upgrade.
- For virtual currency: atomically validate and debit wallet, record order/ledger entries, then fulfill once.
- For real money: create a provider checkout session for the immutable order amount and metadata; return only a checkout URL/order ID. Keep the order pending until verified provider confirmation.
- Receive signed provider webhook events and process them idempotently. Reject invalid signatures, amount/currency mismatches, duplicate fulfillment and cross-tenant references.
- Read order status and authoritative World state so the frontend can poll/reconcile after redirect or network failure.
- All routes require authenticated tenant context and server-side authorization. Never accept tenant ID, employee ownership, balance, price or fulfilled status as client authority.

## UX requirements

- A contextual “near door” prompt appears only when the player avatar is within interaction range; keyboard/controller and touch interaction must both be supported.
- The first room prompt is clear about one-month duration, included one employee, starter equipment, total price/payment rails, and renewal/expiry behavior.
- Employee selection shows role, task description and personality/style options. Keep the employee's operational permissions governed by the existing employee/workforce backend.
- During payment, show pending state and prevent duplicate submits. After checkout, reconcile against server state; if the webhook is delayed, say “Payment is being confirmed” rather than unlocking optimistically.
- Full-screen World Mode must continue to work with the room prompt, close/escape behavior and accessible focus handling.
- Keep motion/lighting responsive and respect reduced-motion settings; don't introduce expensive always-on animations.

## Acceptance criteria for the first slice

1. A new tenant sees only the CEO office active and one adjacent room locked.
2. The CEO avatar can move around the office and interact with the adjacent door.
3. The door panel shows a server-provided quote and a single-month/one-employee offer.
4. The customer can select an existing eligible employee (or complete the existing employee-creation workflow); no fake employee is silently inserted.
5. A virtual-currency purchase is atomic, tenant-scoped, ledger-backed and safe against duplicate requests/double-spend.
6. A real-money order remains pending until verified provider confirmation; canceled, failed or unsigned events never unlock the room.
7. Replaying a successful webhook does not double-charge, double-debit or duplicate room/hire/inventory fulfillment.
8. The selected employee appears in the room with a deterministic starter kit appropriate to the selected role.
9. An upgrade appears only after its order is fulfilled and is persisted in server state.
10. Expired room access never deletes the employee, work history or purchased inventory.
11. Unit/API/integration tests cover tenant isolation, price tampering, idempotency, concurrent virtual debits, webhook verification, amount/currency mismatch, canceled/failed payment and expiry.
12. Existing World read model, billing subscriptions and governed employee execution remain unchanged unless a separately reviewed integration contract requires a change.

## Delivery sequence

- **W0 — World movement and CEO avatar:** implement player-controlled avatar movement and collision/bounds within the initial room; keep CEO identity separate from workforce employees.
- **W1 — Room primitives:** add one adjacent locked room, proximity interaction and responsive contextual panel; other facilities remain future catalogue definitions.
- **W2 — Virtual wallet and first room order:** database migration, append-only ledger, atomic debit, tenant-scoped order fulfillment and tests.
- **W3 — Employee selection and starter kit:** link an existing/created real employee to the room and persist role-based starter inventory.
- **W4 — Real-money one-time checkout:** choose provider/currency, implement dedicated one-time order checkout/webhook adapter, and verify test-mode lifecycle. Reuse security patterns from existing billing code, not its subscription checkout contract.
- **W5 — Upgrades and monthly lease lifecycle:** catalogue tiers, lease renewal/expiry, idempotent fulfillment and customer messaging.
- **W6 — Other facilities:** meeting room, restroom, cafeteria, assembly hall, gym and role-specific rooms gated by server-defined prerequisites.

## Explicitly out of scope until separately approved

- Choosing the real-money currency or payment provider for World purchases.
- Enabling live charges or setting production prices.
- Crypto, cash-out, peer-to-peer transfer, loot boxes or random paid rewards.
- Changing SaaS plan entitlements or treating game room leases as subscription-plan upgrades.
- Automatically firing, deleting or permanently disabling a real employee because a room lease expires.
- Marking PR #983 ready or merging it without explicit user approval.

## Current implementation status

This document records the selected product direction and security boundaries. It does **not** claim that wallet, World orders, room leases, player movement, one-time World checkout or fulfillment APIs have been implemented. Existing Stripe subscription billing is present in the repository, but it is not proof that World one-time purchases are implemented or externally certified.
