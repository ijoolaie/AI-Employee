"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/settings", label: "General" },
  { href: "/settings/security", label: "Security" },
];

export default function SettingsLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-5 lg:flex-row lg:items-start lg:px-6">
      <aside className="w-full shrink-0 lg:w-52" aria-label="Settings navigation">
        <nav className="rounded-lg border border-gray-200 bg-white p-1 shadow-sm">
          <div className="space-y-0.5">
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
                  className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {item.label}
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
