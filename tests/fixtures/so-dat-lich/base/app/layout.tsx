import type { ReactNode } from "react";

export const metadata = { title: "Sổ đặt lịch — Tiệm tóc Mộc" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
