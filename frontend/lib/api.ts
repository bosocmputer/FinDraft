const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }
  return res.json();
}

export const api = {
  get: (path: string, headers?: HeadersInit) => apiFetch(path, { method: "GET", headers }),
  post: (path: string, body?: unknown, headers?: HeadersInit) =>
    apiFetch(path, { method: "POST", body: JSON.stringify(body), headers }),
  put: (path: string, body?: unknown, headers?: HeadersInit) =>
    apiFetch(path, { method: "PUT", body: JSON.stringify(body), headers }),
  delete: (path: string, headers?: HeadersInit) =>
    apiFetch(path, { method: "DELETE", headers }),
};
