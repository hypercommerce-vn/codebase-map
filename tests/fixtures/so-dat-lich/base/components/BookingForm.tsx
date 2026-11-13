"use client";

import { useState } from "react";
import SlotPicker from "@/components/SlotPicker";
import type { Service } from "@/lib/types";

export default function BookingForm({ services }: { services: Service[] }) {
  const [serviceId, setServiceId] = useState(services[0]?.id ?? "");
  const [day, setDay] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [message, setMessage] = useState("");

  async function submitBooking(event: React.FormEvent) {
    event.preventDefault();
    const res = await fetch("/api/bookings", {
      method: "POST",
      body: JSON.stringify({ customerId: "me", serviceId, startsAt }),
    });
    setMessage(res.ok ? "Đặt lịch thành công." : "Khung giờ này đã có người đặt.");
  }

  return (
    <form onSubmit={submitBooking}>
      <select value={serviceId} onChange={(e) => setServiceId(e.target.value)}>
        {services.map((s) => (
          <option key={s.id} value={s.id}>
            {s.name} — {s.priceVnd.toLocaleString("vi-VN")}đ
          </option>
        ))}
      </select>
      <input type="date" value={day} onChange={(e) => setDay(e.target.value)} />
      <SlotPicker day={day} value={startsAt} onChange={setStartsAt} />
      <button type="submit">Đặt lịch</button>
      {message && <p>{message}</p>}
    </form>
  );
}
