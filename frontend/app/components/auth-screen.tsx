"use client";

import { useMemo, useState } from "react";
import { useAuth } from "../lib/auth-context";

export function AuthScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
    [],
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const response = await fetch(`${apiBaseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail ?? "Login failed");
      }

      const data = await response.json();
      login(data.access_token, data.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="tool-card feature-card auth-card" style={{ maxWidth: "400px", margin: "4rem auto" }}>
        <div className="section-heading compact-heading" style={{ textAlign: "center" }}>
          <h2>Sign In</h2>
          <p>Please log in to access Bambam Converter Suite</p>
        </div>

        <form className="converter-form" onSubmit={handleSubmit}>
          <label className="field-group">
            <span>Username</span>
            <input
              type="text"
              required
              minLength={3}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
            />
          </label>

          <label className="field-group">
            <span>Password</span>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
            />
          </label>

          {error && <p className="error-text" style={{ textAlign: "center" }}>{error}</p>}

          <button className="primary-button" type="submit" disabled={isLoading}>
            {isLoading ? "Please wait..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
