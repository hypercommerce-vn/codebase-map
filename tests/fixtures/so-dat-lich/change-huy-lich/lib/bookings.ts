import { insertRow, newId, readAll } from "@/lib/db";
import { isSlotFree, releaseSlot, takeSlot } from "@/lib/slots";
import type { Booking } from "@/lib/types";

const CANCEL_BEFORE_MS = 2 * 60 * 60 * 1000;

export function createBooking(customerId: string, serviceId: string, startsAt: string): Booking {
  if (!isSlotFree(startsAt)) {
    throw new Error("Khung giờ này đã có người đặt.");
  }
  takeSlot(startsAt);
  return insertRow("bookings", {
    id: newId("bk"),
    customerId,
    serviceId,
    startsAt,
    status: "booked",
  });
}

export function listBookingsByCustomer(customerId: string): Booking[] {
  return readAll("bookings").filter((b) => b.customerId === customerId);
}

export function listUpcomingBookings(now: Date): Booking[] {
  return readAll("bookings").filter(
    (b) => b.status === "booked" && new Date(b.startsAt).getTime() > now.getTime(),
  );
}

export function canCancel(booking: Booking, now: Date): boolean {
  return (
    booking.status === "booked" &&
    new Date(booking.startsAt).getTime() - now.getTime() > CANCEL_BEFORE_MS
  );
}

export function cancelBooking(id: string, now: Date): Booking {
  const booking = readAll("bookings").find((b) => b.id === id);
  if (!booking) {
    throw new Error("Không tìm thấy lịch hẹn.");
  }
  if (!canCancel(booking, now)) {
    throw new Error("Chỉ huỷ được trước giờ hẹn ít nhất 2 tiếng.");
  }
  booking.status = "cancelled";
  releaseSlot(booking.startsAt);
  return booking;
}
