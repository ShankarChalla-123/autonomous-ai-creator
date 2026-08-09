import { useState } from "react";
import { useAuth } from "./AuthContext.jsx";

export default function Register({ onSwitchToLogin }) {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setBusy(true);
    try {
      await register(email, password);
    } catch (err) {
      console.error("[auth] Registration failed", {
        status: err.status,
        message: err.message,
      });
      setError(err.message || "Registration failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h2>Create your account</h2>
      <p className="auth-sub">Start the autonomous AI creator pipeline.</p>

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
          placeholder="At least 8 characters"
          required
          autoComplete="new-password"
        />
      </label>

      <label>
        <span>Confirm password</span>
        <input
          type="password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="Repeat your password"
          required
          autoComplete="new-password"
        />
      </label>

      {error && <div className="auth-error">{error}</div>}

      <button className="auth-submit" type="submit" disabled={busy}>
        {busy ? "Creating account…" : "Register"}
      </button>

      <p className="auth-switch">
        Already have an account?{" "}
        <button type="button" className="auth-link" onClick={onSwitchToLogin}>
          Log in
        </button>
      </p>
    </form>
  );
}
