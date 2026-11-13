"use client";

import { useState } from "react";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const res = await fetch("/api/auth", {
      method: "POST",
      body: JSON.stringify({ password }),
    });
    setError(res.ok ? "" : "Sai mật khẩu.");
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Chủ tiệm đăng nhập</h1>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Đăng nhập</button>
      {error && <p>{error}</p>}
    </form>
  );
}
