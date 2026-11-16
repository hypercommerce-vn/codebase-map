import RevenueChart from "@/components/RevenueChart";
import { revenueByRange } from "@/lib/reports";

function lastSevenDays(today: Date): string[] {
  const days: string[] = [];
  for (let back = 6; back >= 0; back -= 1) {
    const day = new Date(today);
    day.setDate(today.getDate() - back);
    days.push(day.toISOString().slice(0, 10));
  }
  return days;
}

export default function ReportPage() {
  const rows = revenueByRange(lastSevenDays(new Date()));
  return (
    <main>
      <h1>Báo cáo doanh thu</h1>
      <RevenueChart rows={rows} />
    </main>
  );
}
