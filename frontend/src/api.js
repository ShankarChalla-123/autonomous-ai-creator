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
