"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { createEmployee, getErrorMessage, listAvailableTools } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";

const schema = z.object({
  name: z.string().min(2, "Name required"),
  slug: z
    .string()
    .min(2)
    .regex(/^[a-z0-9-]+$/, "Lowercase, numbers, hyphens only"),
  prompt_template: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

export default function NewEmployeePage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const { data: availableTools = [], isLoading: toolsLoading } = useQuery({
    queryKey: ["available-tools"],
    queryFn: listAvailableTools,
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  async function onSubmit(data: FormData) {
    setError(null);
    try {
      const emp = await createEmployee({
        name: data.name,
        slug: data.slug,
        kind: "custom",
        prompt_template: data.prompt_template || undefined,
        input_schema: {},
        output_schema: {},
        allowed_tools: selectedTools,
        rules: {},
      });
      await qc.invalidateQueries({ queryKey: ["employees"] });
      router.push(`/employees/${emp.id}`);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <>
      <Header
        title="New employee"
        description="Define a custom AI employee for your organization"
      />
      <div className="mx-auto max-w-xl p-6">
        <Card>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Input
                label="Name"
                placeholder="Sales Report Analyst"
                error={errors.name?.message}
                {...register("name")}
              />
              <Input
                label="Slug"
                placeholder="sales-report-analyst"
                hint="Unique identifier within your tenant"
                error={errors.slug?.message}
                {...register("slug")}
              />
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700">Allowed tools</label>
                <p className="text-xs text-gray-500">Only tools explicitly selected here can be exposed to the AI during a Run.</p>
                {toolsLoading && <div className="text-sm text-gray-500">Loading registered tools…</div>}
                {!toolsLoading && availableTools.length === 0 && (
                  <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500">No registered tools available.</div>
                )}
                <div className="space-y-2">
                  {availableTools.map((tool) => (
                    <label key={tool.name} className="flex cursor-pointer items-start gap-3 rounded-lg border border-gray-200 p-3 hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={selectedTools.includes(tool.name)}
                        onChange={(e) => setSelectedTools((current) => e.target.checked ? [...current, tool.name] : current.filter((name) => name !== tool.name))}
                        className="mt-1"
                      />
                      <span className="min-w-0">
                        <span className="block text-sm font-medium text-gray-800">{tool.name}</span>
                        <span className="block text-xs text-gray-500">{tool.description}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-gray-700">
                  Prompt template
                </label>
                <textarea
                  className="min-h-[120px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
                  placeholder="You are a sales analyst. Analyze the provided data and produce a clear summary..."
                  {...register("prompt_template")}
                />
              </div>

              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => router.back()}
                >
                  Cancel
                </Button>
                <Button type="submit" loading={isSubmitting}>
                  Create employee
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
