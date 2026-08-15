// Domain API boundary for crm.
// New UI code should call this boundary instead of importing transport clients directly.

export type CrmApi = {
  basePath: string;
};

export const crmApi: CrmApi = {
  basePath: "/api/crm",
};
