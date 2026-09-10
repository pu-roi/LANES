/**
 * Utility for resolving Server-Sent Events (SSE) streaming URLs.
 * 
 * In local development, direct the browser directly to the FastAPI backend
 * on port 8000 to prevent Next.js proxy chunk-buffering, premature timeouts,
 * and ECONNREFUSED terminal proxy errors.
 */
export function getSseUrl(endpoint: string): string {
  if (typeof window === "undefined") return "";

  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const apiEnv = process.env.NEXT_PUBLIC_API_URL;

  if (apiEnv && apiEnv.startsWith("http")) {
    return `${apiEnv}${cleanEndpoint}`;
  }

  // In local development or LAN testing, bypass the Next.js rewrite proxy for persistent SSE streams
  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1" ||
    window.location.hostname.startsWith("192.168.") ||
    window.location.hostname.startsWith("10.")
  ) {
    const host = window.location.hostname === "localhost" ? "127.0.0.1" : window.location.hostname;
    return `http://${host}:8000/api/v1${cleanEndpoint}`;
  }

  return `/api/v1${cleanEndpoint}`;
}
