"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { LifeBuoy } from "lucide-react";
import { ResellerSurface } from "@/components/reseller/reseller-surface";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { createResellerSupportEscalation } from "@/lib/api";
import { useI18n } from "@/lib/i18n/provider";

export default function ResellerSupportPage() {
  const { locale } = useI18n();
  const fa = locale === "fa";
  const m = fa
    ? {
        title: "مرکز پشتیبانی مشتری",
        description: "ثبت و ارجاع رسمی مسئله از نماینده به پشتیبانی پلتفرم، با ثبت رویداد حسابرسی.",
        form: "ارجاع به پشتیبانی پلتفرم",
        subject: "موضوع",
        subjectPlaceholder: "موضوع مسئله",
        descriptionLabel: "شرح",
        descriptionPlaceholder: "شرح مسئله و زمینه لازم برای بررسی",
        submit: "ثبت ارجاع",
        submitting: "در حال ثبت…",
        success: "ارجاع با موفقیت ثبت شد.",
        error: "ثبت ارجاع انجام نشد.",
      }
    : {
        title: "Client Support",
        description: "Create an official reseller-to-platform support escalation with an auditable record.",
        form: "Escalate to Platform Support",
        subject: "Subject",
        subjectPlaceholder: "Issue subject",
        descriptionLabel: "Description",
        descriptionPlaceholder: "Describe the issue and relevant context",
        submit: "Create escalation",
        submitting: "Creating…",
        success: "Escalation created successfully.",
        error: "Could not create escalation.",
      };

  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const mutation = useMutation({
    mutationFn: () => createResellerSupportEscalation({ subject: subject.trim(), description: description.trim() }),
    onSuccess: () => {
      setSubject("");
      setDescription("");
    },
  });

  return (
    <>
      <ResellerSurface
        title={m.title}
        description={m.description}
        capabilities={
          fa
            ? ["ثبت ارجاع پشتیبانی پلتفرم", "ثبت زمینه و شرح مسئله", "ثبت رویداد حسابرسی"]
            : ["Platform support escalation", "Structured issue context", "Auditable escalation record"]
        }
      />
      <div className="space-y-4 p-6 pt-0">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LifeBuoy className="h-5 w-5" />
              {m.form}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="reseller-support-subject">{m.subject}</label>
              <input
                id="reseller-support-subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder={m.subjectPlaceholder}
                className="w-full rounded-md border px-3 py-2 text-sm"
                maxLength={255}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium" htmlFor="reseller-support-description">{m.descriptionLabel}</label>
              <textarea
                id="reseller-support-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder={m.descriptionPlaceholder}
                className="min-h-32 w-full rounded-md border px-3 py-2 text-sm"
                maxLength={10000}
              />
            </div>
            {mutation.isSuccess && <p className="text-sm text-green-600">{m.success}</p>}
            {mutation.isError && <p className="text-sm text-red-600">{m.error}</p>}
            <Button
              disabled={mutation.isPending || subject.trim().length < 3 || description.trim().length < 5}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? m.submitting : m.submit}
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
