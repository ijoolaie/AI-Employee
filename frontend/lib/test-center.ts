import { api } from "@/lib/api";

type TestDefinition = {
  id: string;
  code: string;
  name: string;
  test_type: string;
  category: string;
  description: string | null;
  workspace_key: string | null;
  prerequisites: Record<string, unknown>;
  expected_result: Record<string, unknown>;
  evidence_requirements: Record<string, unknown>;
  enabled: boolean;
  created_at: string;
  updated_at: string;
};

type TestRun = {
  id: string;
  test_definition_id: string;
  workspace_key: string | null;
  status: string;
  actor_id: string | null;
  executor_type: string;
  correlation_id: string;
  fixtures: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  evidence: Record<string, unknown>;
  runtime_version: string | null;
  migration_identity: string | null;
  git_sha: string | null;
  evidence_boundary: string;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

type Artifact = {
  id: string;
  artifact_type: string;
  label: string;
  reference: string;
  sha256: string | null;
  size_bytes: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

type VerificationRecord = {
  record_type: string;
  schema_version: string;
  generated_at: string;
  acceptance_boundary: string;
  acceptance_statement: string;
  tenant_id: string;
  run: TestRun & { test_definition_id: string };
  test_definition: TestDefinition;
  artifacts: Artifact[];
};

function unwrap<T>(response: { data: { success: boolean; data?: T } }): T {
  if (!response.data.success || response.data.data === undefined) {
    throw new Error("Unexpected API response");
  }
  return response.data.data;
}

export async function listTestDefinitions(workspaceKey?: string) {
  const params = workspaceKey ? { workspace_key: workspaceKey } : undefined;
  return unwrap((await api.get<{ success: boolean; data?: TestDefinition[] }>("/test-center/definitions", { params })));
}

export async function listTestRuns(params?: {
  workspace_key?: string;
  status?: string;
  test_definition_id?: string;
  limit?: number;
}) {
  return unwrap((await api.get<{ success: boolean; data?: TestRun[] }>("/test-center/runs", { params })));
}

export async function createTestRun(payload: {
  test_definition_id: string;
  workspace_key?: string | null;
  fixtures?: Record<string, unknown>;
}) {
  return unwrap((await api.post<{ success: boolean; data?: TestRun }>("/test-center/runs", payload)));
}

export async function getTestRun(runId: string) {
  return unwrap((await api.get<{ success: boolean; data?: TestRun }>(`/test-center/runs/${runId}`)));
}

export async function getTestRunArtifacts(runId: string) {
  return unwrap((await api.get<{ success: boolean; data?: Artifact[] }>(`/test-center/runs/${runId}/artifacts`)));
}

export async function exportVerificationRecord(runId: string) {
  const response = await api.get<VerificationRecord>(`/test-center/runs/${runId}/verification-record`, {
    responseType: "blob",
  });
  return response.data;
}

export type { Artifact, TestDefinition, TestRun, VerificationRecord };
