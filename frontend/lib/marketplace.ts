import { api } from "@/lib/api";

type MarketplacePublication = {
  id: string;
  owner_tenant_id: string;
  team_version_id: string;
  visibility: "private" | "unlisted" | "public" | string;
  status: string;
  title: string;
  summary: string | null;
  published_by: string | null;
  published_at: string;
  withdrawn_at: string | null;
  customer_acceptance: "not_implied" | string;
  production_deployment: "not_implied" | string;
  trust_basis: "recorded_evidence_only" | string;
};

type MarketplaceInstallation = {
  id: string;
  tenant_id: string;
  team_version_id: string;
  source_publication_id: string;
  workspace_key: string | null;
  enabled: boolean;
  installed_by: string | null;
  installed_at: string;
};

function unwrap<T>(response: { data: { success: boolean; data?: T } }): T {
  if (!response.data.success || response.data.data === undefined) throw new Error("Unexpected API response");
  return response.data.data;
}

export async function listMarketplacePublications() {
  return unwrap((await api.get<{ success: boolean; data?: MarketplacePublication[] }>("/marketplace/publications", { params: { visibility: "public" } })));
}

export async function getMarketplacePublication(id: string) {
  return unwrap((await api.get<{ success: boolean; data?: MarketplacePublication }>(`/marketplace/publications/${id}`)));
}

export async function installMarketplacePublication(id: string, workspaceKey?: string) {
  return unwrap((await api.post<{ success: boolean; data?: MarketplaceInstallation }>(`/marketplace/publications/${id}/install`, { workspace_key: workspaceKey || null })));
}

export type { MarketplaceInstallation, MarketplacePublication };
