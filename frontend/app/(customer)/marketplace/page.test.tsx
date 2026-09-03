import { describe, expect, it, vi } from "vitest";

const { get, post } = vi.hoisted(() => ({
  get: vi.fn(async () => ({ data: { success: true, data: [{ id: "pub-1", title: "Support Team", visibility: "public", status: "published" }] } })),
  post: vi.fn(async (path: string, body: unknown) => ({ data: { success: true, data: { id: "install-1", source_publication_id: path.split("/").at(-2), workspace_key: (body as { workspace_key: string }).workspace_key } } })),
}));

vi.mock("@/lib/api", () => ({ api: { get, post } }));

import { installMarketplacePublication, listMarketplacePublications } from "@/lib/marketplace";

describe("Marketplace installation client", () => {
  it("discovers only public publications", async () => {
    const publications = await listMarketplacePublications();
    expect(publications).toHaveLength(1);
    expect(get).toHaveBeenCalledWith("/marketplace/publications", { params: { visibility: "public" } });
  });

  it("sends the selected publication and workspace to the backend authorization boundary", async () => {
    const installation = await installMarketplacePublication("pub-1", "ops");
    expect(installation).toMatchObject({ id: "install-1", source_publication_id: "pub-1", workspace_key: "ops" });
    expect(post).toHaveBeenCalledWith("/marketplace/publications/pub-1/install", { workspace_key: "ops" });
  });
});
