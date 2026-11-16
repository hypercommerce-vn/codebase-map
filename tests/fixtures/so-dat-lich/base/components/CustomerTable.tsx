import type { Customer } from "@/lib/types";

export default function CustomerTable({ customers }: { customers: Customer[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Tên</th>
          <th>Số điện thoại</th>
          <th>Ghi chú</th>
        </tr>
      </thead>
      <tbody>
        {customers.map((c) => (
          <tr key={c.id}>
            <td>{c.name}</td>
            <td>{c.phone}</td>
            <td>{c.note ?? ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
