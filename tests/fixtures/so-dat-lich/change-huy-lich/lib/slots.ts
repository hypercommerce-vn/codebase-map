import { insertRow, readAll } from "@/lib/db";
import type { Slot } from "@/lib/types";

const OPEN_HOUR = 9;
const CLOSE_HOUR = 19;

export function listSlots(day: string): Slot[] {
  const taken = new Set(
    readAll("slots")
      .filter((s) => s.taken)
      .map((s) => s.startsAt),
  );
  const slots: Slot[] = [];
  for (let hour = OPEN_HOUR; hour < CLOSE_HOUR; hour += 1) {
    const startsAt = `${day}T${String(hour).padStart(2, "0")}:00:00`;
    slots.push({ startsAt, taken: taken.has(startsAt) });
  }
  return slots;
}

export function isSlotFree(startsAt: string): boolean {
  return !readAll("slots").some((s) => s.startsAt === startsAt && s.taken);
}

export function takeSlot(startsAt: string): void {
  insertRow("slots", { startsAt, taken: true });
}

export function releaseSlot(startsAt: string): void {
  const slot = readAll("slots").find((s) => s.startsAt === startsAt && s.taken);
  if (slot) {
    slot.taken = false;
  }
}
