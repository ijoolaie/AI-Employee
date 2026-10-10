import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const shell = readFileSync("features/world/WorldShell.tsx", "utf8");
const panel = readFileSync("features/world/WorldRoomAccessPanel.tsx", "utf8");
const viewport = readFileSync("features/world/WorldViewport.tsx", "utf8");

describe("World room access gate contracts", () => {
  it("checks the server access endpoint for the configured paid room", () => {
    expect(shell).toContain('"/world-commerce/catalogue"');
    expect(shell).toContain("/world-commerce/room-inventory/");
    expect(shell).toContain("/access`");
    expect(shell).toContain("encodeURIComponent(roomCatalogueQuery.data!)");
    expect(shell).toContain("roomAccessQuery.data?.granted === true");
    expect(shell).toContain("Boolean(roomAccessQuery.data.room_instance_id)");
  });

  it("does not treat loading or an unavailable authorization service as granted access", () => {
    expect(shell).toContain('roomAccessQuery.isLoading || roomCatalogueQuery.isLoading || roomAccessUnavailable');
    expect(panel).toContain('state === "loading"');
    expect(panel).toContain('state === "unavailable"');
    expect(panel).toContain("دسترسی اتاق مسدود می‌ماند");
  });

  it("only presents the room access confirmation when the server grants access", () => {
    expect(shell).toContain('roomAccessGranted ? "Locked room nearby · Access authorized · Press E or inspect"');
    expect(shell).toContain('roomAccessGranted ? "granted" : "unavailable"');
    expect(panel).toContain("سرور مجوز و نمونهٔ پایدار اتاق را تأیید کرده است");
  });

  it("renders a room interior only for an authorized persistent room instance", () => {
    expect(viewport).toContain("const roomGranted = roomAccessRef.current.granted && Boolean(roomAccessRef.current.roomInstanceId);");
    expect(viewport).toContain("roomInterior.visible = roomGranted;");
    expect(viewport).toContain("roomEntrance.userData.door.rotation.y = roomGranted ? Math.PI / 2 : 0;");
    expect(viewport).toContain("roomEntrance.userData.doorway.visible = !roomGranted;");
    expect(panel).toContain("ذخیره‌سازی سفارشی‌سازی‌ها و چیدمان اختصاصی هنوز تکمیل نشده است");
  });

  it("allows retrying failed server authorization without granting access optimistically", () => {
    expect(panel).toContain('onClick={onRetry}');
    expect(shell).toContain("void roomCatalogueQuery.refetch(); if (roomCatalogueQuery.data) void roomAccessQuery.refetch();");
  });

  it("refreshes the latest room authorization callback after server state changes", () => {
    expect(viewport).toContain("roomInteractRef.current = onRoomInteract;");
    expect(viewport).toContain("roomProximityRef.current = onRoomProximity;");
    expect(viewport).toContain("onRoomProximity, onRoomInteract");
  });
});
