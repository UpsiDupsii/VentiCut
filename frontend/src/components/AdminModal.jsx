import React, { useState, useEffect } from "react";
import { adminLogin, fetchAdminStats } from "../services/api";

export default function AdminModal({ isOpen, onClose }) {
  const [adminToken, setAdminToken] = useState(
    localStorage.getItem("venticut_admin_token") || null
  );
  const [username, setUsername] = useState("admin@email.com");
  const [password, setPassword] = useState("1234");
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const loadStats = async (token) => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      const data = await fetchAdminStats(token);
      setStats(data);
    } catch (err) {
      handleLogout();
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && adminToken) {
      loadStats(adminToken);
    }
  }, [isOpen, adminToken]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg("");
    try {
      const res = await adminLogin(username.trim(), password.trim());
      setAdminToken(res.access_token);
      localStorage.setItem("venticut_admin_token", res.access_token);
      loadStats(res.access_token);
    } catch (err) {
      setErrorMsg(err.message || "Invalid credentials");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setAdminToken(null);
    setStats(null);
    localStorage.removeItem("venticut_admin_token");
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(0, 0, 0, 0.7)",
      backdropFilter: "blur(4px)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 100,
      padding: "16px",
    }}>
      <div style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-strong)",
        borderRadius: "var(--radius-lg)",
        width: "100%",
        maxWidth: "680px",
        maxHeight: "90vh",
        overflowY: "auto",
        boxShadow: "0 20px 40px rgba(0, 0, 0, 0.5)",
        display: "flex",
        flexDirection: "column",
      }}>
        <div style={{
          padding: "18px 24px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)" }}>
            {adminToken ? "Admin Console & API Quota Telemetry" : "Administrator Authentication"}
          </h3>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              color: "var(--text-muted)",
              fontSize: "20px",
              cursor: "pointer",
            }}
          >
            &times;
          </button>
        </div>

        <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
          {!adminToken ? (
            /* Login Form */
            <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                Log in to inspect real-time API token consumption, remaining free-tier quotas, and server telemetry.
              </p>

              {errorMsg && (
                <div style={{
                  backgroundColor: "rgba(239, 68, 68, 0.1)",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  color: "#f87171",
                  padding: "10px 14px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "13px",
                }}>
                  {errorMsg}
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-secondary)" }}>
                  Username or Email
                </label>
                <input
                  type="text"
                  className="input-control"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                <label style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-secondary)" }}>
                  Password
                </label>
                <input
                  type="password"
                  className="input-control"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              <button type="submit" className="btn-action" disabled={isLoading}>
                {isLoading ? "Authenticating..." : "Authenticate"}
              </button>

              <p style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Pre-seeded credentials: <code>admin@email.com</code> / <code>1234</code>
              </p>
            </form>
          ) : (
            /* Dashboard View */
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-primary)" }}>
                  admin@email.com (Superadmin)
                </span>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    className="btn-action"
                    style={{ padding: "6px 12px", fontSize: "12px" }}
                    onClick={() => loadStats(adminToken)}
                    disabled={isLoading}
                  >
                    {isLoading ? "Refreshing..." : "Refresh"}
                  </button>
                  <button
                    style={{
                      backgroundColor: "var(--bg-subtle)",
                      border: "1px solid var(--border-subtle)",
                      color: "var(--text-primary)",
                      padding: "6px 12px",
                      fontSize: "12px",
                      borderRadius: "var(--radius-sm)",
                      cursor: "pointer",
                    }}
                    onClick={handleLogout}
                  >
                    Log Out
                  </button>
                </div>
              </div>

              {isLoading && !stats && (
                <div style={{ padding: "32px", textAlign: "center", color: "var(--text-secondary)", fontSize: "13px" }}>
                  Loading real-time API quota telemetry...
                </div>
              )}

              {stats && (
                <>
                  {/* Groq Quota Meter */}
                  <div style={{
                    backgroundColor: "var(--bg-base)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "14px 16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: 500 }}>
                      <span>Groq LLM Tokens (Daily Free Limit)</span>
                      <span>
                        {(stats.api_usage?.groq?.total_tokens_used ?? 0).toLocaleString()} /{" "}
                        {(stats.api_usage?.groq?.daily_token_limit ?? 500000).toLocaleString()} tokens
                      </span>
                    </div>
                    <div style={{
                      width: "100%",
                      height: "6px",
                      backgroundColor: "var(--bg-subtle)",
                      borderRadius: "9999px",
                      overflow: "hidden",
                    }}>
                      <div style={{
                        height: "100%",
                        backgroundColor: "var(--accent-primary)",
                        width: `${Math.min(100, stats.api_usage?.groq?.token_usage_percentage ?? stats.api_usage?.groq?.tokens_pct_used ?? 0)}%`,
                        transition: "width 0.3s ease",
                      }} />
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)" }}>
                      <span>Remaining: {(stats.api_usage?.groq?.tokens_remaining ?? 0).toLocaleString()} tokens</span>
                      <span>Audio: {stats.api_usage?.groq?.whisper_audio_minutes ?? stats.api_usage?.groq?.audio_minutes_processed ?? 0} mins ({stats.api_usage?.groq?.whisper_calls ?? 0} calls)</span>
                    </div>
                  </div>

                  {/* Gemini Quota Meter */}
                  <div style={{
                    backgroundColor: "var(--bg-base)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    padding: "14px 16px",
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: 500 }}>
                      <span>Google Gemini Requests (Daily Limit)</span>
                      <span>
                        {(stats.api_usage?.gemini?.requests_used ?? 0).toLocaleString()} /{" "}
                        {(stats.api_usage?.gemini?.daily_request_limit ?? stats.api_usage?.gemini?.requests_limit ?? 1500).toLocaleString()} requests
                      </span>
                    </div>
                    <div style={{
                      width: "100%",
                      height: "6px",
                      backgroundColor: "var(--bg-subtle)",
                      borderRadius: "9999px",
                      overflow: "hidden",
                    }}>
                      <div style={{
                        height: "100%",
                        backgroundColor: "var(--status-info)",
                        width: `${Math.min(100, stats.api_usage?.gemini?.request_usage_percentage ?? stats.api_usage?.gemini?.requests_pct_used ?? 0)}%`,
                        transition: "width 0.3s ease",
                      }} />
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--text-muted)" }}>
                      <span>Remaining: {(stats.api_usage?.gemini?.requests_remaining ?? 0).toLocaleString()} requests</span>
                      <span>RPM Limit: 15</span>
                    </div>
                  </div>

                  {/* Telemetry Grid */}
                  <div className="metric-grid">
                    <div className="metric-card">
                      <div className="metric-label">Total Jobs</div>
                      <div className="metric-value">{stats.jobs_telemetry?.total ?? 0}</div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-label">Storage (Uploads)</div>
                      <div className="metric-value">
                        {stats.api_usage?.storage?.uploads_mb ?? stats.api_usage?.storage_mb?.uploads ?? 0} MB
                      </div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-label">Webhook Deliveries</div>
                      <div className="metric-value">
                        {stats.api_usage?.webhooks?.successful ?? 0} / {stats.api_usage?.webhooks?.total_dispatched ?? 0}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}