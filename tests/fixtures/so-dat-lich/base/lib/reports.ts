import { readAll } from "@/lib/db";

export type RevenueRow = {
  day: string;
  totalVnd: number;
  bookings: number;
};

function priceOf(serviceId: string): number {
  return readAll("services").find((s) => s.id === serviceId)?.priceVnd ?? 0;
}

export function revenueByDay(day: string): RevenueRow {
  const done = readAll("bookings").filter(
    (b) => b.status === "done" && b.startsAt.startsWith(day),
  );
  return {
    day,
    totalVnd: done.reduce((sum, b) => sum + priceOf(b.serviceId), 0),
    bookings: done.length,
  };
}

export function revenueByRange(days: string[]): RevenueRow[] {
  return days.map((day) => revenueByDay(day));
}
