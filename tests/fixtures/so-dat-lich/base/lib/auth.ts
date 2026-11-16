const OWNER_PASSWORD = process.env.OWNER_PASSWORD ?? "";
const sessions = new Set<string>();

export function checkPassword(password: string): boolean {
  return OWNER_PASSWORD.length > 0 && password === OWNER_PASSWORD;
}

export function createSession(): string {
  const token = Math.random().toString(36).slice(2);
  sessions.add(token);
  return token;
}

export function isOwner(token: string | null): boolean {
  return token !== null && sessions.has(token);
}
