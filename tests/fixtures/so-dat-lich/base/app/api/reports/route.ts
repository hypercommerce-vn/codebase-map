import { NextResponse } from "next/server";
import { isOwner } from "@/lib/auth";
import { revenueByDay } from "@/lib/reports";

export async function GET(request: Request) {
  if (!isOwner(request.headers.get("x-session"))) {
    return NextResponse.json({ message: "Chỉ chủ tiệm mới xem được." }, { status: 401 });
  }
  const day = new URL(request.url).searchParams.get("day") ?? "";
  return NextResponse.json(revenueByDay(day));
}
