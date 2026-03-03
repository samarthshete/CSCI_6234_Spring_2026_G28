export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setAccessToken(t: string) {
  localStorage.setItem("access_token", t);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

export function setRefreshToken(t: string) {
  localStorage.setItem("refresh_token", t);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function normalizeEmail(e: string): string {
  return e.trim().toLowerCase();
}

export function validateEmail(e: string): string | null {
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) return "Invalid email address";
  return null;
}

export function validatePassword(p: string): string | null {
  if (p.length < 8) return "Password must be at least 8 characters";
  if (!/[a-zA-Z]/.test(p)) return "Password must contain at least one letter";
  if (!/\d/.test(p)) return "Password must contain at least one digit";
  return null;
}
