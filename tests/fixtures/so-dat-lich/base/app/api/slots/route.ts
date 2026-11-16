import { NextResponse } from "next/server";
import { listSlots } from "@/lib/slots";

export async function GET(request: Request) {
  const day = new URL(request.url).searchParams.get("day") ?? "";
  return NextResponse.json(listSlots(day));
}
