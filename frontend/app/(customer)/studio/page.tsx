"use client";

import { useState, type ReactNode } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { createEmployee, getErrorMessage, listAvailableTools, listEmployees } from "@/lib/api";
import { Bot, Check, Code2, Save, ShieldCheck, SlidersHorizontal, Wrench } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";

export default function StudioPage() {
  const { t } = useI18n();
  const m = t.studio;
  const employees = useQuery({ queryKey: ["employees"], queryFn: listEmployees });
  const tools = useQuery({ queryKey: ["available-tools"], queryFn: listAvailableTools });
  const [name,setName]=useState(""); const [slug,setSlug]=useState(""); const [kind,setKind]=useState("assistant"); const [prompt,setPrompt]=useState("You are a reliable AI employee. Complete the user's task accurately and explain important decisions."); const [selectedTools,setSelectedTools]=useState<string[]>([]); const [autonomy,setAutonomy]=useState(true); const [maxSteps,setMaxSteps]=useState(6); const [requirePlan,setRequirePlan]=useState(true); const [outputSchema,setOutputSchema]=useState('{\n  "result": "string"\n}');
  const create = useMutation({ mutationFn: () => createEmployee({ slug: slug.trim(), name: name.trim(), kind, prompt_template: prompt, allowed_tools: selectedTools, output_schema: JSON.parse(outputSchema), rules: { autonomy: { enabled: autonomy, max_steps: maxSteps, require_plan: requirePlan }, memory: { enabled: true, auto_extract: true, query_fields: ["message"] } } }), onSuccess: () => employees.refetch() });
  const existing = employees.data ?? [];
  const toggle = (n:string) => setSelectedTools(v => v.includes(n) ? v.filter(x=>x!==n) : [...v,n]);
  const invalid = !name.trim() || !slug.trim() || !prompt.trim() || create.isPending;
  return <>
    <Header title={m.title} description={m.description} />
    <div className="grid gap-6 p-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Bot className="h-4 w-4 text-brand-600"/>{m.employeeDefinition}</CardTitle></CardHeader><CardContent className="grid gap-4 sm:grid-cols-2"><Field label={m.name}><input value={name} onChange={e=>setName(e.target.value)} placeholder={m.namePlaceholder}/></Field><Field label={m.slug}><input value={slug} onChange={e=>setSlug(e.target.value)} placeholder={m.slugPlaceholder}/></Field><Field label={m.kind}><select value={kind} onChange={e=>setKind(e.target.value)}><option>assistant</option><option>analyst</option><option>sales</option><option>operations</option><option>support</option></select></Field><div className="rounded-xl bg-gray-50 p-4 text-sm"><p className="font-medium text-gray-800">{m.runtime}</p><p className="mt-1 text-xs text-gray-500">{m.runtimeDescription}</p></div></CardContent></Card>
        <Card><CardHeader><CardTitle>{m.systemPrompt}</CardTitle></CardHeader><CardContent><textarea value={prompt} onChange={e=>setPrompt(e.target.value)} rows={9} className="w-full rounded-xl border border-gray-300 p-3 font-mono text-sm"/><div className="mt-3 flex flex-wrap gap-2"><Badge>{m.memoryAware}</Badge><Badge>{m.toolAware}</Badge><Badge>{m.tenantScoped}</Badge></div></CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Wrench className="h-4 w-4 text-brand-600"/>{m.allowedTools}</CardTitle></CardHeader><CardContent><div className="grid gap-3 sm:grid-cols-2">{tools.isLoading ? <Spinner/> : (tools.data ?? []).map(t => <button key={t.name} onClick={()=>toggle(t.name)} className={`rounded-xl border p-4 text-left transition ${selectedTools.includes(t.name)?"border-brand-400 bg-brand-50":"border-gray-200 hover:bg-gray-50"}`}><div className="flex items-center justify-between gap-2"><span className="font-medium text-sm">{t.name}</span>{selectedTools.includes(t.name)&&<Check className="h-4 w-4 text-brand-600"/>}</div><p className="mt-1 text-xs text-gray-500">{t.description}</p><p className="mt-2 text-[11px] text-gray-400">{t.side_effects?m.sideEffect:m.safeTool}</p></button>)}{!(tools.data ?? []).length && <p className="text-sm text-gray-500">{m.noTools}</p>}</div></CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><SlidersHorizontal className="h-4 w-4 text-brand-600"/>{m.autonomyMemory}</CardTitle></CardHeader><CardContent className="space-y-5"><Toggle label={m.autonomousPlanning} description={m.autonomousPlanningDescription} value={autonomy} onChange={setAutonomy}/><Toggle label={m.requirePlan} description={m.requirePlanDescription} value={requirePlan} onChange={setRequirePlan}/><Toggle label={m.autoMemory} description={m.autoMemoryDescription} value={true} onChange={()=>{}} disabled/><div><label className="text-sm font-medium">{m.maxPlanSteps} <span className="text-gray-400">({maxSteps})</span></label><input type="range" min="1" max="20" value={maxSteps} onChange={e=>setMaxSteps(Number(e.target.value))} className="mt-3 w-full"/></div></CardContent></Card>
        <Card><CardHeader><CardTitle className="flex items-center gap-2"><Code2 className="h-4 w-4"/>{m.outputSchema}</CardTitle></CardHeader><CardContent><textarea value={outputSchema} onChange={e=>setOutputSchema(e.target.value)} rows={7} className="w-full rounded-xl border border-gray-300 p-3 font-mono text-xs"/></CardContent></Card>
        <div className="flex flex-wrap items-center gap-3"><Button disabled={invalid} onClick={()=>create.mutate()}><Save className="h-4 w-4"/>{create.isPending?m.creating:m.create}</Button>{create.error&&<span className="text-sm text-red-600">{getErrorMessage(create.error)}</span>}{create.isSuccess&&<span className="text-sm text-emerald-600">{m.createdSuccess}</span>}</div>
      </div>
      <div className="space-y-6"><Card><CardHeader><CardTitle>{m.currentEmployees}</CardTitle></CardHeader><CardContent className="space-y-2">{existing.slice(0,8).map(e=><div key={e.id} className="flex items-center justify-between rounded-lg bg-gray-50 p-3"><div><p className="text-sm font-medium">{e.name}</p><p className="text-xs text-gray-500">{e.kind}</p></div><Badge status={e.is_active?"active":"inactive"}/></div>)}{!existing.length&&<p className="text-sm text-gray-500">{m.createFirst}</p>}</CardContent></Card><Card><CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-brand-600"/>{m.safetyBoundary}</CardTitle></CardHeader><CardContent className="space-y-3 text-sm text-gray-600"><p>{m.toolPermissions}</p><p>{m.sideEffectPolicy}</p><p>{m.autonomyPolicy}</p></CardContent></Card></div>
    </div>
  </>;
}
function Field({label,children}:{label:string;children:ReactNode}){return <label className="text-sm font-medium text-gray-700">{label}<div className="mt-1.5">{children}</div></label>}
function Toggle({label,description,value,onChange,disabled=false}:{label:string;description:string;value:boolean;onChange:(v:boolean)=>void;disabled?:boolean}){return <button type="button" disabled={disabled} onClick={()=>onChange(!value)} className="flex w-full items-start justify-between gap-4 rounded-xl border border-gray-200 p-4 text-left disabled:opacity-60"><span><span className="block text-sm font-medium text-gray-900">{label}</span><span className="mt-1 block text-xs leading-5 text-gray-500">{description}</span></span><span className={`mt-0.5 flex h-6 w-11 shrink-0 rounded-full p-1 transition ${value?"bg-brand-600":"bg-gray-200"}`}><span className={`h-4 w-4 rounded-full bg-white shadow transition ${value?"translate-x-5":"translate-x-0"}`}/></span></button>}
