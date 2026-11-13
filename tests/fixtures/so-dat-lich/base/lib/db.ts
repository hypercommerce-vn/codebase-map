import type { Booking, Customer, Service, Slot } from "@/lib/types";

type Tables = {
  bookings: Booking[];
  customers: Customer[];
  services: Service[];
  slots: Slot[];
};

const tables: Tables = {
  bookings: [],
  customers: [],
  services: [
    { id: "cat-toc", name: "Cắt tóc", priceVnd: 120000, minutes: 30 },
    { id: "goi-dau", name: "Gội đầu", priceVnd: 60000, minutes: 20 },
    { id: "nhuom", name: "Nhuộm", priceVnd: 450000, minutes: 90 },
  ],
  slots: [],
};

export function readAll<K extends keyof Tables>(table: K): Tables[K] {
  return tables[table];
}

export function insertRow<K extends keyof Tables>(
  table: K,
  row: Tables[K][number],
): Tables[K][number] {
  (tables[table] as Tables[K][number][]).push(row);
  return row;
}

export function newId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}
