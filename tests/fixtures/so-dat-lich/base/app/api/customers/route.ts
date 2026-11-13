import { NextResponse } from "next/server";
import { isOwner } from "@/lib/auth";
import { listCustomers, saveCustomer } from "@/lib/customers";

export async function GET(request: Request) {
  if (!isOwner(request.headers.get("x-session"))) {
    return NextResponse.json({ message: "Chỉ chủ tiệm mới xem được." }, { status: 401 });
  }
  return NextResponse.json(listCustomers());
}

export async function POST(request: Request) {
  const { name, phone, note } = await request.json();
  return NextResponse.json(saveCustomer(name, phone, note), { status: 201 });
}
