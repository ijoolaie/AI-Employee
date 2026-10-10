import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync("features/world/WorldRoomOfferPanel.tsx", "utf8");

describe("World room offer panel contracts", () => {
  it("supports IRR, USD and USDT", () => {
    expect(source).toContain('{ code: "IRR", label: "ریال" }');
    expect(source).toContain('{ code: "USD", label: "دلار آمریکا" }');
    expect(source).toContain('{ code: "USDT", label: "تتر" }');
  });

  it("loads catalogue data from the server and does not invent a price", () => {
    expect(source).toContain('"/world-commerce/catalogue"');
    expect(source).toContain("const amountValue = priceOption?.amount;");
    expect(source).toContain("در کاتالوگ تعریف نشده است");
  });

  it("sends order identity and payment choices without a client amount", () => {
    expect(source).toContain('"/world-commerce/orders"');
    expect(source).toContain("item_code: room.code");
    expect(source).toContain("payment_method: paymentMethod");
    expect(source).toContain("payment_provider: provider");
    expect(source).toContain("idempotency_key: key");
    expect(source).not.toContain("amount: amount");
  });

  it("preserves the idempotency key and distinguishes order from payment", () => {
    expect(source).toContain("const key = idempotencyKey ?? crypto.randomUUID();");
    expect(source).toContain("setIdempotencyKey(key);");
    expect(source).toContain("سفارش ثبت شد؛ پرداخت انجام نشده است.");
    expect(source).toContain("هیچ مبلغی کسر نشده و اتاقی فعال نشده است.");
  });

  it("describes the offer as lease renewal and does not imply immediate access", () => {
    expect(source).toContain("اجاره یا تمدید اتاق شرکت");
    expect(source).toContain("پس از تأیید و فعال‌سازی سمت سرور");
    expect(source).toContain("اتاق فعال نشده است.");
  });

  it("blocks incomplete orders and locks choices during submission", () => {
    expect(source).toContain("if (!room || !amount || !provider || !paymentMethod || createOrderMutation.isPending) return;");
    expect(source).toContain("disabled={!amount || !provider || !paymentMethod || createOrderMutation.isPending}");
  });
});
