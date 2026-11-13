import { NextResponse } from "next/server";
import { checkPassword, createSession } from "@/lib/auth";

export async function POST(request: Request) {
  const { password } = await request.json();
  if (!checkPassword(password)) {
    return NextResponse.json({ message: "Sai mật khẩu." }, { status: 401 });
  }
  return NextResponse.json({ session: createSession() });
}
