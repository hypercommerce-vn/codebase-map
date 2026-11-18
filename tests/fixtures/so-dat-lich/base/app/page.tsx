import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>Tiệm tóc Mộc</h1>
      <ul>
        <li>
          <Link href="/dat-lich">Đặt lịch</Link>
        </li>
        <li>
          <Link href="/lich-cua-toi">Lịch của tôi</Link>
        </li>
        <li>
          <Link href="/dang-nhap">Chủ tiệm đăng nhập</Link>
        </li>
      </ul>
    </main>
  );
}
