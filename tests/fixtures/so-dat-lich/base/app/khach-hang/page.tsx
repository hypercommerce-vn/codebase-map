import CustomerTable from "@/components/CustomerTable";
import { listCustomers } from "@/lib/customers";

export default function CustomersPage() {
  return (
    <main>
      <h1>Danh sách khách</h1>
      <CustomerTable customers={listCustomers()} />
    </main>
  );
}
