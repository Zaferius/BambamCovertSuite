export async function authFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const token = typeof window !== "undefined" ? localStorage.getItem("bambam_token") : null;
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
    localStorage.removeItem("bambam_token");
    localStorage.removeItem("bambam_user");
    window.location.reload();
  }

  return response;
}
