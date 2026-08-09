export const API_BASE = (import.meta.env.VITE_API_BASE_URL || "")
  .replace(/\/+$/, "");

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  if (token) localStorage.setItem("token", token);
  else localStorage.removeItem("token");
}

export function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function parseJson(res) {
  let text = "";
  try {
    text = await res.text();
  } catch {
    text = "";
  }

  if (!text.trim()) {
    return { status: res.status, ok: res.ok, data: null, text };
  }

  try {
    return { status: res.status, ok: res.ok, data: JSON.parse(text), text };
  } catch {
    return { status: res.status, ok: res.ok, data: null, text };
  }
}
