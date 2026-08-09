import { useState } from "react";
import { useAuth } from "./AuthContext.jsx";

export default function Login({ onSwitchToRegister }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
    } catch (err) {
      console.error("[auth] Login failed", {
        status: err.status,
        message: err.message,
      });
      setError(err.message || "Login failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h2>Welcome back</h2>
      <p className="auth-sub">Log in to continue creating with AI.</p>

      <label>
        <span>Email</span>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
          autoComplete="email"
        />
      </label>

      <label>
        <span>Password</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Your password"
          required
          autoComplete="current-password"
        />
      </label>

      {error && <div className="auth-error">{error}</div>}

      <button className="auth-submit" type="submit" disabled={busy}>
        {busy ? "Logging in…" : "Log In"}
      </button>

      <p className="auth-switch">
        Don&apos;t have an account?{" "}
        <button type="button" className="auth-link" onClick={onSwitchToRegister}>
          Create one
        </button>
      </p>
    </form>
  );
}
