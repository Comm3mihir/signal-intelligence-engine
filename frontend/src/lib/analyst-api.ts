import { apiUrl } from "./api-url";

const key = "signal.analyst.access";

export function saveAnalystToken(token: string) {
  if (token.trim()) sessionStorage.setItem(key, token.trim());
  else sessionStorage.removeItem(key);
}

export async function analystApi<T>(path: string, options?: RequestInit): Promise<T> {
  const headers = new Headers(options?.headers);
  const token = typeof window === "undefined" ? null : sessionStorage.getItem(key);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(apiUrl(path), { cache: "no-store", ...options, headers });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = typeof data?.detail === "string" ? data.detail : null;
    throw new Error(detail || (response.status === 422 ? "Check the input fields and try again." :
      `The intelligence service returned HTTP ${response.status}.`));
  }
  return response.json();
}
