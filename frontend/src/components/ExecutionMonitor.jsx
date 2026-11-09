import React from "react";

export default function ExecutionMonitor({ job }) {
  if (!job) return null;

  const pct = job.progress || 0;

  const getStepClass = (stepNum) => {
    if (stepNum === 1) {
      if (pct >= 20) return "completed";
      if (pct > 0) return "active";
    }
    if (stepNum === 2) {
      if (pct >= 55) return "completed";
      if (pct >= 20) return "active";
    }
    if (stepNum === 3) {
      if (pct >= 75) return "completed";
      if (pct >= 55) return "active";
    }
    if (stepNum === 4) {
      if (pct >= 90) return "completed";
      if (pct >= 75) return "active";
    }
    return "";
  };

  const steps = [
    { num: 1, label: "Step 1", title: "Ingestion & Audio" },
    { num: 2, label: "Step 2", title: "Transcription Agent" },
    { num: 3, label: "Step 3", title: "Understanding Agent" },
    { num: 4, label: "Step 4", title: "Viral Clip Finder" },
  ];

  return (
    <div style={{
      backgroundColor: "var(--bg-surface)",
      border: "1px solid var(--border-subtle)",
      borderRadius: "var(--radius-lg)",
      padding: "24px",
      display: "flex",
      flexDirection: "column",
      gap: "20px",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "12px",
      }}>
        <div>
          <h3 style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)" }}>
            {job.video_filename || "Job Execution"}
          </h3>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
            {job.message || "Processing..."}
          </p>
        </div>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "15px",
          fontWeight: 600,
          color: "var(--text-primary)",
        }}>
          {pct}%
        </div>
      </div>

      {/* Progress Track */}
      <div style={{
        width: "100%",
        height: "6px",
        backgroundColor: "var(--bg-base)",
        borderRadius: "9999px",
        overflow: "hidden",
        border: "1px solid var(--border-subtle)",
      }}>
        <div style={{
          height: "100%",
          width: `${pct}%`,
          backgroundColor: "var(--accent-primary)",
          transition: "width 0.3s ease",
        }} />
      </div>

      {/* Stepper Cards */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
        gap: "12px",
      }}>
        {steps.map((s) => {
          const state = getStepClass(s.num);
          const isCompleted = state === "completed";
          const isActive = state === "active";

          return (
            <div
              key={s.num}
              style={{
                backgroundColor: isActive ? "var(--bg-elevated)" : "var(--bg-subtle)",
                border: `1px solid ${
                  isCompleted
                    ? "rgba(16, 185, 129, 0.4)"
                    : isActive
                    ? "var(--accent-primary)"
                    : "var(--border-subtle)"
                }`,
                borderRadius: "var(--radius-md)",
                padding: "12px 14px",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
              }}
            >
              <span style={{
                fontSize: "11px",
                fontWeight: 600,
                color: isCompleted ? "var(--status-success)" : "var(--text-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.04em",
              }}>
                {s.label}
              </span>
              <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-primary)" }}>
                {s.title}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
