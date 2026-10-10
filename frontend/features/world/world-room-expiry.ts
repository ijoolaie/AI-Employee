export type LeaseExpiryStatus = { kind: "unknown" | "expired" | "urgent" | "active"; daysRemaining: number | null };

const DAY_MS = 24 * 60 * 60 * 1000;

export function getRoomLeaseExpiryStatus(expiresAt: string | null, now = Date.now()): LeaseExpiryStatus {
  if (!expiresAt) return { kind: "unknown", daysRemaining: null };
  const expiryTime = new Date(expiresAt).getTime();
  if (!Number.isFinite(expiryTime)) return { kind: "unknown", daysRemaining: null };
  const daysRemaining = Math.ceil((expiryTime - now) / DAY_MS);
  if (daysRemaining <= 0) return { kind: "expired", daysRemaining: 0 };
  if (daysRemaining <= 7) return { kind: "urgent", daysRemaining };
  return { kind: "active", daysRemaining };
}
