"use client";

import Link from "next/link";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuthStore } from "@/lib/auth-store";

export default function SettingsPage() {
  const { user, tenant } = useAuthStore();

  return (
    <>
      <Header
        title="Settings"
        description="Account and organization details"
      />
      <div className="mx-auto max-w-2xl space-y-6 p-6">
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Email" value={user?.email} />
            <Row label="Full name" value={user?.full_name || "—"} />
            <Row label="User ID" value={user?.id} mono />
            <Row
              label="Status"
              value={user?.is_active ? "Active" : "Inactive"}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Name" value={tenant?.name} />
            <Row label="Slug" value={tenant?.slug} mono />
            <Row label="Tenant ID" value={tenant?.id} mono />
            <Row label="Status" value={tenant?.status} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Related</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p className="text-gray-600">
              Billing and usage are managed on their own pages:
            </p>
            <ul className="list-inside list-disc space-y-1 text-brand-700">
              <li>
                <Link href="/billing" className="hover:underline">
                  Billing &amp; plans
                </Link>
              </li>
              <li>
                <Link href="/usage" className="hover:underline">
                  Usage &amp; quotas
                </Link>
              </li>
              <li>
                <Link href="/knowledge" className="hover:underline">
                  Knowledge base (RAG)
                </Link>
              </li>
              <li>
                <Link href="/memory" className="hover:underline">
                  Employee memory
                </Link>
              </li>
              <li>
                <Link href="/team" className="hover:underline">
                  Team &amp; roles
                </Link>
              </li>
            </ul>
            <p className="pt-2 text-xs text-gray-400">Team and role administration is available for tenant administrators.</p>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-gray-50 pb-2 last:border-0 last:pb-0">
      <span className="text-gray-500">{label}</span>
      <span
        className={
          mono
            ? "truncate font-mono text-xs text-gray-700"
            : "truncate font-medium text-gray-900"
        }
      >
        {value ?? "—"}
      </span>
    </div>
  );
}
