import React, { useState, useEffect, useRef } from "react";
import Navbar from "./components/Navbar";
import VideoIngestion from "./components/VideoIngestion";
import ExecutionMonitor from "./components/ExecutionMonitor";
import ViralClipsTab from "./components/ViralClipsTab";
import UnderstandingTab from "./components/UnderstandingTab";
import TranscriptTab from "./components/TranscriptTab";
import MetadataTab from "./components/MetadataTab";
import LogsTab from "./components/LogsTab";
import AdminModal from "./components/AdminModal";
import { fetchJobDetails } from "./services/api";

export default function App() {
  const [activeJobId, setActiveJobId] = useState(null);
  const [job, setJob] = useState(null);
  const [activeTab, setActiveTab] = useState("viralClips");
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const pollTimerRef = useRef(null);

  const startJobPolling = (jobId) => {
    setActiveJobId(jobId);
    if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    pollJob(jobId);
    pollTimerRef.current = setInterval(() => pollJob(jobId), 1500);
  };

  const pollJob = async (jobId) => {
    try {
      const data = await fetchJobDetails(jobId);
      setJob(data);

      if (data.status === "completed" || data.status === "failed") {
        if (pollTimerRef.current) clearInterval(pollTimerRef.current);
      }
    } catch (err) {
      console.error("Job polling error:", err);
    }
  };

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, []);

  const handleClipUpdated = (updatedClip) => {
    setJob((prev) => {
      if (!prev) return prev;
      const updatedHighlights = (prev.highlights || []).map((c) =>
        c.id === updatedClip.id ? updatedClip : c
      );
      return { ...prev, highlights: updatedHighlights };
    });
  };

  const tabs = [
    { id: "viralClips", label: "Viral Clips" },
    { id: "understanding", label: "Understanding" },
    { id: "transcript", label: "Transcript" },
    { id: "metadata", label: "Metadata" },
    { id: "logs", label: "Logs" },
  ];

  return (
    <>
      <Navbar onOpenAdmin={() => setIsAdminOpen(false || true)} />

      <main>
        <div style={{ marginBottom: "4px" }}>
          <h2 style={{
            fontSize: "24px",
            fontWeight: 700,
            letterSpacing: "-0.025em",
            color: "var(--text-primary)",
            marginBottom: "6px",
          }}>
            Video Ingestion and Analysis
          </h2>
          <p style={{
            fontSize: "14px",
            color: "var(--text-secondary)",
            maxWidth: "680px",
            lineHeight: 1.5,
          }}>
            Submit long-form video files or YouTube URLs to trigger non-blocking background agents: Transcription, Video Understanding, Viral Clip Finder, Hook Generator, Video Editing, and Caption Agent.
          </p>
        </div>

        {/* Video Ingestion Card Grid */}
        <VideoIngestion onJobStarted={startJobPolling} />

        {/* Real-time Execution Monitor */}
        {job && (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <ExecutionMonitor job={job} />

            {/* Tab Navigation */}
            <div style={{
              display: "flex",
              gap: "4px",
              borderBottom: "1px solid var(--border-subtle)",
              paddingBottom: "2px",
              overflowX: "auto",
            }}>
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  style={{
                    background: "none",
                    border: "none",
                    padding: "8px 14px",
                    fontSize: "13px",
                    fontWeight: 500,
                    color: activeTab === t.id ? "var(--text-primary)" : "var(--text-secondary)",
                    backgroundColor: activeTab === t.id ? "var(--bg-subtle)" : "transparent",
                    borderBottom: activeTab === t.id ? "2px solid var(--accent-primary)" : "none",
                    borderRadius: activeTab === t.id ? "var(--radius-sm) var(--radius-sm) 0 0" : "var(--radius-sm)",
                    cursor: "pointer",
                    whiteSpace: "nowrap",
                  }}
                >
                  {t.label}
                  {t.id === "viralClips" && job.highlights?.length > 0 && ` (${job.highlights.length})`}
                </button>
              ))}
            </div>

            {/* Tab Content Panes */}
            <div style={{ paddingTop: "8px" }}>
              {activeTab === "viralClips" && (
                <ViralClipsTab
                  highlights={job.highlights || []}
                  jobId={job.job_id}
                  onClipUpdated={handleClipUpdated}
                />
              )}
              {activeTab === "understanding" && (
                <UnderstandingTab understanding={job.understanding} />
              )}
              {activeTab === "transcript" && (
                <TranscriptTab transcription={job.transcription} />
              )}
              {activeTab === "metadata" && (
                <MetadataTab metadata={job.metadata} />
              )}
              {activeTab === "logs" && (
                <LogsTab logs={job.logs || []} />
              )}
            </div>
          </div>
        )}
      </main>

      <footer style={{
        borderTop: "1px solid var(--border-subtle)",
        padding: "20px 24px",
        textAlign: "center",
        fontSize: "12px",
        color: "var(--text-muted)",
        backgroundColor: "var(--bg-surface)",
      }}>
        VentiCut &bull; Enterprise Video Repurposing Pipeline &bull; React Architecture
      </footer>

      <AdminModal isOpen={isAdminOpen} onClose={() => setIsAdminOpen(false)} />
    </>
  );
}
