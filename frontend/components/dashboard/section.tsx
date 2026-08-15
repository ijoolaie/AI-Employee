import type { ReactNode } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DashboardSection({ title, description, action, children }: { title: string; description?: string; action?: ReactNode; children: ReactNode }) {
  return <Card><CardHeader><div><CardTitle>{title}</CardTitle>{description && <p className="mt-1 text-xs text-gray-500">{description}</p>}</div>{action}</CardHeader><CardContent>{children}</CardContent></Card>;
}
