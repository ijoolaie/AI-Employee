import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const source = readFileSync("features/world/WorldShell.tsx", "utf8");
const viewport = readFileSync("features/world/WorldViewport.tsx", "utf8");

describe("World room inventory access", () => {
  it("reads room access from the tenant-scoped persistent inventory endpoint", () => {
    expect(source).toContain("/world-commerce/room-inventory/");
    expect(source).toContain("/access`");
    expect(source).toContain("roomAccessQuery.data?.granted === true");
    expect(source).toContain("Boolean(roomAccessQuery.data.room_instance_id)");
  });

  it("requires a server-issued room instance and server expiry before showing the room", () => {
    expect(source).toContain("roomAccessQuery.data?.room_instance_id ?? null");
    expect(source).toContain("roomAccessQuery.data?.expires_at ?? null");
    expect(viewport).toContain("roomAccessRef.current.granted && Boolean(roomAccessRef.current.roomInstanceId)");
    expect(viewport).toContain("roomInterior.visible = roomGranted;");
  });

  it("fails closed when inventory authorization cannot be loaded", () => {
    expect(source).toContain("roomCatalogueQuery.error || roomAccessQuery.error");
    expect(source).toContain("roomAccessUnavailable");
    expect(source).toContain("نمونه اتاق دارای مجوز معتبر برای این مستأجر پیدا نشد.");
  });
});
