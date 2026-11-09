import React, { useState, useRef } from "react";
import { submitYoutubeJob, submitUploadJob } from "../services/api";

export default function VideoIngestion({ onJobStarted }) {
  const [ytUrl, setYtUrl] = useState("");
  const [ytWebhook, setYtWebhook] = useState("");
  const [uploadWebhook, setUploadWebhook] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSubmittingYt, setIsSubmittingYt] = useState(false);
  const [isSubmittingUpload, setIsSubmittingUpload] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmitYt = async () => {
    if (!ytUrl.trim()) {
      alert("Please enter a valid YouTube video URL.");
      return;
    }
    setIsSubmittingYt(true);
    try {
      const data = await submitYoutubeJob(ytUrl.trim(), ytWebhook.trim() || null);
      onJobStarted(data.job_id);
    } catch (err) {
      alert("Failed to submit YouTube job: " + err.message);
    } finally {
      setIsSubmittingYt(false);
    }
  };

  const handleSubmitUpload = async () => {
    if (!selectedFile) return;
    setIsSubmittingUpload(true);
    try {
      const data = await submitUploadJob(selectedFile, uploadWebhook.trim() || null);
      onJobStarted(data.job_id);
    } catch (err) {
      alert("Failed to upload video: " + err.message);
    } finally {
      setIsSubmittingUpload(false);
    }
  };

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
      gap: "20px",
    }}>
      {/* YouTube Ingestion Panel */}
      <div style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--text-primary)" }}>
            YouTube Source
          </div>
          <span style={{
            fontSize: "11px",
            fontWeight: 500,
            padding: "2px 8px",
            borderRadius: "var(--radius-sm)",
            backgroundColor: "var(--bg-subtle)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
          }}>
            yt-dlp
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-secondary)" }}>
            Video URL
          </label>
          <input
            type="url"
            className="input-control"
            placeholder="https://www.youtube.com/watch?v=..."
            value={ytUrl}
            onChange={(e) => setYtUrl(e.target.value)}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-secondary)" }}>
            Webhook Notification URL (Optional)
          </label>
          <input
            type="url"
            className="input-control"
            placeholder="https://api.yourdomain.com/webhooks/venticut"
            value={ytWebhook}
            onChange={(e) => setYtWebhook(e.target.value)}
          />
        </div>

        <button
          className="btn-action"
          onClick={handleSubmitYt}
          disabled={isSubmittingYt || !ytUrl.trim()}
        >
          {isSubmittingYt ? "Queueing..." : "Process Source in Background"}
        </button>
      </div>

      {/* File Upload Panel */}
      <div style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontSize: "15px", fontWeight: 600, color: "var(--text-primary)" }}>
            Direct File Upload
          </div>
          <span style={{
            fontSize: "11px",
            fontWeight: 500,
            padding: "2px 8px",
            borderRadius: "var(--radius-sm)",
            backgroundColor: "var(--bg-subtle)",
            color: "var(--text-secondary)",
            border: "1px solid var(--border-subtle)",
          }}>
            Local
          </span>
        </div>

        <input
          type="file"
          ref={fileInputRef}
          accept="video/mp4,video/x-matroska,video/quicktime,video/webm"
          style={{ display: "none" }}
          onChange={handleFileChange}
        />

        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          style={{
            border: "1px dashed var(--border-strong)",
            borderRadius: "var(--radius-md)",
            backgroundColor: isDragOver ? "var(--bg-subtle)" : "rgba(22, 32, 50, 0.4)",
            padding: "24px 16px",
            textAlign: "center",
            cursor: "pointer",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
          }}
        >
          <p style={{ fontSize: "13px", fontWeight: 500, color: "var(--text-primary)" }}>
            {selectedFile
              ? `${selectedFile.name} (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)`
              : "Select video file or drag and drop"}
          </p>
          <p style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            MP4, MOV, MKV, WebM up to 500 MB
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-secondary)" }}>
            Webhook Notification URL (Optional)
          </label>
          <input
            type="url"
            className="input-control"
            placeholder="https://api.yourdomain.com/webhooks/venticut"
            value={uploadWebhook}
            onChange={(e) => setUploadWebhook(e.target.value)}
          />
        </div>

        <button
          className="btn-action"
          onClick={handleSubmitUpload}
          disabled={isSubmittingUpload || !selectedFile}
        >
          {isSubmittingUpload ? "Uploading..." : "Upload and Analyze"}
        </button>
      </div>
    </div>
  );
}
