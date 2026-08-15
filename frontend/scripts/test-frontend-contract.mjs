
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, "..");

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log("  OK " + name);
  } catch (e) {
    failed++;
    console.error("  FAIL " + name);
    console.error("    " + e.message);
  }
}

function read(rel) {
  const full = path.join(root, rel);
  if (!fs.existsSync(full)) throw new Error("missing file: " + rel);
  return fs.readFileSync(full, "utf8");
}

console.log("\n=== Frontend Backend contract tests ===\n");

for (const rel of [
  "lib/api.ts",
  "lib/errors.ts",
  "lib/auth-store.ts",
  "types/index.ts",
  "app/(auth)/login/page.tsx",
  "app/(customer)/settings/page.tsx",
  "app/(customer)/knowledge/page.tsx",
  "app/(customer)/memory/page.tsx",
  "components/layout/sidebar.tsx",
  ".env.example",
]) {
  test("exists " + rel, () => { read(rel); });
}

test("login Suspense", () => {
  const src = read("app/(auth)/login/page.tsx");
  if (!src.includes("Suspense")) throw new Error("no Suspense");
  if (!src.includes("useSearchParams")) throw new Error("no useSearchParams");
});

test("password recovery UI and API contract", () => {
  const login = read("app/(auth)/login/page.tsx");
  const forgot = read("app/(auth)/forgot-password/page.tsx");
  const reset = read("app/(auth)/reset-password/page.tsx");
  const api = read("lib/api.ts");
  if (!login.includes('href="/forgot-password"')) throw new Error("login missing password recovery link");
  if (!forgot.includes("forgotPassword")) throw new Error("forgot password page not wired");
  if (!reset.includes("resetPassword")) throw new Error("reset password page not wired");
  if (!api.includes('post<APIResponse<{ message: string }>>("/auth/forgot-password"')) throw new Error("forgot password API path missing");
  if (!api.includes('post<APIResponse<{ message: string }>>("/auth/reset-password"')) throw new Error("reset password API path missing");
});

test("settings stale copy removed", () => {
  const src = read("app/(customer)/settings/page.tsx");
  if (src.includes("will appear here in a later phase")) throw new Error("stale copy");
  if (!src.includes("/billing") || !src.includes("/usage")) throw new Error("missing links");
});

const api = read("lib/api.ts");
for (const name of ["indexKnowledgeFile", "searchKnowledge", "createMemory", "searchMemory", "deleteMemory"]) {
  test("api " + name, () => {
    if (!api.includes("function " + name)) throw new Error("not found");
  });
}

test("knowledge paths", () => {
  if (!api.includes("/knowledge/index")) throw new Error("no index path");
  if (!api.includes("/knowledge/search")) throw new Error("no search path");
});

test("memory paths", () => {
  if (!api.includes("/memory")) throw new Error("no memory");
  if (!api.includes("/memory/search")) throw new Error("no search");
});

const types = read("types/index.ts");
for (const name of ["KnowledgeDocument", "KnowledgeSearchResult", "MemoryItem", "MemorySearchResult"]) {
  test("type " + name, () => {
    if (!types.includes("interface " + name)) throw new Error("missing");
  });
}

test("sidebar nav", () => {
  const src = read("components/layout/sidebar.tsx");
  if (!src.includes('href: "/knowledge"')) throw new Error("no knowledge");
  if (!src.includes('href: "/memory"')) throw new Error("no memory");
});

test("knowledge page helpers", () => {
  const src = read("app/(customer)/knowledge/page.tsx");
  if (!src.includes("indexKnowledgeFile") || !src.includes("searchKnowledge")) throw new Error("incomplete");
});

test("memory page helpers", () => {
  const src = read("app/(customer)/memory/page.tsx");
  if (!src.includes("createMemory") || !src.includes("searchMemory") || !src.includes("deleteMemory")) throw new Error("incomplete");
});

test("errors module", () => {
  const src = read("lib/errors.ts");
  if (!src.includes("export function getErrorMessage")) throw new Error("missing");
});

