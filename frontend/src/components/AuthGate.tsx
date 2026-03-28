"use client";

import { useState, useEffect, ReactNode } from "react";
import { checkPassword } from "@/lib/api";

export default function AuthGate({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("runnon_auth");
    if (stored === "true") {
      setAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setChecking(true);
    setError("");

    try {
      const result = await checkPassword(password);
      if (result.authenticated) {
        localStorage.setItem("runnon_auth", "true");
        setAuthenticated(true);
      } else {
        setError("Wrong password");
        setPassword("");
      }
    } catch {
      setError("Can't reach the server");
    } finally {
      setChecking(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-foreground/20 border-t-foreground rounded-full animate-spin" />
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-full max-w-xs text-center">
          <h1 className="text-4xl font-bold tracking-tight mb-2">
            RUNNON
          </h1>
          <p className="text-muted text-sm mb-10">content engine</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="w-full text-center tracking-widest"
              autoFocus
            />
            {error && (
              <p className="text-danger text-sm">{error}</p>
            )}
            <button
              type="submit"
              disabled={checking || !password}
              className="btn-primary w-full"
            >
              {checking ? "..." : "Enter"}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
