import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, CheckCircle2 } from "lucide-react";

export function ResellerSurface({ title, description, capabilities }: { title: string; description: string; capabilities: string[] }) {
  return <div className="p-6"><Card><CardHeader><CardTitle>{title}</CardTitle></CardHeader><CardContent><p className="max-w-3xl text-sm text-gray-600">{description}</p><div className="mt-6 grid gap-3 md:grid-cols-2">{capabilities.map(item => <div key={item} className="flex gap-3 rounded-lg border border-gray-100 bg-gray-50/60 p-4"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /><span className="text-sm text-gray-700">{item}</span><ArrowRight className="ml-auto h-4 w-4 shrink-0 text-gray-300" /></div>)}</div></CardContent></Card></div>;
}
