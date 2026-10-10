import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const shell = readFileSync("features/world/WorldShell.tsx", "utf8");
const panel = readFileSync("features/world/WorldRoomAccessPanel.tsx", "utf8");
const viewport = readFileSync("features/world/WorldViewport.tsx", "utf8");

describe("World room access gate contracts", () => {
  it("checks the server access endpoint for the configured paid room", () => {
    expect(shell).toContain('"/world-commerce/catalogue"');
    expect(shell).toContain('"/world-commerce/room-inventory"');
    expect(shell).toContain("/world-commerce/room-inventory/");
    expect(shell).toContain("/access`");
    expect(shell).toContain("encodeURIComponent(roomAccessItemCode!)");
    expect(shell).toContain("roomAccessQuery.data?.granted === true");
    expect(shell).toContain("Boolean(roomAccessQuery.data.room_instance_id)");
  });

  it("does not treat loading or an unavailable authorization service as granted access", () => {
    expect(shell).toContain('roomInventoryQuery.isLoading || roomAccessQuery.isLoading || roomCatalogueQuery.isLoading || roomAccessUnavailable');
    expect(panel).toContain('state === "loading"');
    expect(panel).toContain('state === "unavailable"');
    expect(panel).toContain("دسترسی اتاق مسدود می‌ماند");
  });

  it("only presents the room access confirmation when the server grants access", () => {
    expect(shell).toContain('roomAccessGranted ? "Locked room nearby · Access authorized · Press E or inspect"');
    expect(shell).toContain('roomAccessGranted ? "granted" : "unavailable"');
    expect(panel).toContain("سرور مجوز فعال این اتاق را تأیید کرده است");
  });

  it("does not falsely claim that an authorized lease opens a 3D room", () => {
    expect(panel).toContain("اتصال مجوز به نمونهٔ اختصاصی اتاق");
    expect(panel).toContain("ادعای بازشدن اتاق نیست");
  });

  it("allows retrying failed server authorization without granting access optimistically", () => {
    expect(panel).toContain('onClick={onRetry}');
    expect(shell).toContain("void roomInventoryQuery.refetch(); void roomCatalogueQuery.refetch(); if (roomAccessItemCode) void roomAccessQuery.refetch();");
  });

  it("refreshes the latest room authorization callback after server state changes", () => {
    expect(viewport).toContain("roomInteractRef.current = onRoomInteract;");
    expect(viewport).toContain("roomProximityRef.current = onRoomProximity;");
    expect(viewport).toContain("onRoomProximity, onRoomInteract");
  });
});
