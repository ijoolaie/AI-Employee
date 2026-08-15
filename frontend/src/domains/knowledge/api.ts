// Domain API boundary for knowledge.
// New UI code should call this boundary instead of importing transport clients directly.

export type KnowledgeApi = {
  basePath: string;
};

export const knowledgeApi: KnowledgeApi = {
  basePath: "/api/knowledge",
};
