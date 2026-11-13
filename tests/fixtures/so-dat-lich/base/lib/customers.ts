import { insertRow, newId, readAll } from "@/lib/db";
import type { Customer } from "@/lib/types";

export function listCustomers(): Customer[] {
  return [...readAll("customers")].sort((a, b) => a.name.localeCompare(b.name, "vi"));
}

export function findCustomer(id: string): Customer | undefined {
  return readAll("customers").find((c) => c.id === id);
}

export function saveCustomer(name: string, phone: string, note?: string): Customer {
  return insertRow("customers", { id: newId("kh"), name, phone, note });
}
