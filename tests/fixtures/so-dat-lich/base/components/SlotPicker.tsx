"use client";

import { useEffect, useState } from "react";
import type { Slot } from "@/lib/types";

type Props = {
  day: string;
  value: string;
  onChange: (startsAt: string) => void;
};

export default function SlotPicker({ day, value, onChange }: Props) {
  const [slots, setSlots] = useState<Slot[]>([]);

  useEffect(() => {
    fetch(`/api/slots?day=${day}`)
      .then((res) => res.json())
      .then(setSlots);
  }, [day]);

  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Chọn giờ</option>
      {slots.map((slot) => (
        <option key={slot.startsAt} value={slot.startsAt} disabled={slot.taken}>
          {slot.startsAt.slice(11, 16)} {slot.taken ? "(đã kín)" : ""}
        </option>
      ))}
    </select>
  );
}
