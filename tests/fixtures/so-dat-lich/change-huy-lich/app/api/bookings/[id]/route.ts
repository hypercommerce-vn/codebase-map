import { NextResponse } from "next/server";
import { cancelBooking } from "@/lib/bookings";

export async function DELETE(_request: Request, { params }: { params: { id: string } }) {
  try {
    return NextResponse.json(cancelBooking(params.id, new Date()));
  } catch (error) {
    return NextResponse.json({ message: (error as Error).message }, { status: 409 });
  }
}
