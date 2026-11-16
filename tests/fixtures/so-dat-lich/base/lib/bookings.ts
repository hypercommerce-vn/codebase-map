import { insertRow, newId, readAll } from "@/lib/db";
import { isSlotFree, takeSlot } from "@/lib/slots";
import type { Booking } from "@/lib/types";

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
