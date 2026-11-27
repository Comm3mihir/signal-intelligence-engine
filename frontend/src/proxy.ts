import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  if (process.env.SIGNAL_ENV !== "production" && !process.env.VERCEL) return NextResponse.next();
  const password = process.env.SIGNAL_WORKSPACE_PASSWORD;
  if (!password) return new NextResponse("Workspace access is not configured.", { status: 503 });
  const username = process.env.SIGNAL_WORKSPACE_USER || "signal";
  const bytes = new TextEncoder().encode(`${username}:${password}`);
  const expected = "Basic " + btoa(String.fromCharCode(...Array.from(bytes)));
  const supplied = request.headers.get("authorization") || "";
  let differences = supplied.length ^ expected.length;
  for (let index = 0; index < expected.length; index += 1) {
    differences |= expected.charCodeAt(index) ^ (supplied.charCodeAt(index) || 0);
  }
  if (differences === 0) return NextResponse.next();
  return new NextResponse("Workspace sign-in required.", {
    status: 401, headers: { "WWW-Authenticate": 'Basic realm="SIGNAL"', "Cache-Control": "no-store" },
  });
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] };
