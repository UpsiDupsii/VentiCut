import React, { useState } from "react";
import { rerenderClip } from "../services/api";

const CAPTION_STYLES = [
  { id: "hormozi_glow", name: "Hormozi Glow", desc: "Spoken words pop in neon lime", color: "#00FF66" },
  { id: "mrbeast_yellow", name: "MrBeast Yellow", desc: "Bold yellow impact with dark outline", color: "#FFE81F" },
  { id: "karaoke_fill", name: "Karaoke Wave", desc: "Syllable progressive coral color wipe", color: "#FF5511" },
  { id: "tiktok_badge", name: "TikTok Pill", desc: "Frosted badge with magenta highlight", color: "#FF20D0" },
  { id: "minimal_clean", name: "Minimalist Clean", desc: "Clean frosted documentary subtitles", color: "#E0E0E0" },
];

export default function ViralClipsTab({ highlights = [], jobId, onClipUpdated }) {
  const [selectedCaptionStyles, setSelectedCaptionStyles] = useState({});
  const [rerenderingClips, setRerenderingClips] = useState({});
  const [statusMessages, setStatusMessages] = useState({});
  const [activePlatformTabs, setActivePlatformTabs] = useState({});
  const [auditOpenStates, setAuditOpenStates] = useState({});
  const [copyFeedback, setCopyFeedback] = useState({});

  if (!highlights || highlights.length === 0) {
    return (
      <div style={{ padding: "20px 0", color: "var(--text-muted)", fontSize: "13px" }}>
        Awaiting viral clip extraction and rendering...
      </div>
    );
  }

  const handleSelectCaptionStyle = (clipId, styleId) => {
    setSelectedCaptionStyles((prev) => ({ ...prev, [clipId]: styleId }));
  };

  const handlePlatformTab = (clipId, platform) => {
    setActivePlatformTabs((prev) => ({ ...prev, [clipId]: platform }));
  };

  const toggleAudit = (clipId) => {
    setAuditOpenStates((prev) => ({ ...prev, [clipId]: !prev[clipId] }));
  };

  const handleCopyText = (text, key) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopyFeedback((prev) => ({ ...prev, [key]: true }));
    setTimeout(() => {
      setCopyFeedback((prev) => ({ ...prev, [key]: false }));
    }, 2000);
  };

  const handleRerender = async (clip) => {
    if (!jobId) {
      alert("Job ID not available for re-rendering.");
      return;
    }

    const targetStyle = selectedCaptionStyles[clip.id] || clip.caption_style || "hormozi_glow";
    setRerenderingClips((prev) => ({ ...prev, [clip.id]: true }));
    setStatusMessages((prev) => ({ ...prev, [clip.id]: "Re-rendering video, updating subtitles, and regenerating cover frame..." }));

    try {
      const updatedClip = await rerenderClip(jobId, clip.id, {
        captionStyle: targetStyle,
        hookVariantId: clip.selected_hook ? clip.selected_hook.id : null,
      });

      if (onClipUpdated) {
        onClipUpdated(updatedClip);
      }
      setStatusMessages((prev) => ({
        ...prev,
        [clip.id]: `Subtitles and thumbnail refreshed!`,
      }));
    } catch (err) {
      setStatusMessages((prev) => ({ ...prev, [clip.id]: `Failed: ${err.message}` }));
    } finally {
      setRerenderingClips((prev) => ({ ...prev, [clip.id]: false }));
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
          Processed Clips: {highlights.length} &bull; Complete Distribution Pipeline (9:16 Shorts, ASS Subtitles, Cover Frames, Quality Audits, and Multi-Platform SEO)
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {highlights.map((clip, i) => {
          const activeStyle = selectedCaptionStyles[clip.id] || clip.caption_style || "hormozi_glow";
          const isRerendering = rerenderingClips[clip.id] || false;
          const statusMsg = statusMessages[clip.id];
          const activePlatform = activePlatformTabs[clip.id] || "youtube_shorts";
          const isAuditOpen = auditOpenStates[clip.id] || false;

          const qa = clip.quality_review;
          const readinessScore = clip.readiness_score || (qa ? qa.overall_score : 92.0);
          const social = clip.social_metadata;
          const currentPlatformCopy = social ? social[activePlatform] : null;

          return (
            <div
              key={clip.id || i}
              style={{
                backgroundColor: "var(--bg-surface)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                padding: "20px 22px",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
              }}
            >
              {/* Header row with Title and Readiness Score */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
                <div style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.4 }}>
                  #{i + 1} {clip.headline}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  {/* Readiness Score Badge */}
                  <span style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "12px",
                    fontWeight: 600,
                    padding: "4px 10px",
                    borderRadius: "9999px",
                    backgroundColor: readinessScore >= 80 ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                    color: readinessScore >= 80 ? "var(--status-success)" : "var(--status-warning)",
                    border: `1px solid ${readinessScore >= 80 ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
                    whiteSpace: "nowrap",
                  }}>
                    {readinessScore.toFixed(0)}% Publish Ready
                  </span>

                  {/* Virality Score */}
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
              </div>

              {/* Primary Hook Banner */}
              {clip.hook_text && (
                <div style={{
                  backgroundColor: "var(--bg-subtle)",
                  borderLeft: "3px solid var(--accent-primary)",
                  padding: "8px 12px",
                  borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
                  fontSize: "13px",
                  color: "var(--text-primary)",
                }}>
                  <strong>Opening Hook:</strong> "{clip.hook_text}"
                </div>
              )}

              {/* Video timing & scores */}
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
                <span>3s Hook Score: <strong>{clip.hook_score.toFixed(0)}%</strong></span>
                <span>Retention: <strong>{clip.retention_score.toFixed(0)}%</strong></span>
                {clip.caption_word_count > 0 && (
                  <span>Spoken Dialogue Words: <strong>{clip.caption_word_count}</strong></span>
                )}
              </div>

              {/* Media Section: Video Player & 9:16 Thumbnail Preview */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                gap: "16px",
                backgroundColor: "var(--bg-base)",
                borderRadius: "var(--radius-md)",
                padding: "16px",
                border: "1px solid var(--border-subtle)",
              }}>
                {/* Left: Vertical Video Player */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--status-success)" }}>
                      Vertical 9:16 Video (Captions Burned)
                    </span>
                    {clip.rendered_url && (
                      <a
                        href={`${clip.rendered_url}${clip.rendered_url.includes("?") ? "&" : "?"}download=true`}
                        download={`venticut_short_${clip.id}.mp4`}
                        className="btn-action"
                        style={{ textDecoration: "none", fontSize: "11px", padding: "4px 10px" }}
                      >
                        Download MP4
                      </a>
                    )}
                  </div>
                  {clip.rendered_url ? (
                    <div style={{
                      maxWidth: "280px",
                      borderRadius: "var(--radius-md)",
                      overflow: "hidden",
                      backgroundColor: "#000",
                      border: "1px solid var(--border-subtle)",
                    }}>
                      <video
                        key={clip.rendered_url}
                        controls
                        playsInline
                        preload="auto"
                        style={{ width: "100%", maxHeight: "420px", display: "block" }}
                      >
                        <source src={clip.rendered_url} type="video/mp4" />
                        Your browser does not support HTML5 video streaming.
                      </video>
                    </div>
                  ) : (
                    <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
                      Video render in progress...
                    </div>
                  )}
                </div>

                {/* Right: 9:16 Cover Frame Thumbnail */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--status-info)" }}>
                      Vertical Cover Thumbnail (1080x1920)
                    </span>
                    {clip.thumbnail_url && (
                      <a
                        href={clip.thumbnail_url}
                        download={`venticut_cover_${clip.id}.jpg`}
                        style={{
                          backgroundColor: "var(--bg-subtle)",
                          border: "1px solid var(--border-subtle)",
                          color: "var(--text-primary)",
                          padding: "4px 10px",
                          fontSize: "11px",
                          borderRadius: "var(--radius-sm)",
                          textDecoration: "none",
                        }}
                      >
                        Download JPG
                      </a>
                    )}
                  </div>
                  {clip.thumbnail_url ? (
                    <div style={{
                      maxWidth: "240px",
                      borderRadius: "var(--radius-md)",
                      overflow: "hidden",
                      border: "1px solid var(--border-subtle)",
                      backgroundColor: "#000",
                    }}>
                      <img
                        src={clip.thumbnail_url}
                        alt={`Thumbnail for ${clip.headline}`}
                        style={{ width: "100%", maxHeight: "420px", objectFit: "cover", display: "block" }}
                      />
                    </div>
                  ) : (
                    <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: "12px" }}>
                      Cover thumbnail generating...
                    </div>
                  )}
                </div>
              </div>

              {/* Quality & Brand Safety Audit Card */}
              {qa && (
                <div style={{
                  backgroundColor: "var(--bg-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "14px",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "10px",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      Agent 7: Quality Review & Safety Audit ({qa.overall_score.toFixed(0)}/100)
                    </span>
                    <button
                      onClick={() => toggleAudit(clip.id)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--accent-primary)",
                        fontSize: "12px",
                        cursor: "pointer",
                        fontWeight: 500,
                      }}
                    >
                      {isAuditOpen ? "Hide Audit Details" : "View Audit Checklist"}
                    </button>
                  </div>

                  {isAuditOpen && (
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "4px" }}>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "8px" }}>
                        {qa.checks && qa.checks.map((chk, cIdx) => (
                          <div
                            key={cIdx}
                            style={{
                              backgroundColor: "var(--bg-base)",
                              border: "1px solid var(--border-subtle)",
                              borderRadius: "var(--radius-sm)",
                              padding: "10px",
                              display: "flex",
                              flexDirection: "column",
                              gap: "4px",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                              <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>
                                {chk.name}
                              </span>
                              <span style={{
                                fontSize: "10px",
                                fontWeight: 600,
                                textTransform: "uppercase",
                                padding: "2px 6px",
                                borderRadius: "4px",
                                backgroundColor: chk.status === "pass" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                                color: chk.status === "pass" ? "var(--status-success)" : "var(--status-warning)",
                              }}>
                                {chk.status} ({chk.score.toFixed(0)}%)
                              </span>
                            </div>
                            <span style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: 1.3 }}>
                              {chk.details}
                            </span>
                          </div>
                        ))}
                      </div>

                      {qa.suggestions && qa.suggestions.length > 0 && (
                        <div style={{ marginTop: "6px", fontSize: "12px", color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: "4px" }}>
                          <strong>Tactical Publishing Recommendations:</strong>
                          {qa.suggestions.map((sug, sIdx) => (
                            <div key={sIdx} style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                              &bull; {sug}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Multi-Platform Social Distribution Suite (Agent 8) */}
              {social && (
                <div style={{
                  backgroundColor: "var(--bg-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "14px",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                      Agent 8: Multi-Platform SEO & Distribution Copy
                    </span>
                    <div style={{ display: "flex", gap: "6px" }}>
                      {[
                        { id: "youtube_shorts", label: "YouTube Shorts" },
                        { id: "tiktok", label: "TikTok" },
                        { id: "instagram_reels", label: "Instagram Reels" },
                      ].map((tab) => (
                        <button
                          key={tab.id}
                          onClick={() => handlePlatformTab(clip.id, tab.id)}
                          style={{
                            backgroundColor: activePlatform === tab.id ? "var(--accent-primary)" : "var(--bg-base)",
                            color: activePlatform === tab.id ? "#fff" : "var(--text-secondary)",
                            border: "1px solid var(--border-subtle)",
                            padding: "4px 10px",
                            fontSize: "11px",
                            borderRadius: "var(--radius-sm)",
                            cursor: "pointer",
                            fontWeight: 500,
                          }}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {currentPlatformCopy && (
                    <div style={{
                      backgroundColor: "var(--bg-base)",
                      borderRadius: "var(--radius-sm)",
                      padding: "12px",
                      border: "1px solid var(--border-subtle)",
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}>
                      {/* Post Title */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                          {currentPlatformCopy.title}
                        </span>
                        <button
                          onClick={() => handleCopyText(
                            `${currentPlatformCopy.caption}\n\n${(currentPlatformCopy.hashtags || []).join(" ")}`,
                            `${clip.id}_caption`
                          )}
                          style={{
                            backgroundColor: "var(--bg-subtle)",
                            border: "1px solid var(--border-subtle)",
                            color: "var(--text-primary)",
                            padding: "4px 10px",
                            fontSize: "11px",
                            borderRadius: "var(--radius-sm)",
                            cursor: "pointer",
                          }}
                        >
                          {copyFeedback[`${clip.id}_caption`] ? "Copied!" : "Copy Post Caption"}
                        </button>
                      </div>

                      {/* Post Caption */}
                      <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.5, whiteSpace: "pre-line" }}>
                        {currentPlatformCopy.caption}
                      </div>

                      {/* Hashtags */}
                      {currentPlatformCopy.hashtags && currentPlatformCopy.hashtags.length > 0 && (
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
                          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                            {currentPlatformCopy.hashtags.map((tag, tIdx) => (
                              <span key={tIdx} style={{ fontSize: "11px", color: "var(--status-info)" }}>
                                {tag}
                              </span>
                            ))}
                          </div>
                          <button
                            onClick={() => handleCopyText(currentPlatformCopy.hashtags.join(" "), `${clip.id}_tags`)}
                            style={{
                              background: "none",
                              border: "none",
                              color: "var(--text-muted)",
                              fontSize: "11px",
                              cursor: "pointer",
                              textDecoration: "underline",
                            }}
                          >
                            {copyFeedback[`${clip.id}_tags`] ? "Copied Tags!" : "Copy All Tags"}
                          </button>
                        </div>
                      )}

                      {/* Pinned Comment */}
                      {currentPlatformCopy.pinned_comment && (
                        <div style={{
                          backgroundColor: "var(--bg-subtle)",
                          padding: "8px 10px",
                          borderRadius: "var(--radius-sm)",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          fontSize: "11px",
                        }}>
                          <span style={{ color: "var(--text-primary)" }}>
                            <strong>Pinned Comment:</strong> "{currentPlatformCopy.pinned_comment}"
                          </span>
                          <button
                            onClick={() => handleCopyText(currentPlatformCopy.pinned_comment, `${clip.id}_comment`)}
                            style={{
                              background: "none",
                              border: "none",
                              color: "var(--accent-primary)",
                              cursor: "pointer",
                              fontWeight: 500,
                            }}
                          >
                            {copyFeedback[`${clip.id}_comment`] ? "Copied!" : "Copy"}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Caption Style Selector */}
              <div style={{
                backgroundColor: "var(--bg-subtle)",
                borderRadius: "var(--radius-md)",
                padding: "14px",
                border: "1px solid var(--border-subtle)",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    Agent 6: Caption Subtitle Presets
                  </span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Select style to re-burn dialogue captions
                  </span>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: "8px" }}>
                  {CAPTION_STYLES.map((st) => {
                    const isSelected = activeStyle === st.id;
                    return (
                      <div
                        key={st.id}
                        onClick={() => handleSelectCaptionStyle(clip.id, st.id)}
                        style={{
                          backgroundColor: isSelected ? "var(--bg-elevated)" : "var(--bg-base)",
                          border: `1.5px solid ${isSelected ? "var(--accent-primary)" : "var(--border-subtle)"}`,
                          borderRadius: "var(--radius-sm)",
                          padding: "10px",
                          cursor: "pointer",
                          display: "flex",
                          flexDirection: "column",
                          gap: "4px",
                          transition: "all 0.15s ease",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                          <span style={{ fontSize: "12px", fontWeight: 600, color: isSelected ? "var(--text-primary)" : "var(--text-secondary)" }}>
                            {st.name}
                          </span>
                          <span style={{ width: "10px", height: "10px", borderRadius: "50%", backgroundColor: st.color, display: "inline-block" }} />
                        </div>
                        <span style={{ fontSize: "11px", color: "var(--text-muted)", lineHeight: 1.3 }}>
                          {st.desc}
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "10px", marginTop: "4px" }}>
                  <button
                    className="btn-action"
                    onClick={() => handleRerender(clip)}
                    disabled={isRerendering}
                    style={{ fontSize: "12px", padding: "6px 14px" }}
                  >
                    {isRerendering ? "Burning Subtitles & Updating Assets..." : "Apply & Re-burn Subtitles"}
                  </button>
                  {statusMsg && (
                    <span style={{ fontSize: "12px", color: statusMsg.includes("Failed") ? "var(--status-error)" : "var(--status-success)" }}>
                      {statusMsg}
                    </span>
                  )}
                </div>
              </div>

              {/* Hook Variants Generated by Hook Generator Agent */}
              {clip.hooks && clip.hooks.length > 0 && (
                <div style={{
                  backgroundColor: "var(--bg-subtle)",
                  borderRadius: "var(--radius-md)",
                  padding: "12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px",
                  border: "1px solid var(--border-subtle)",
                }}>
                  <div style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    Agent 4: Hook Generator &bull; 4 Copywriting Archetypes
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "8px" }}>
                    {clip.hooks.map((h, hIdx) => (
                      <div
                        key={h.id || hIdx}
                        style={{
                          backgroundColor: "var(--bg-base)",
                          border: "1px solid var(--border-subtle)",
                          borderRadius: "var(--radius-sm)",
                          padding: "8px 10px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "4px",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontSize: "11px", fontWeight: 600, color: "#818cf8" }}>
                            {h.hook_type}
                          </span>
                          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "10px", fontWeight: 600, color: "var(--status-success)" }}>
                            {h.hook_score.toFixed(0)}%
                          </span>
                        </div>
                        <div style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-primary)" }}>
                          {h.headline}
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--text-secondary)", lineHeight: 1.4 }}>
                          "{h.spoken_hook}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Editorial reasoning */}
              {clip.reasoning && (
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {clip.reasoning}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
