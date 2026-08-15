// Domain API boundary for workflow.
// New UI code should call this boundary instead of importing transport clients directly.

export type WorkflowApi = {
  basePath: string;
};

export const workflowApi: WorkflowApi = {
  basePath: "/api/workflow",
};
