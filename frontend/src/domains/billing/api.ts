// Domain API boundary for billing.
// New UI code should call this boundary instead of importing transport clients directly.

export type BillingApi = {
  basePath: string;
};

export const billingApi: BillingApi = {
  basePath: "/api/billing",
};
