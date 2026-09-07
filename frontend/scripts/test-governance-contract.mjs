import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel) => fs.readFileSync(path.join(root, rel), "utf8");
const page = read("app/(customer)/governance/page.tsx");
const sidebar = read("components/layout/sidebar.tsx");

const required = [
  "/agent-governance/workforce-registry",
  "/agent-workforce/proposals",
  "/board-decision",
  "/ceo-decision",
  "/provision",
  "/activate",
  "/access-review",
];
for (const token of required) {
  if (!page.includes(token)) throw new Error(`governance page missing ${token}`);
}
for (const token of ["Workforce Registry", "Proposal Queue", "Submit workforce proposal", "Approve access"]) {
  if (!page.includes(token)) throw new Error(`governance UI missing ${token}`);
}
if (!sidebar.includes('href: "/governance"')) throw new Error("governance navigation missing");
if (!sidebar.includes("Workforce Governance")) throw new Error("governance navigation label missing");
console.log("Governance UI contract: PASS");
