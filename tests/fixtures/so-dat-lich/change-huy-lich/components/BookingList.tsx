"use client";

import { useEffect, useState } from "react";
import type { Booking } from "@/lib/types";

function statusLabel(booking: Booking): string {
  if (booking.status === "done") return "Đã xong";
  if (booking.status === "cancelled") return "Đã huỷ";
  return "Sắp tới";
}

export default function BookingList() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [message, setMessage] = useState("");

  function loadBookings() {
    fetch("/api/bookings?customerId=me")
      .then((res) => res.json())
      .then(setBookings);
  }

  useEffect(loadBookings, []);

  async function cancelBooking(id: string) {
    const res = await fetch(`/api/bookings/${id}`, { method: "DELETE" });
    if (res.ok) {
      setMessage("Đã huỷ lịch.");
      loadBookings();
    } else {
      const body = await res.json();
      setMessage(body.message);
    }
  }

  if (bookings.length === 0) {
    return <p>Bạn chưa có lịch hẹn nào.</p>;
  }

  return (
    <div>
      {message && <p>{message}</p>}
      <ul>
        {bookings.map((b) => (
          <li key={b.id}>
            {new Date(b.startsAt).toLocaleString("vi-VN")} — {statusLabel(b)}
            {b.status === "booked" && (
              <button type="button" onClick={() => cancelBooking(b.id)}>
                Huỷ lịch
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
