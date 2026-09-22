"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { listEmployeeTemplates, installEmployeeTemplate, getErrorMessage } from "@/lib/api";
import { useRouter } from "next/navigation";
import { useI18n } from "@/lib/i18n/provider";

export default function TemplatesPage() {
  const { t, locale } = useI18n();
  const tx = t.employee;
  const q = useQuery({ queryKey: ["employee-templates"], queryFn: listEmployeeTemplates });
  const qc = useQueryClient();
  const router = useRouter();
  const install = useMutation({
    mutationFn: installEmployeeTemplate,
    onSuccess: (employee) => {
      void qc.invalidateQueries({ queryKey: ["employees"] });
      router.push(`/employees/${employee.id}`);
    },
  });

  return (
    <>
      <Header title={tx.templates} description={tx.templatesDescription} />
      <div className="grid gap-4 p-6 md:grid-cols-2 xl:grid-cols-3" dir="auto">
        {q.isLoading && (
          <Card>
            <CardContent className="flex items-center gap-2 p-6 text-sm text-gray-500">
              <Spinner />
              {tx.loading}
            </CardContent>
          </Card>
        )}

        {q.error && (
          <Card>
            <CardContent className="space-y-2 p-6 text-sm text-red-600">
              <p>{getErrorMessage(q.error)}</p>
              <Button variant="secondary" onClick={() => void q.refetch()}>
                {tx.retry}
              </Button>
            </CardContent>
          </Card>
        )}

        {install.error && (
          <Card className="border-red-200 bg-red-50 md:col-span-2 xl:col-span-3">
            <CardContent className="flex items-center justify-between gap-3 p-4 text-sm text-red-700">
              <span>{getErrorMessage(install.error)}</span>
              <Button variant="secondary" onClick={() => install.reset()}>
                {tx.retry}
              </Button>
            </CardContent>
          </Card>
        )}

        {(q.data ?? []).map((template) => {
          const name = locale === "fa" ? template.name_fa : template.name;
          const description = locale === "fa" ? template.description_fa : template.description;
          const purpose = locale === "fa" ? template.purpose_fa : template.purpose;
          const category = locale === "fa" ? template.category_fa : template.category;
          const inputContract = locale === "fa" ? template.input_contract_fa : template.input_contract;
          const outputContract = locale === "fa" ? template.output_contract_fa : template.output_contract;
          const dependencies = locale === "fa" ? template.dependencies_fa : template.dependencies;
          const example = locale === "fa" ? template.example_fa : template.example;

          return (
            <Card key={template.code} className="flex h-full flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle>{name}</CardTitle>
                    <p className="mt-1 text-xs text-gray-500">{category}</p>
                  </div>
                  <span className="shrink-0 rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                    v{template.version}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-4">
                <p className="text-sm text-gray-600">{description}</p>

                <div>
                  <p className="text-xs font-semibold text-gray-700">{tx.templatePurpose}</p>
                  <p className="mt-1 text-sm text-gray-600">{purpose}</p>
                </div>

                <div className="grid gap-3 text-xs text-gray-600">
                  <div>
                    <p className="font-semibold text-gray-700">{tx.templateTools}</p>
                    <p className="mt-1 break-words">{template.allowed_tools.join(", ") || "—"}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">{tx.templateDependencies}</p>
                    <p className="mt-1">{dependencies.join(" · ") || "—"}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">{tx.templateInput}</p>
                    <p className="mt-1">{inputContract}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">{tx.templateOutput}</p>
                    <p className="mt-1">{outputContract}</p>
                  </div>
                  <div>
                    <p className="font-semibold text-gray-700">{tx.templateExample}</p>
                    <p className="mt-1">{example}</p>
                  </div>
                  <p className="text-gray-500">
                    {tx.templateCompatibility}: {template.min_platform_version}
                  </p>
                </div>

                <Button
                  className="mt-auto w-full"
                  onClick={() => install.mutate(template.code)}
                  loading={install.isPending}
                >
                  {tx.installTemplate}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </>
  );
}
