import { NextRequest, NextResponse } from "next/server";

const ITCENTER_API_BASE_URL = process.env.ITCENTER_API_BASE_URL ?? "http://127.0.0.1:8000";

const SESSION_COOKIE_NAME = "itcenter_session";

const ALLOWED_PATH_PREFIXES = [
  "api/v1/health",
  "api/v1/auth/login",
  "api/v1/auth/me",
  "api/v1/auth/logout",
  "api/v1/machines",
  "api/v1/alerts",
  "api/v1/security-events",
  "api/v1/dashboard",
  "api/v1/reports",
];

function isAllowedPath(joinedPath: string): boolean {
  return ALLOWED_PATH_PREFIXES.some(
    (prefix) => joinedPath === prefix || joinedPath.startsWith(`${prefix}/`),
  );
}

/**
 * Next.js already runs decodeURIComponent() on each catch-all `[...path]`
 * segment before this handler ever sees it. That means an encoded separator
 * inside a single raw URL segment (e.g. "machines%2f..%2f..%2f..%2fdocs")
 * arrives here as ONE array element containing literal "/" and ".."
 * characters — `segments.join("/")` would then produce a path that still
 * starts with an allowed prefix, even though it actually points somewhere
 * else entirely once `new URL()` normalizes the ".." later in
 * `fetchUpstream()`.
 *
 * To close that gap we re-split every decoded segment on its real
 * separators BEFORE the allowlist check, and reject outright if any
 * resulting logical component is empty, "." or "..". We split on both
 * "/" and "\" because the WHATWG URL parser used by `new URL()` treats a
 * backslash exactly like a forward slash for special schemes (http/https),
 * so a backslash-smuggled ".." (from "%5c") would bypass a forward-slash-only
 * check just the same.
 *
 * Returns null when the path must be rejected.
 */
function toSafeSegments(rawSegments: string[]): string[] | null {
  const segments: string[] = [];

  for (const rawSegment of rawSegments) {
    for (const part of rawSegment.split(/[/\\]/)) {
      if (part === "" || part === "." || part === "..") {
        return null;
      }
      segments.push(part);
    }
  }

  return segments;
}

function isSecureRequest(request: NextRequest): boolean {
  const forwardedProto = request.headers.get("x-forwarded-proto");
  return forwardedProto ? forwardedProto === "https" : request.nextUrl.protocol === "https:";
}

function withSessionCookie(
  response: NextResponse,
  request: NextRequest,
  token: string,
  maxAge?: number,
): NextResponse {
  response.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "strict",
    path: "/",
    maxAge,
  });
  return response;
}

function withClearedSessionCookie(response: NextResponse, request: NextRequest): NextResponse {
  response.cookies.set(SESSION_COOKIE_NAME, "", {
    httpOnly: true,
    secure: isSecureRequest(request),
    sameSite: "strict",
    path: "/",
    maxAge: 0,
  });
  return response;
}

function fetchUpstream(
  request: NextRequest,
  joinedPath: string,
  body: string | undefined,
  sessionToken: string | undefined,
) {
  const upstreamUrl = new URL(`/${joinedPath}`, ITCENTER_API_BASE_URL);
  upstreamUrl.search = request.nextUrl.search;

  return fetch(upstreamUrl, {
    method: request.method,
    headers: {
      "Content-Type": request.headers.get("Content-Type") ?? "application/json",
      ...(sessionToken ? { Authorization: `Bearer ${sessionToken}` } : {}),
    },
    body,
    cache: "no-store",
  });
}

async function relay(response: Response): Promise<NextResponse> {
  const responseBody = await response.arrayBuffer();
  const headers: Record<string, string> = {
    "Content-Type": response.headers.get("Content-Type") ?? "application/json",
  };

  const contentDisposition = response.headers.get("Content-Disposition");
  if (contentDisposition) {
    headers["Content-Disposition"] = contentDisposition;
  }

  return new NextResponse(responseBody, {
    status: response.status,
    headers,
  });
}

async function handleLogin(
  request: NextRequest,
  joinedPath: string,
  body: string | undefined,
): Promise<NextResponse> {
  const response = await fetchUpstream(request, joinedPath, body, undefined);

  if (!response.ok) {
    return relay(response);
  }

  const payload = (await response.json()) as {
    access_token?: string;
    expires_in?: number;
    user?: unknown;
  };

  if (!payload.access_token) {
    return NextResponse.json({ detail: "Unexpected login response" }, { status: 502 });
  }

  return withSessionCookie(
    NextResponse.json({ user: payload.user }),
    request,
    payload.access_token,
    payload.expires_in,
  );
}

async function handleLogout(
  request: NextRequest,
  joinedPath: string,
  body: string | undefined,
  sessionToken: string | undefined,
): Promise<NextResponse> {
  try {
    const response = await fetchUpstream(request, joinedPath, body, sessionToken);
    return withClearedSessionCookie(await relay(response), request);
  } catch {
    return withClearedSessionCookie(
      NextResponse.json({ status: "success", message: "Logged out" }),
      request,
    );
  }
}

async function proxyRequest(request: NextRequest, rawSegments: string[]): Promise<NextResponse> {
  const segments = toSafeSegments(rawSegments);

  if (!segments) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const joinedPath = segments.join("/");

  if (!isAllowedPath(joinedPath)) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const sessionToken = request.cookies.get(SESSION_COOKIE_NAME)?.value;

  if (joinedPath === "api/v1/auth/login") {
    return handleLogin(request, joinedPath, body);
  }

  if (joinedPath === "api/v1/auth/logout") {
    return handleLogout(request, joinedPath, body, sessionToken);
  }

  return relay(await fetchUpstream(request, joinedPath, body, sessionToken));
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}

export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  return proxyRequest(request, path);
}
