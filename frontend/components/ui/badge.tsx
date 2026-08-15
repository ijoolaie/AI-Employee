import { cn, statusColor } from "@/lib/utils";
import { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status?: string;
}

export function Badge({ className, status, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        status ? statusColor(status) : "bg-gray-100 text-gray-700",
        className
      )}
      {...props}
    >
      {children ?? status}
    </span>
  );
}
