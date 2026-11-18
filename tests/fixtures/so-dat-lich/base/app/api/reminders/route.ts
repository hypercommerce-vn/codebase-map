import { NextResponse } from "next/server";
import { sendReminders } from "@/lib/reminders";

export async function POST() {
  const sent = sendReminders(new Date());
  return NextResponse.json({ sent });
}
