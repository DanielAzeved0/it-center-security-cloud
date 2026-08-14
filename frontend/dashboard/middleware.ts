import { NextRequest, NextResponse } from "next/server";

const SESSION_COOKIE_NAME = "itcenter_session";

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has(SESSION_COOKIE_NAME);

  if (!hasSession) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/machines", "/machines/:path*", "/alerts", "/security", "/executive"],
};
