export type Locale = "en" | "fa";

export const messages = {
  en: {
    common: { language: "Language", english: "English", persian: "Persian", signOut: "Sign out", platformAdmin: "Platform Admin" },
    nav: { business: "Business", aiWorkspace: "AI Workspace", operations: "Operations", developer: "Developer", dashboard: "Business Dashboard", invoices: "Invoices", team: "Team & Roles" },
  },
  fa: {
    common: { language: "زبان", english: "انگلیسی", persian: "فارسی", signOut: "خروج", platformAdmin: "مدیریت پلتفرم" },
    nav: { business: "کسب‌وکار", aiWorkspace: "فضای کاری هوش مصنوعی", operations: "عملیات", developer: "توسعه‌دهنده", dashboard: "داشبورد کسب‌وکار", invoices: "فاکتورها", team: "تیم و نقش‌ها" },
  },
} as const;
