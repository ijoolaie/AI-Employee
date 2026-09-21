export type Locale = "en" | "fa";

export const messages = {
  en: {
    common: { language: "Language", english: "English", persian: "Persian", signOut: "Sign out", platformAdmin: "Platform Admin" },
    employee: { title: "Employees", description: "AI roles available in your organization", newEmployee: "New employee", noEmployees: "No employees yet", noEmployeesDescription: "Create your first custom AI employee to start running tasks.", createEmployee: "Create employee", created: "Created", name: "Name", slug: "Slug", allowedTools: "Allowed tools", allowedToolsDescription: "Only tools explicitly selected here can be exposed to the AI during a Run.", noTools: "No registered tools available.", promptTemplate: "Prompt template", cancel: "Cancel", publishCustomers: "Publish to your customers", publishDescription: "Create a public web channel. Your customers can chat with this employee without logging into the AI Employee Platform.", publish: "Publish", customerChatUrl: "Customer chat URL", copyUrl: "Copy URL", guardrails: "Guardrails", guardrailsDescription: "Control risky actions, approvals and forbidden operations. Changes publish a new employee version.", saveGuardrails: "Save guardrails", runEmployee: "Run this employee", documentFile: "Document file (PDF, image, or DOCX)", datasetFile: "Dataset file (CSV or Excel)", noFiles: "No files uploaded yet.", uploadFirst: "Upload one on the Files page first.", inputJson: "Input (JSON)", startRun: "Start run", runHistory: "Run history", noRuns: "No runs for this employee yet.", loading: "Loading…", selectFile: "Select a file…", inputInvalidJson: "Input must be valid JSON", chooseDocument: "Choose a PDF, image, or DOCX file to analyze first.", chooseDataset: "Choose a CSV/Excel file to analyze first.", cancel: "Cancel" },
    nav: { business: "Business", aiWorkspace: "AI Workspace", operations: "Operations", developer: "Developer", dashboard: "Business Dashboard", invoices: "Invoices", team: "Team & Roles" },
  },
  fa: {
    common: { language: "زبان", english: "انگلیسی", persian: "فارسی", signOut: "خروج", platformAdmin: "مدیریت پلتفرم" },
    nav: { business: "کسب‌وکار", aiWorkspace: "فضای کاری هوش مصنوعی", operations: "عملیات", developer: "توسعه‌دهنده", dashboard: "داشبورد کسب‌وکار", invoices: "فاکتورها", team: "تیم و نقش‌ها" },
  },
} as const;
