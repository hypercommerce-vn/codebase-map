import type { RevenueRow } from "@/lib/reports";

function barWidth(row: RevenueRow, max: number): string {
  return max === 0 ? "0%" : `${Math.round((row.totalVnd / max) * 100)}%`;
}

export default function RevenueChart({ rows }: { rows: RevenueRow[] }) {
  const max = Math.max(0, ...rows.map((r) => r.totalVnd));
  return (
    <ul>
      {rows.map((row) => (
        <li key={row.day}>
          {row.day}: {row.totalVnd.toLocaleString("vi-VN")}đ
          <span
            style={{
              display: "inline-block",
              width: barWidth(row, max),
              height: 8,
              background: "#3E7C5A",
            }}
          />
        </li>
      ))}
    </ul>
  );
}
