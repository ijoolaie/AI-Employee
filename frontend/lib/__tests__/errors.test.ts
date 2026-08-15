import { describe, expect, it } from "vitest";
import axios from "axios";
import { getErrorMessage } from "../errors";

describe("getErrorMessage", () => {
  it("reads API envelope error.message", () => {
    const err = {
      isAxiosError: true,
      response: { data: { error: { message: "Tenant slug taken", code: "SLUG_TAKEN" } }, status: 409 },
      message: "Request failed",
    };
    // axios.isAxiosError checks prototype; use real AxiosError shape via adapter
    const real = new axios.AxiosError("fail");
    real.response = {
      data: { error: { message: "Tenant slug taken", code: "SLUG_TAKEN" } },
      status: 409,
      statusText: "Conflict",
      headers: {},
      config: {} as never,
    };
    expect(getErrorMessage(real)).toBe("Tenant slug taken");
  });

  it("reads FastAPI string detail", () => {
    const real = new axios.AxiosError("fail");
    real.response = {
      data: { detail: "Not authenticated" },
      status: 401,
      statusText: "Unauthorized",
      headers: {},
      config: {} as never,
    };
    expect(getErrorMessage(real)).toBe("Not authenticated");
  });

  it("joins validation detail array", () => {
    const real = new axios.AxiosError("fail");
    real.response = {
      data: { detail: [{ msg: "field required" }, { msg: "invalid email" }] },
      status: 422,
      statusText: "Unprocessable",
      headers: {},
      config: {} as never,
    };
    expect(getErrorMessage(real)).toBe("field required; invalid email");
  });

  it("maps 403 without body message", () => {
    const real = new axios.AxiosError("fail");
    real.response = {
      data: {},
      status: 403,
      statusText: "Forbidden",
      headers: {},
      config: {} as never,
    };
    expect(getErrorMessage(real)).toBe("You do not have permission for this action.");
  });

  it("handles plain Error", () => {
    expect(getErrorMessage(new Error("boom"))).toBe("boom");
  });

  it("handles unknown", () => {
    expect(getErrorMessage(123)).toBe("Unknown error");
  });
});
