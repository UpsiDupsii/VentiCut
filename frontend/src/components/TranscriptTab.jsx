import React, { useState } from "react";

export default function TranscriptTab({ transcription }) {
  const [copied, setCopied] = useState(false);

  if (!transcription) {
    return (
      <div style={{ padding: "20px 0", color: "var(--text-muted)", fontSize: "13px" }}>
        Awaiting transcription data...
      </div>
    );
  }

  const segments = transcription.segments || [];
  const fullText = transcription.full_text || "";

  const handleCopy = () => {
    if (!fullText) return;
    navigator.clipboard.writeText(fullText).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          Segments: {segments.length} | Language: {(transcription.language || "EN").toUpperCase()}
        </span>
        <button
          className="btn-action"
          style={{ padding: "6px 12px", fontSize: "12px" }}
          onClick={handleCopy}
        >
          {copied ? "Copied!" : "Copy Full Transcript"}
        </button>
      </div>

      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: "8px",
        maxHeight: "420px",
        overflowY: "auto",
        paddingRight: "6px",
      }}>
        {segments.map((seg, i) => (
          <div
            key={seg.id || i}
            style={{
              backgroundColor: "var(--bg-base)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "var(--radius-md)",
              padding: "12px 14px",
              display: "flex",
              flexDirection: "column",
              gap: "4px",
            }}
          >
            <div style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "11px",
              color: "var(--status-info)",
              fontWeight: 500,
            }}>
              {seg.start.toFixed(2)}s - {seg.end.toFixed(2)}s
            </div>
            <div style={{ fontSize: "13px", lineHeight: 1.5, color: "var(--text-primary)" }}>
              {seg.text}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
