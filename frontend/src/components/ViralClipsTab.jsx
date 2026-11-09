import React from "react";

export default function ViralClipsTab({ highlights = [] }) {
  if (!highlights || highlights.length === 0) {
    return (
      <div style={{ padding: "20px 0", color: "var(--text-muted)", fontSize: "13px" }}>
        Awaiting viral clip extraction...
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          Detected Clips: {highlights.length}
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        {highlights.map((clip, i) => (
          <div
            key={clip.id || i}
            style={{
              backgroundColor: "var(--bg-base)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "18px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
              <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.4 }}>
                #{i + 1} {clip.headline}
              </div>
              <span style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "12px",
                fontWeight: 600,
                padding: "4px 10px",
                borderRadius: "9999px",
                backgroundColor: "rgba(79, 70, 229, 0.15)",
                color: "#818cf8",
                border: "1px solid rgba(79, 70, 229, 0.3)",
                whiteSpace: "nowrap",
              }}>
                {clip.virality_score.toFixed(0)} Virality
              </span>
            </div>

            {clip.hook_text && (
              <div style={{
                backgroundColor: "var(--bg-subtle)",
                borderLeft: "3px solid var(--accent-primary)",
                padding: "8px 12px",
                borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
                fontSize: "13px",
                color: "var(--text-primary)",
              }}>
                <strong>Hook:</strong> "{clip.hook_text}"
              </div>
            )}

            <div style={{
              display: "flex",
              alignItems: "center",
              gap: "16px",
              fontSize: "12px",
              color: "var(--text-muted)",
              flexWrap: "wrap",
            }}>
              <span style={{
                fontFamily: "'JetBrains Mono', monospace",
                color: "var(--status-info)",
                fontWeight: 500,
              }}>
                {clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s ({clip.duration.toFixed(1)}s)
              </span>
              <span>Hook Score: <strong>{clip.hook_score.toFixed(0)}%</strong></span>
              <span>Retention: <strong>{clip.retention_score.toFixed(0)}%</strong></span>
            </div>

            {clip.reasoning && (
              <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                {clip.reasoning}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
