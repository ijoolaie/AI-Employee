"use client";

import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bot, BookOpen, Brain, MessageCircle, Workflow, Code2, ArrowRight, Sparkles, Radio, Activity } from "lucide-react";
import Link from "next/link";

const items = [
  { href: "/employees", title: "AI Employees", text: "Create, configure, version and publish your digital employees.", icon: Bot },
  { href: "/conversations", title: "Customer Conversations", text: "Review conversations between your customers and AI Employees.", icon: MessageCircle },
  { href: "/knowledge", title: "Knowledge Base", text: "Manage the information your employees use to answer customers.", icon: BookOpen },
  { href: "/memory", title: "Memory", text: "Control employee memory and customer context.", icon: Brain },
  { href: "/workflows", title: "Workflows", text: "Automate multi-step sales and operational processes.", icon: Workflow },
  { href: "/channels", title: "Customer Channels", text: "Publish web chat and website widgets for your customers.", icon: Radio },
  { href: "/developer", title: "Developer", text: "Connect external systems, APIs and integrations.", icon: Code2 },
];

export default function AIWorkspacePage() {
  return <>
    <Header title="AI Workspace" description="Build, publish and operate your AI Employees." />
    <div className="space-y-6 p-6">
      <Card className="overflow-hidden border-brand-100 bg-brand-50/50">
        <CardContent className="flex flex-col gap-5 p-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-4">
            <div className="rounded-xl bg-brand-600 p-3 text-white"><Sparkles className="h-6 w-6" /></div>
            <div>
              <p className="text-lg font-semibold text-gray-900">Your AI Employee workspace</p>
              <p className="mt-1 max-w-2xl text-sm text-gray-600">Configure an employee, connect its knowledge and tools, publish a customer channel, then monitor the conversations it handles.</p>
            </div>
          </div>
          <Link href="/employees/new" className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700">Create employee <ArrowRight className="h-4 w-4" /></Link>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center gap-3 pb-2"><div className="rounded-lg bg-brand-50 p-2.5 text-brand-600"><Activity className="h-5 w-5" /></div><div><CardTitle className="text-base">Execution Workspace</CardTitle><p className="text-sm text-gray-500">Unified execution status, approvals and evidence.</p></div></CardHeader>
        <CardContent><div className="grid gap-3 sm:grid-cols-3"><div className="rounded-lg border p-3"><p className="text-xs text-gray-500">Execution model</p><p className="mt-1 font-medium">Unified WorkItem</p></div><div className="rounded-lg border p-3"><p className="text-xs text-gray-500">Safety</p><p className="mt-1 font-medium">Tenant scoped</p></div><div className="rounded-lg border p-3"><p className="text-xs text-gray-500">Evidence</p><p className="mt-1 font-medium">Correlated</p></div></div></CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map(({ href, title, text, icon: Icon }) => <Link key={href} href={href} className="group">
          <Card className="h-full transition group-hover:-translate-y-0.5 group-hover:border-brand-200 group-hover:shadow-sm">
            <CardHeader className="flex flex-row items-center gap-3 pb-2"><div className="rounded-lg bg-brand-50 p-2.5 text-brand-600"><Icon className="h-5 w-5" /></div><CardTitle className="text-base">{title}</CardTitle></CardHeader>
            <CardContent><p className="text-sm leading-6 text-gray-500">{text}</p><p className="mt-4 text-sm font-medium text-brand-600">Open →</p></CardContent>
          </Card>
        </Link>)}
      </div>
    </div>
  </>;
}
