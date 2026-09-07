import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel) => fs.readFileSync(path.join(root, rel), "utf8");
const page = read("app/(customer)/governance/page.tsx");
const sidebar = read("components/layout/sidebar.tsx");

const required = [
  "/agent-governance/workforce-registry",
  "/agent-governance/templates/",
  "/evaluations`)).data",
  "/agent-governance/templates/${templateId}/evaluate",
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
for (const token of [
  "Workforce Registry",
  "Proposal Queue",
  "Submit workforce proposal",
  "Approve access",
  "Evaluation evidence",
  "Record evaluation",
  "agent_workforce.board_review",
  "agent_workforce.ceo_approve",
  "agent_workforce.provision",
  "agent_workforce.activate",
]) {
  if (!page.includes(token)) throw new Error(`governance UI missing ${token}`);
}
if (!page.includes("{ approve: true }")) throw new Error("Board/CEO approval payload must use approve=true");
if (!page.includes("{ approve: false }")) throw new Error("Board rejection payload must use approve=false");
if (!page.includes("proposal.provisioned_agent_instance_id")) throw new Error("proposal activation binding missing");
if (!page.includes("?.identity_id")) throw new Error("proposal access review must resolve AgentIdentity id");
if (!sidebar.includes('href: "/governance"')) throw new Error("governance navigation missing");
if (!sidebar.includes("Workforce Governance")) throw new Error("governance navigation label missing");
console.log("Governance UI contract: PASS");
