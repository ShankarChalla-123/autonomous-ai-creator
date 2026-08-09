import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { API_BASE, setToken } from "./api.js";

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
      .then((res) => {
        if (!res.ok) throw new Error("Session expired");
        return res.json();
      })
      .then((data) => setUser(data.user))
      .catch(() => logout())
      .finally(() => setChecking(false));
  }, [logout]);

  const authenticate = async (path, email, password) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.message || "Authentication failed.");
    setToken(json.access_token);
    setUser(json.user);
    return json.user;
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
