import { AUTH_TOKEN_STORAGE_KEY, AUTH_USER_STORAGE_KEY } from "./app-constants";

export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) : null;
  const headers = new Headers(init?.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const newInit: RequestInit = {
    ...init,
    headers,
  };

  const response = await fetch(input, newInit);

  if (response.status === 401 && typeof window !== "undefined") {
    // If token is invalid or expired, clear it
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    localStorage.removeItem(AUTH_USER_STORAGE_KEY);
    window.location.reload();
  }

  return response;
}
