import React from "react";

export default function Navbar({ onOpenAdmin }) {
  return (
    <header style={{
      backgroundColor: "rgba(17, 24, 39, 0.85)",
      backdropFilter: "blur(8px)",
      borderBottom: "1px solid var(--border-subtle)",
      position: "sticky",
      top: 0,
      zIndex: 50,
      padding: "14px 28px",
    }}>
      <div style={{
        maxWidth: "1280px",
        margin: "0 auto",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <img
            src="/assets/logo.png"
            alt="VentiCut Logo"
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "var(--radius-sm)",
              objectFit: "contain",
              border: "1px solid var(--border-subtle)",
            }}
          />
          <div>
            <h1 style={{
              fontSize: "16px",
              fontWeight: 700,
              letterSpacing: "-0.02em",
              color: "var(--text-primary)",
            }}>
              VentiCut
            </h1>
            <p style={{
              fontSize: "12px",
              color: "var(--text-muted)",
              fontWeight: 400,
            }}>
              AI Video Repurposing Pipeline
            </p>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            padding: "4px 10px",
            fontSize: "12px",
            fontWeight: 500,
            borderRadius: "9999px",
            backgroundColor: "var(--status-success-bg)",
            color: "var(--status-success)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
          }}>
            <span style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: "currentColor",
            }}></span>
            Pipeline & Webhooks Ready
          </span>

          <button
            onClick={onOpenAdmin}
            style={{
              backgroundColor: "var(--bg-subtle)",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-primary)",
              padding: "6px 14px",
              fontSize: "12px",
              fontWeight: 500,
              borderRadius: "var(--radius-sm)",
              cursor: "pointer",
            }}
          >
            Admin Console
          </button>
        </div>
      </div>
    </header>
  );
}
