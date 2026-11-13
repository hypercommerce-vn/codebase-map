import BookingForm from "@/components/BookingForm";
import { readAll } from "@/lib/db";

export default function BookingPage() {
  const services = readAll("services");
  return (
    <main>
      <h1>Đặt lịch</h1>
      <BookingForm services={services} />
    </main>
  );
}
