"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  {
    href: "/settings",
    label: "General",
    description: "Profile and organization details",
  },
  {
    href: "/settings/security",
    label: "Security",
    description: "Password and account security",
  },
];

export default function SettingsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-6 lg:flex-row lg:items-start lg:px-6">
      <aside className="w-full shrink-0 lg:w-64" aria-label="Settings navigation">
        <nav className="rounded-lg border border-gray-200 bg-white p-2 shadow-sm">
          <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
            Settings
          </div>
          <div className="space-y-1">
            {items.map((item) => {
              const active =
                item.href === "/settings"
                  ? pathname === "/settings"
                  : pathname.startsWith(item.href);

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`block rounded-md px-3 py-2.5 transition-colors ${
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <div className="text-sm font-medium">{item.label}</div>
                  <div className="mt-0.5 text-xs text-gray-500">
                    {item.description}
                  </div>
                </Link>
              );
            })}
          </div>
        </nav>
      </aside>

      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
