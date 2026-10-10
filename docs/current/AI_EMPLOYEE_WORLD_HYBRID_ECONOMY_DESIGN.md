# AI Employee World — Economy & Room Progression Design

**Status:** Approved product direction; front-end prototype plus initial backend commerce foundation underway
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

Implemented on the feature branch: a procedural CEO avatar, bounded movement, one visually locked adjacent room, a proximity prompt and preview-only room offer, plus a front-end customization panel. The current customization selections are not account-persisted and do not yet reconfigure the 3D scene; premium options remain locked. The existing workforce visualization remains present, so this is not yet the final isolated one-room onboarding experience.

Backend foundation now includes a server-owned World catalogue, one-time order records distinct from SaaS subscriptions, per-currency price/provider configuration stored in catalogue data, tenant-scoped order APIs, payment-reference submission, vendor-scoped order review endpoints, separate approver and activator user IDs/username snapshots/timestamps, a commerce event timeline protected against UPDATE/DELETE, and persistent tenant feature entitlements granted only when an approved order is activated. Request schemas reject client-supplied price/tenant/verification fields, and order creation reads amount/provider eligibility from the server catalogue. The access-check endpoint grants catalogue-free items to tenants, recognizes vendor-included access without fabricating a purchase, and otherwise checks active tenant entitlements. The migration seeds separate World approval and activation permissions for existing owner/admin/tenant-admin roles; vendor list filtering checks review versus activation permissions separately. Database constraints prevent reuse of a provider transaction reference across orders, and concurrent idempotent order retries resolve to the existing tenant order rather than creating a duplicate.

Still not implemented: wallet balance/ledger and virtual-credit debit, real payment-provider adapters or provider verification/webhooks, production-ready currency/provider/network configuration (including the USDT network), seeded vendor RBAC permissions and support-session entitlements, lease expiration/renewal policy, room/furniture/employee placement fulfillment, and persistence/application of CEO/employee customization to the live scene. The entitlement record currently captures purchased item ownership but does not yet drive the 3D renderer or create room inventory. World Credit purchases are explicitly disabled until a wallet ledger exists. No real payments are processed by this implementation, and the frontend offer panel is still preview-only. Existing Stripe subscription billing is not reused for World one-time purchases.


## Additional approved product requirements — currencies, office/CEO customization, vendor support

### Customer-selected payment currency and multiple gateways

- The buyer must be able to choose among **Iranian rial (IRR), US dollar (USD), and Tether (USDT)** where that currency and at least one compatible payment provider are enabled for the buyer's market/account.
- Treat IRR, USD and USDT as distinct settlement rails, not interchangeable display labels. Never silently convert one into another or infer an exchange rate. If conversion is later offered, show the source amount, destination amount, rate, fee and quote expiry before confirmation.
- Build a provider-adapter registry so multiple gateways can be configured per supported currency. Each provider/currency pair has explicit enabled state, environment (test/live), merchant configuration reference, limits, fees where known, health status and priority/fallback policy. Do not expose secrets to the frontend or store credentials in the World catalogue.
- At checkout, show only providers that are currently enabled and compatible with the selected currency, order, region and account. The server validates the chosen provider/currency pair and freezes the payable quote into the order.
- Payment verification must be provider-specific and server-side. For fiat gateways, verify signed callbacks or query the provider's authoritative status API. For USDT, do not treat a screenshot, transaction hash supplied by the buyer, or a frontend callback as confirmation: define the supported network(s), token contract(s), confirmation/finality threshold, amount, destination wallet and transaction-replay protections before implementation. No chain/network is chosen by this requirement.
- Payment is not fulfilled merely because a user reports payment. The vendor's manual review/approval flow described below is an additional authorization step where required; it does not replace technical verification or override a failed, mismatched, refunded or otherwise invalid provider result.
- Before live implementation, decide legal/compliance, accounting, refund, chargeback, exchange-rate, USDT custody/wallet and supported-network policies. Until then, use test mode or manual approval records without moving real funds. No production prices or live provider credentials are defined here.

### CEO identity, avatar and office customization

- The player is the tenant's CEO/manager avatar, separate from the operational employee roster. On first entry, offer a customization step for both CEO **appearance/personality presentation** and the initial office.
- CEO customization includes safe baseline options such as name/display label, avatar body/style options, hair/skin/clothing palettes where supported, and presentation traits/personality descriptors. These are visual/product preferences only and must not alter authorization, billing privileges, real employee permissions, or AI execution policy.
- Provide several free default CEO looks/personality presets and office-layout templates. Premium/paid clothing, luxury appearance themes, expanded office layouts and premium furniture/decor can be offered through the server-owned catalogue.
- Let the user select an initial office layout before entering the world. Include a useful free starter layout and multiple purchasable larger/luxury layouts. Catalogue metadata must identify footprint, supported furniture anchors, accessibility/navigation constraints, included assets and price/payment rails. Do not let a client-supplied layout bypass room bounds, collision, entitlements or purchase checks.
- The office layout and purchased cosmetic inventory should persist to the tenant's World state and be recoverable across sessions/devices. A user may preview paid options, but the selected paid option is applied only after entitlement or confirmed purchase is established.
- At employee onboarding/room assignment, allow customization of the employee's supported appearance and personality presentation, with several free presets and paid special/luxury clothing and decor options. Store this as presentation metadata linked to the real employee. It must not rewrite job descriptions, alter permissions, change evaluation data or infer protected/sensitive traits.
- Separate the **visual personality preset** from the employee's actual configured personality, job description, memory, and execution configuration. Only an explicit authorized workflow can change operational employee settings.
- A vendor/support role may preview all catalogue options, including paid room templates, clothing and equipment, without charge for vendor-owned support/testing contexts. This vendor entitlement must not accidentally make the same items free for reseller or customer tenants.

