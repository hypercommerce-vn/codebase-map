"use client";

import { useEffect, useState } from "react";
import type { Booking } from "@/lib/types";

export default function BookingList() {
  const [bookings, setBookings] = useState<Booking[]>([]);

  useEffect(() => {
    fetch("/api/bookings?customerId=me")
      .then((res) => res.json())
      .then(setBookings);
  }, []);

  if (bookings.length === 0) {
    return <p>Bạn chưa có lịch hẹn nào.</p>;
  }

  return (
    <ul>
      {bookings.map((b) => (
        <li key={b.id}>
          {new Date(b.startsAt).toLocaleString("vi-VN")} —{" "}
          {b.status === "done" ? "Đã xong" : "Sắp tới"}
        </li>
      ))}
    </ul>
  );
}
