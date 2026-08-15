"use client";

import { useAuthStore } from "@/lib/auth-store";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sparkles } from "lucide-react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="hidden w-1/2 flex-col justify-between bg-brand-950 p-12 text-white lg:flex">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
            <Sparkles className="h-5 w-5" />
          </div>
          <span className="text-lg font-semibold">AI Employee Platform</span>
        </div>
        <div>
          <h2 className="text-3xl font-bold leading-tight tracking-tight">
            Hire AI employees
            <br />
            that actually work.
          </h2>
          <p className="mt-4 max-w-md text-brand-200">
            Define roles, upload data, run tasks, and get reproducible results
            with full cost and trace visibility.
          </p>
        </div>
        <p className="text-sm text-brand-400">© 2026 AI Employee Platform</p>
      </div>

      {/* Form panel */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
