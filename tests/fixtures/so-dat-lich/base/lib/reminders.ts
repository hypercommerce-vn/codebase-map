import { listUpcomingBookings } from "@/lib/bookings";
import { findCustomer } from "@/lib/customers";
import type { Booking } from "@/lib/types";

const REMIND_BEFORE_MS = 24 * 60 * 60 * 1000;

export function dueReminders(now: Date): Booking[] {
  return listUpcomingBookings(now).filter(
    (b) => new Date(b.startsAt).getTime() - now.getTime() <= REMIND_BEFORE_MS,
  );
}

export function buildReminderMessage(booking: Booking, customerName: string): string {
  const time = new Date(booking.startsAt).toLocaleString("vi-VN");
  return `Chào ${customerName}, tiệm tóc Mộc nhắc bạn có lịch hẹn lúc ${time}.`;
}

function sendSms(phone: string, text: string): void {
  console.log(`[SMS] ${phone}: ${text}`);
}

export function sendReminders(now: Date): number {
  let sent = 0;
  for (const booking of dueReminders(now)) {
    const customer = findCustomer(booking.customerId);
    if (!customer) continue;
    sendSms(customer.phone, buildReminderMessage(booking, customer.name));
    sent += 1;
  }
  return sent;
}
