import React, { useRef, useEffect } from "react";

export default function LogsTab({ logs = [] }) {
  const logRef = useRef(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div
      ref={logRef}
      style={{
        backgroundColor: "var(--bg-base)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-md)",
        padding: "14px",
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: "12px",
        color: "var(--text-secondary)",
        maxHeight: "260px",
        overflowY: "auto",
        lineHeight: 1.6,
        whiteSpace: "pre-wrap",
      }}
    >
      {logs.length > 0 ? logs.join("\n") : "Pipeline execution events will be logged here."}
    </div>
  );
}