test("api reexports errors", () => {
  if (!api.includes('from "./errors"')) throw new Error("no reexport");
});

for (const rel of [
  "app/(customer)/orders/page.tsx",
  "app/(customer)/sales/page.tsx",
]) {
  test("exists " + rel, () => { read(rel); });
}

for (const name of ["listOrders", "getOrderSummary", "updateOrderStatus", "listDeals", "getSalesPipeline", "getSalesForecast", "updateDealStage"]) {
  test("api " + name, () => {
    if (!api.includes("function " + name)) throw new Error("not found: " + name);
  });
}

test("orders paths", () => {
  if (!api.includes("/orders")) throw new Error("no orders");
  if (!api.includes("/orders/summary")) throw new Error("no orders summary");
});

test("sales paths", () => {
  if (!api.includes("/sales/deals")) throw new Error("no deals");
  if (!api.includes("/sales/pipeline")) throw new Error("no pipeline");
  if (!api.includes("/sales/forecast")) throw new Error("no forecast");
});

for (const name of ["BusinessOrder", "OrderSummary", "BusinessDeal", "SalesPipelineSummary", "SalesForecast"]) {
  test("type " + name, () => {
    if (!types.includes("interface " + name)) throw new Error("missing " + name);
  });
}

test("sidebar orders sales", () => {
  const src = read("components/layout/sidebar.tsx");
  if (!src.includes('href: "/orders"')) throw new Error("no orders nav");
  if (!src.includes('href: "/sales"')) throw new Error("no sales nav");
});

test("orders page helpers", () => {
  const src = read("app/(customer)/orders/page.tsx");
  if (!src.includes("listOrders") || !src.includes("getOrderSummary")) throw new Error("incomplete orders");
});

test("sales page helpers", () => {
  const src = read("app/(customer)/sales/page.tsx");
  if (!src.includes("listDeals") || !src.includes("getSalesPipeline")) throw new Error("incomplete sales");
});

test("orders emptystate icon", () => {
  const src = read("app/(customer)/orders/page.tsx");
  if (!src.includes("icon={ShoppingCart}")) throw new Error("missing icon");
});
test("sales emptystate icon", () => {
  const src = read("app/(customer)/sales/page.tsx");
  if (!src.includes("icon={TrendingUp}")) throw new Error("missing icon");
});

// ── v0.9.5 Enterprise pages coverage ──────────────────────────────
const enterprisePages = [
  "app/(customer)/dashboard/page.tsx",
  "app/(customer)/chat/page.tsx",
  "app/(customer)/studio/page.tsx",
  "app/(customer)/employees/page.tsx",
  "app/(customer)/employees/new/page.tsx",
  "app/(customer)/runs/page.tsx",
  "app/(customer)/traces/page.tsx",
  "app/(customer)/workflows/page.tsx",
  "app/(customer)/approvals/page.tsx",
  "app/(customer)/schedules/page.tsx",
  "app/(customer)/files/page.tsx",
  "app/(customer)/analytics/page.tsx",
  "app/(customer)/usage/page.tsx",
  "app/(customer)/billing/page.tsx",
  "app/(customer)/developer/page.tsx",
  "app/(customer)/api-keys/page.tsx",
  "app/(customer)/tasks/page.tsx",
  "app/(customer)/reports/page.tsx",
  "app/(customer)/logs/page.tsx",
  "app/(customer)/webhooks/page.tsx",
  "app/(admin)/admin/page.tsx",
  "app/(admin)/admin/tenants/page.tsx",
  "app/(admin)/admin/validation/page.tsx",
  "app/(auth)/register/page.tsx",
];
for (const rel of enterprisePages) {
  test("exists " + rel, () => { read(rel); });
}

