import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { API_BASE, parseJson, setToken } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setChecking(false);
      return;
    }

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => parseJson(res))
      .then(({ ok, data }) => {
        if (!ok || !data || !data.user) {
          throw new Error("Session expired");
        }
        setUser(data.user);
      })
      .catch(() => logout())
      .finally(() => setChecking(false));
  }, [logout]);

  const authenticate = async (path, email, password) => {
    const fallback = path.includes("register")
      ? "Registration failed. Please try again."
      : "Login failed. Please try again.";

    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
    } catch {
      const error = new Error(
        "Network error. Please check your connection and try again."
      );
      error.status = 0;
      throw error;
    }

    const { status, ok, data } = await parseJson(res);

    if (!ok) {
      const serverMessage =
        data && typeof data === "object"
          ? data.message || data.detail
          : null;
      const message =
        status >= 500
          ? "Server error. Please try again later."
          : serverMessage || fallback;
      const error = new Error(message);
      error.status = status;
      throw error;
    }

    if (!data || typeof data !== "object" || !data.access_token) {
      const error = new Error(fallback);
      error.status = status;
      throw error;
    }

    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  const login = useCallback(
    (email, password) => authenticate("/auth/login", email, password),
    []
  );

  const register = useCallback(
    (email, password) => authenticate("/auth/register", email, password),
    []
  );

  return (
    <AuthContext.Provider value={{ user, checking, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
