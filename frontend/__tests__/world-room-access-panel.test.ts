import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const shell = readFileSync("features/world/WorldShell.tsx", "utf8");
const panel = readFileSync("features/world/WorldRoomAccessPanel.tsx", "utf8");
const viewport = readFileSync("features/world/WorldViewport.tsx", "utf8");
const access = readFileSync("features/world/WorldRoomSceneAccess.ts", "utf8");

describe("World room access gate contracts", () => {
  it("uses tenant-scoped inventory access and requires a room instance", () => {
    expect(shell).toContain('"/world-commerce/room-inventory"');
    expect(shell).toContain("/world-commerce/room-inventory/");
    expect(shell).toContain("/access`");
    expect(shell).toContain("roomAccessQuery.data?.granted === true");
    expect(shell).toContain("room_instance_id");
    expect(shell).toContain("expires_at");
  });

  it("fails closed after query errors even if TanStack Query retains prior data", () => {
    expect(shell).toContain("roomInventoryQuery.error || roomCatalogueQuery.error || roomAccessQuery.error");
    expect(shell).toContain("isRoomSceneAccessUsable(roomSceneAccess, roomAccessUnavailable)");
    expect(access).toContain("if (unavailable || access?.granted !== true) return false;");
  });

  it("enforces expiry at the 3D scene boundary, not only on the polling interval", () => {
    expect(viewport).toContain("isRoomSceneAccessUsable(access, access.unavailable)");
    expect(viewport).toContain("roomInterior.visible = roomGranted");
    expect(viewport).toContain("roomEntrance.userData.door.rotation.y = roomGranted ? Math.PI / 2 : 0");
    expect(shell).toContain("window.setTimeout(() => { void roomAccessQuery.refetch(); }, delay)");
  });

  it("binds the visible procedural scene to the authorized room instance ID", () => {
    expect(viewport).toContain("roomInterior.userData.roomInstanceId = authorizedInstanceId");
    expect(viewport).toContain("roomInterior.userData.roomInstanceId === authorizedInstanceId");
    expect(panel).toContain("شناسه نمونه");
    expect(panel).toContain("جایگذاری کارمندان و سفارشی‌سازی پایدار مدیر هنوز تکمیل نشده است");
  });

  it("keeps retry and denied/unavailable messaging non-optimistic", () => {
    expect(panel).toContain('state === "loading"');
    expect(panel).toContain('state === "unavailable"');
    expect(panel).toContain("دسترسی اتاق مسدود می‌ماند");
    expect(panel).toContain("onClick={onRetry}");
  });
});