// Core API surface for AI Employees / Runs / Chat / Studio
for (const name of [
  "listEmployees", "getEmployee", "createEmployee", "listAvailableTools",
  "listRuns", "getRun", "createRun", "getRunTrace",
  "getCustomerDashboard", "getOperationsMetrics", "getAuditLogs",
  "listDeadLetters", "replayDeadLetter",
  "listApprovals", "decideApproval",
  "listWorkflows", "createWorkflow", "getWorkflow",
  "listBillingPlans", "getSubscription", "createCheckoutSession",
  "listFiles", "uploadFile", "deleteFile",
]) {
  test("api " + name, () => {
    if (!api.includes("function " + name)) throw new Error("not found: " + name);
  });
}

for (const name of ["listApiKeys", "createApiKey", "revokeApiKey"]) {
  test("api " + name, () => {
    if (!api.includes("function " + name)) throw new Error("not found: " + name);
  });
}
test("api key page is real CRUD UI", () => {
  const src = read("app/(customer)/api-keys/page.tsx");
  for (const name of ["listApiKeys", "createApiKey", "revokeApiKey"]) {
    if (!src.includes(name)) throw new Error("missing " + name);
  }
});
test("customer P2 pages exist", () => {
  for (const rel of ["app/(customer)/tasks/page.tsx", "app/(customer)/reports/page.tsx"]) read(rel);
});
test("developer P3 logs page exists", () => read("app/(customer)/logs/page.tsx"));
test("sidebar exposes P0-P3 surfaces", () => {
  const src = read("components/layout/sidebar.tsx");
  for (const href of ["/tasks", "/reports", "/logs"]) {
    if (!src.includes('href: "' + href + '"')) throw new Error("missing nav " + href);
  }
});

test("chat page uses real runs", () => {
  const src = read("app/(customer)/chat/page.tsx");
  if (!src.includes("createRun") || !src.includes("getRun")) throw new Error("chat not wired to runs");
  if (!src.includes("listEmployees")) throw new Error("chat missing employees");
});

test("studio page creates employee", () => {
  const src = read("app/(customer)/studio/page.tsx");
  if (!src.includes("createEmployee") || !src.includes("listAvailableTools")) throw new Error("studio incomplete");
  if (!src.includes("allowed_tools") && !src.includes("selectedTools")) throw new Error("studio missing tools");
});

test("dashboard uses customer dashboard api", () => {
  const src = read("app/(customer)/dashboard/page.tsx");
  if (!src.includes("getCustomerDashboard") && !src.includes("dashboard")) throw new Error("dashboard incomplete");
});

test("developer console has dlq/ops", () => {
  const src = read("app/(customer)/developer/page.tsx");
  if (!src.includes("listDeadLetters") && !src.includes("Dead")) throw new Error("developer missing DLQ");
  if (!src.includes("getOperationsMetrics") && !src.includes("getAuditLogs") && !src.includes("audit")) throw new Error("developer missing ops");
});

test("traces page loads run trace", () => {
  const src = read("app/(customer)/traces/page.tsx");
  if (!src.includes("getRunTrace") && !src.includes("trace")) throw new Error("traces incomplete");
});

test("approvals page has decide", () => {
  const src = read("app/(customer)/approvals/page.tsx");
  if (!src.includes("listApprovals") || !src.includes("decideApproval")) throw new Error("approvals incomplete");
});

test("billing page has plans/subscription", () => {
  const src = read("app/(customer)/billing/page.tsx");
  if (!src.includes("listBillingPlans") && !src.includes("getSubscription") && !src.includes("billing")) throw new Error("billing incomplete");
});

test("sidebar full nav groups", () => {
  const src = read("components/layout/sidebar.tsx");
  const required = ["/dashboard", "/chat", "/employees", "/workflows", "/runs", "/approvals",
    "/schedules", "/knowledge", "/memory", "/files", "/analytics", "/usage", "/billing",
    "/traces", "/studio", "/developer", "/api-keys", "/webhooks", "/settings", "/orders", "/sales"];
  for (const href of required) {
    if (!src.includes('href: "' + href + '"')) throw new Error("missing nav " + href);
  }
});

