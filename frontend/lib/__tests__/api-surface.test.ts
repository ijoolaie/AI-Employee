import { describe, expect, it } from "vitest";
import * as api from "../api";

/**
 * Contract smoke: frontend must expose client helpers for every major
 * backend capability used by the UI (aligned with backend/app/api/v1/router.py).
 */
describe("api client surface", () => {
  const required = [
    "login",
    "register",
    "fetchMe",
    "listEmployees",
    "listFiles",
    "listRuns",
    "getRun",
    "getRunTrace",
    "listWorkflows",
    "listBillingPlans",
    "createCheckoutSession",
    "createPortalSession",
    "indexKnowledgeFile",
    "searchKnowledge",
    "createMemory",
    "searchMemory",
    "deleteMemory",
    "getErrorMessage",
  ] as const;

  for (const name of required) {
    it(`exports ${name}`, () => {
      expect(typeof (api as Record<string, unknown>)[name]).toBe("function");
    });
  }
});
