import React from "react";

export default function MetadataTab({ metadata }) {
  if (!metadata) {
    return (
      <div style={{ padding: "20px 0", color: "var(--text-muted)", fontSize: "13px" }}>
        No video metadata available.
      </div>
    );
  }

  return (
    <div className="metric-grid">
      <div className="metric-card">
        <div className="metric-label">Duration</div>
        <div className="metric-value">{metadata.duration}s</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Resolution</div>
        <div className="metric-value">{metadata.width}x{metadata.height}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Aspect Ratio</div>
        <div className="metric-value">{metadata.aspect_ratio}</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">Framerate</div>
        <div className="metric-value">{metadata.fps} fps</div>
      </div>
      <div className="metric-card">
        <div className="metric-label">File Size</div>
        <div className="metric-value">{metadata.file_size_mb} MB</div>
      </div>
    </div>
  );
}
