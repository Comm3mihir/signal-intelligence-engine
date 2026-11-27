const renderBackend = "https://signal-intelligence-engine.onrender.com";
const configuredBackend = process.env.NEXT_PUBLIC_API_URL?.trim().replace(/\/+$/, "");
const localHosts = new Set(["localhost", "127.0.0.1", "0.0.0.0", "[::1]"]);

export function apiUrl(path: string): string {
  if (configuredBackend) return `${configuredBackend}${path}`;

  const local = typeof window === "undefined" || localHosts.has(window.location.hostname);
  if (local) return path === "/" ? "/backend-health" : path;

  return `${renderBackend}${path}`;
}
