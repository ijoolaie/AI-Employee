import { strict as assert } from "node:assert";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = join(process.cwd(), "src");
const domains = ["employees", "workflow", "knowledge", "crm", "commerce", "billing"];

for (const domain of domains) {
  assert.ok(existsSync(join(root, "domains", domain, "index.ts")), `${domain} domain missing`);
  assert.ok(existsSync(join(root, "domains", domain, "api.ts")), `${domain} api boundary missing`);
  assert.ok(existsSync(join(root, "domains", domain, "types.ts")), `${domain} types missing`);
}

const registry = readFileSync(join(root, "domain-registry.ts"), "utf8");
for (const domain of domains) {
  assert.ok(registry.includes(`${domain}:`), `${domain} not registered`);
}
