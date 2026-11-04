"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage, register as registerApi } from "@/lib/api";

const schema = z.object({
  tenant_name: z.string().min(2, "At least 2 characters"),
  tenant_slug: z
    .string()
    .min(2)
    .regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, hyphens only"),
  full_name: z.string().optional(),
  email: z.string().email(),
  password: z.string().min(8, "At least 8 characters"),
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  async function onSubmit(data: FormData) {
    setError(null);
    setSuccess(null);
    try {
      const result = await registerApi(data);
      setSuccess(result.message);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Create account</h1>
      <p className="mt-1 text-sm text-gray-500">
        Set up your organization. Access is enabled after an approved payment or operator Demo grant.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4">
        <Input
          label="Organization name"
          placeholder="Acme Corp"
          error={errors.tenant_name?.message}
          {...register("tenant_name")}
        />
        <Input
          label="Tenant slug"
          placeholder="acme-corp"
          hint="Used in login. Lowercase, numbers, hyphens."
          error={errors.tenant_slug?.message}
          {...register("tenant_slug")}
        />
        <Input
          label="Your name"
          placeholder="Jane Doe"
          error={errors.full_name?.message}
          {...register("full_name")}
        />
        <Input
          label="Email"
          type="email"
          placeholder="you@company.com"
          error={errors.email?.message}
          {...register("email")}
        />
        <Input
          label="Password"
          type="password"
          placeholder="Min. 8 characters"
          error={errors.password?.message}
          {...register("password")}
        />

        {success && (
          <div className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
            {success} You can sign in after access is enabled.
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <Button type="submit" className="w-full" loading={isSubmitting}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-brand-600 hover:text-brand-700"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
