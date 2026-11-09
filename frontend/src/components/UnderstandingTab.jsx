import React from "react";

export default function UnderstandingTab({ understanding }) {
  if (!understanding) {
    return (
      <div style={{ padding: "20px 0", color: "var(--text-muted)", fontSize: "13px" }}>
        Awaiting video understanding analysis...
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div>
        <div style={{
          fontSize: "13px",
          fontWeight: 600,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          marginBottom: "4px",
        }}>
          Summary
        </div>
        <div style={{
          backgroundColor: "var(--bg-base)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-md)",
          padding: "16px",
        }}>
          <p style={{ fontSize: "13px", lineHeight: 1.6, color: "var(--text-secondary)" }}>
            {understanding.summary || "No summary provided."}
          </p>
        </div>
      </div>

      <div>
        <div style={{
          fontSize: "13px",
          fontWeight: 600,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          marginBottom: "6px",
        }}>
          Identified Topics
        </div>
        <div>
          {(understanding.topics || []).map((topic, i) => (
            <span key={i} className="badge-chip">
              {topic}
            </span>
          ))}
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-label">Tone</div>
          <div className="metric-value">{understanding.tone || "General"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Pacing</div>
          <div className="metric-value">{understanding.pacing || "Moderate"}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Target Audience</div>
          <div className="metric-value">{understanding.target_audience || "General"}</div>
        </div>
      </div>

      <div>
        <div style={{
          fontSize: "13px",
          fontWeight: 600,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.03em",
          marginBottom: "4px",
        }}>
          Suggested Opening Hooks
        </div>
        <div style={{
          backgroundColor: "var(--bg-base)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-md)",
          padding: "16px",
        }}>
          <ul style={{
            fontSize: "13px",
            lineHeight: 1.6,
            paddingLeft: "18px",
            color: "var(--text-primary)",
          }}>
            {(understanding.potential_hooks || []).map((hook, i) => (
              <li key={i}>{hook}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