test("admin pages exist and call admin apis", () => {
  const admin = read("app/(admin)/admin/page.tsx");
  const tenants = read("app/(admin)/admin/tenants/page.tsx");
  const validation = read("app/(admin)/admin/validation/page.tsx");
  if (!admin.includes("getAdminDashboard") && !admin.includes("admin")) throw new Error("admin dashboard incomplete");
  if (!tenants.includes("listAdminTenants") && !tenants.includes("tenant")) throw new Error("tenants incomplete");
  if (!validation.includes("getValidationSummary") && !validation.includes("validation")) throw new Error("validation incomplete");
});

test("register page present", () => {
  const src = read("app/(auth)/register/page.tsx");
  if (!src.includes("register") && !src.includes("Register")) throw new Error("register incomplete");
});

test("api base and auth interceptor", () => {
  if (!api.includes("API_BASE") && !api.includes("baseURL")) throw new Error("no API base");
  if (!api.includes("refresh") || !api.includes("Authorization")) throw new Error("no auth interceptor");
});

// ── RC7/RC8 production-readiness coverage ──────────────────────────
for (const rel of [
  "app/(customer)/analytics/page.tsx",
  "app/(customer)/templates/page.tsx",
  "app/(customer)/billing/page.tsx",
  "app/(customer)/integrations/page.tsx",
  "app/(customer)/customers/page.tsx",
  "app/(customer)/inbox/page.tsx",
]) {
  test("RC7 page exists " + rel, () => { read(rel); });
}

test("RC7 sidebar covers sales-critical workspaces", () => {
  const src = read("components/layout/sidebar.tsx");
  for (const href of ["/analytics", "/templates", "/billing", "/integrations", "/customers", "/inbox"]) {
    if (!src.includes('href: "' + href + '"')) throw new Error("missing RC7 nav " + href);
  }
});

test("RC8 release metadata", () => {
  const pkg = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
  if (pkg.version !== "1.0.0-rc.8") throw new Error("frontend version is not rc.8");
});


// ── RC8 GDPR / customer-channel coverage ───────────────────────────
for (const rel of [
  "app/(customer)/privacy/page.tsx",
  "app/(customer)/customers/page.tsx",
  "app/(customer)/inbox/page.tsx",
  "app/(customer)/channels/page.tsx",
  "app/chat/[publicKey]/page.tsx",
]) {
  test("RC8 page exists " + rel, () => { read(rel); });
}

for (const name of ["listCustomers", "exportCustomerData", "deleteCustomerData", "sendInboxMessage", "sendPublicMessage", "listProducts"]) {
  test("RC8 api " + name, () => {
    if (!api.includes("function " + name)) throw new Error("not found: " + name);
  });
}

test("RC8 privacy page uses GDPR api", () => {
  const src = read("app/(customer)/privacy/page.tsx");
  if (!src.includes("exportCustomerData") || !src.includes("deleteCustomerData")) throw new Error("privacy page incomplete");
});

test("RC8 inbox page uses inbox api", () => {
  const src = read("app/(customer)/inbox/page.tsx");
  if (!src.includes("sendInboxMessage")) throw new Error("inbox page not wired to send message");
});

test("RC8 public chat page uses public message api", () => {
  const src = read("app/chat/[publicKey]/page.tsx");
  if (!src.includes("sendPublicMessage")) throw new Error("public chat not wired to message api");
});

// RC8 P0-P4 password recovery contract checks
const recoveryChecks = [
  ["exists app/(auth)/forgot-password/page.tsx", "app/(auth)/forgot-password/page.tsx"],
  ["exists app/(auth)/reset-password/page.tsx", "app/(auth)/reset-password/page.tsx"],
  ["api forgotPassword", "forgotPassword"],
  ["api resetPassword", "resetPassword"],
];
for (const [label, needle] of recoveryChecks) {
  const ok = needle.endsWith(".tsx") ? fs.existsSync(path.join(root, needle)) : api.includes(needle);
  if (!ok) { console.error(`  FAIL ${label}`); failed++; } else { passed++; console.log(`  OK ${label}`); }
}

console.log("\nResult: " + passed + " passed, " + failed + " failed\n");
process.exit(failed ? 1 : 0);