### Vendor-assisted troubleshooting, payment approval and audit trail

- Provide a vendor-only support workflow allowing authorized vendor staff to inspect and troubleshoot every supported World feature for a reseller or customer, including premium layouts, avatar/employee cosmetics, rooms, furniture, equipment, and related feature flags.
- Resellers and customers remain subject to normal catalogue prices and entitlements. A vendor may grant or activate a paid feature for a reseller/customer only through a privileged, explicit support action with a recorded reason and an applicable authorization path (verified payment approval, documented complimentary grant, or another separately configured policy). Do not provide a hidden client-side bypass.
- For orders requiring manual payment approval, the **vendor** must explicitly review and approve the payment before the associated paid feature is activated. Record payment verification status separately from vendor approval status. Approval must not be possible for a provider-verified failure, amount/currency mismatch, duplicate/replayed transaction, refund, or other invalid state.
- Every approval and feature activation must create an append-only audit record with at least: tenant/customer/reseller ID; order/payment ID; feature and target entity; payment currency and amount; provider and provider transaction/reference ID when applicable; verification evidence/reference; decision (approved/rejected/revoked); reason/support ticket; timestamp; authenticated vendor user ID and displayed username for the approver; authenticated user ID and displayed username for the person who activated the feature; activation timestamp; and prior/new entitlement state. If one person performs both actions, record both roles explicitly rather than collapsing them into a generic “admin” event.
- The audit UI must visibly show **who verified/approved the payment and who activated the feature**, with names/usernames, roles and timestamps. Never rely on a free-text name alone: bind the record to the authenticated account ID and retain a display-name snapshot for historical readability.
- Separate capabilities/permissions for payment reviewer, feature activator, and auditor where practical. Enforce server-side authorization, tenant scoping, reason capture, idempotency, and conflict-of-interest policy. Define whether the same vendor user may approve and activate the same order before production; default to requiring a second authorized person for high-risk/manual exceptions if the business policy has not yet been approved.
- Support actions must be auditable and reversible where appropriate. Revocation must append a new event and preserve prior history; never edit/delete an old approval record to hide it. A support grant must not change the underlying payment record or falsely label an unpaid order as paid.
- Vendor support access must be time-bound or ticket-scoped where possible, least-privilege, and logged. Do not expose unrelated tenant data or secrets while troubleshooting. All access to customer/reseller World state and all privileged feature changes should be recorded.

### Additional acceptance criteria

13. Checkout supports buyer selection of IRR, USD or USDT only when an enabled compatible provider/rail exists; currency/provider mismatch is rejected server-side.
14. Multiple providers can be configured independently per currency, with test/live separation and no client exposure of secrets.
15. A new CEO can choose a free or paid initial office template and customize a free/premium avatar look; paid selections cannot be applied without an entitlement.
16. CEO and employee appearance/personality presentation settings persist and remain separate from operational permissions and employee execution configuration.
17. Vendor-owned support/testing context can preview all catalogue items without charge, while reseller/customer entitlements remain unchanged.
18. Vendor manual payment approval is required where configured, and cannot override a technically invalid or failed payment.
19. The audit trail identifies, by authenticated account ID and displayed username, both the payment approver and the feature activator, including timestamps, reasons and order/feature references.
20. Privileged support grants, approvals, activations and revocations are append-only, tenant-scoped, idempotent and reviewable; no grant silently changes an unpaid order to paid.


## Implementation checkpoint — vendor support diagnostics (2026-10-10)

The backend now includes a read-only vendor diagnostics endpoint at `GET /world-commerce/vendor/tenants/{tenant_id}/diagnostics`. It returns per-status order counts, up to 20 recent order summaries, and tenant entitlements without exposing buyer identity or payment transaction references. Access is limited to platform admins or vendor tenants holding the separate `world.support.view` permission, and non-admin vendor access is constrained to the vendor tenant and its descendants. Each diagnostics view writes an entry to the existing audit ledger. A new Alembic revision seeds the permission for owner/admin/tenant-admin roles; permission assignment and vendor hierarchy policy must still be reviewed before production enablement.

This is a read-only diagnostics primitive, not a complete support-ticket/session system. No temporary support grants, customer impersonation, payment provider verification, wallet ledger, lease automation, or 3D scene entitlement wiring is enabled. Tests were added for permission enforcement and unrelated-tenant isolation; verify CI on the latest branch head before treating them as passing.


### Diagnostics data-minimization regression test (2026-10-10)

A schema regression test now asserts that vendor support order summaries omit buyer user IDs and provider transaction references. The summary deliberately contains only the order identifier, catalogue code snapshot, amount/currency, status and timestamps. Re-run CI against the current head after this test-only change; the previously green CI applies to the earlier SHA only.


### Support diagnostics audit regression coverage (2026-10-10)

A success-path regression test now verifies that vendor diagnostics return only the minimal summary contract, preserve order counts, invoke the support-access audit recorder with the viewed tenant and actor, and commit the audit record with the response. This complements the permission-denial, unrelated-tenant denial, and sensitive-field omission tests. This remains a read-only diagnostic surface; it does not create support tickets, support sessions, impersonation, temporary grants, or commerce mutations.
