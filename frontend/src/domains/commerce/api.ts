// Domain API boundary for commerce.
// New UI code should call this boundary instead of importing transport clients directly.

export type CommerceApi = {
  basePath: string;
};

export const commerceApi: CommerceApi = {
  basePath: "/api/commerce",
};
