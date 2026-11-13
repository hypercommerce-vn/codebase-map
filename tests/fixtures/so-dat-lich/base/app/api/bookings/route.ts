import { NextResponse } from "next/server";
import { createBooking, listBookingsByCustomer } from "@/lib/bookings";

export async function GET(request: Request) {
  const customerId = new URL(request.url).searchParams.get("customerId") ?? "";
  return NextResponse.json(listBookingsByCustomer(customerId));
}

export async function POST(request: Request) {
  const { customerId, serviceId, startsAt } = await request.json();
  try {
    return NextResponse.json(createBooking(customerId, serviceId, startsAt), { status: 201 });
  } catch (error) {
    return NextResponse.json({ message: (error as Error).message }, { status: 409 });
  }
}
