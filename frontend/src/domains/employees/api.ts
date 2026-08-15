// Domain API boundary for employees.
// New UI code should call this boundary instead of importing transport clients directly.

export type EmployeesApi = {
  basePath: string;
};

export const employeesApi: EmployeesApi = {
  basePath: "/api/employees",
};
