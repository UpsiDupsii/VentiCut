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

  const handleRerender = async (clip) => {
    if (!jobId) {
      alert("Job ID not available for re-rendering.");
      return;
    }

    const targetStyle = selectedCaptionStyles[clip.id] || clip.caption_style || "hormozi_glow";
    setRerenderingClips((prev) => ({ ...prev, [clip.id]: true }));
    setStatusMessages((prev) => ({ ...prev, [clip.id]: "Burning synchronized dialogue captions via FFmpeg..." }));

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
        [clip.id]: `Subtitles updated to ${targetStyle}!`,
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
          Processed Clips: {highlights.length} &bull; Vertical 9:16 Shorts with Spoken Voice Captions
        </span>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
        {highlights.map((clip, i) => {
          const activeStyle = selectedCaptionStyles[clip.id] || clip.caption_style || "hormozi_glow";
          const isRerendering = rerenderingClips[clip.id] || false;
          const statusMsg = statusMessages[clip.id];

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
                gap: "14px",
              }}
            >
              {/* Header row */}
              <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "12px" }}>
                <div style={{ fontSize: "16px", fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.4 }}>
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

              {/* Rendered Video Player with Dialogue Captions */}
              {clip.rendered_url && (
                <div style={{
                  backgroundColor: "var(--bg-base)",
                  borderRadius: "var(--radius-md)",
                  padding: "16px",
                  border: "1px solid var(--border-subtle)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}>
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "8px",
                  }}>
                    <span style={{
                      fontSize: "12px",
                      fontWeight: 600,
                      color: "var(--status-success)",
                    }}>
                      Vertical 9:16 Video Ready &bull; Spoken Voice Subtitles Burned
                    </span>
                    <a
                      href={clip.rendered_url}
                      download={`venticut_short_${clip.id}.mp4`}
                      className="btn-action"
                      style={{
                        textDecoration: "none",
                        fontSize: "12px",
                        padding: "6px 14px",
                      }}
                    >
                      Download MP4
                    </a>
                  </div>

                  {/* HTML5 Video Player */}
                  <div style={{
                    maxWidth: "300px",
                    borderRadius: "var(--radius-md)",
                    overflow: "hidden",
                    backgroundColor: "#000",
                    border: "1px solid var(--border-subtle)",
                  }}>
                    <video
                      key={clip.rendered_url}
                      controls
                      preload="metadata"
                      src={clip.rendered_url}
                      style={{ width: "100%", maxHeight: "450px", display: "block" }}
                    />
                  </div>

                  {/* Applied Effects Badges */}
                  {clip.editing_effects && clip.editing_effects.length > 0 && (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {clip.editing_effects.map((eff, effIdx) => (
                        <span key={effIdx} className="badge-chip">
                          {eff}
                        </span>
                      ))}
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
                <div style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "6px",
                }}>
                  <span style={{
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                  }}>
                    Caption Subtitle Presets
                  </span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Select style to re-burn dialogue captions
                  </span>
                </div>

                <div style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
                  gap: "8px",
                }}>
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
                          <span style={{
                            fontSize: "12px",
                            fontWeight: 600,
                            color: isSelected ? "var(--text-primary)" : "var(--text-secondary)",
                          }}>
                            {st.name}
                          </span>
                          <span style={{
                            width: "10px",
                            height: "10px",
                            borderRadius: "50%",
                            backgroundColor: st.color,
                            display: "inline-block",
                          }} />
                        </div>
                        <span style={{
                          fontSize: "11px",
                          color: "var(--text-muted)",
                          lineHeight: 1.3,
                        }}>
                          {st.desc}
                        </span>
                      </div>
                    );
                  })}
                </div>

                <div style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  gap: "10px",
                  marginTop: "4px",
                }}>
                  <button
                    className="btn-action"
                    onClick={() => handleRerender(clip)}
                    disabled={isRerendering}
                    style={{ fontSize: "12px", padding: "6px 14px" }}
                  >
                    {isRerendering ? "Burning Subtitles with FFmpeg..." : "Apply & Re-burn Subtitles"}
                  </button>
                  {statusMsg && (
                    <span style={{
                      fontSize: "12px",
                      color: statusMsg.includes("Failed") ? "var(--status-error)" : "var(--status-success)",
                    }}>
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
                  <div style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                  }}>
                    Hook Generator Agent &bull; 4 Copywriting Archetypes
                  </div>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
                    gap: "8px",
                  }}>
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
                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}>
                          <span style={{
                            fontSize: "11px",
                            fontWeight: 600,
                            color: "#818cf8",
                          }}>
                            {h.hook_type}
                          </span>
                          <span style={{
                            fontFamily: "'JetBrains Mono', monospace",
                            fontSize: "10px",
                            fontWeight: 600,
                            color: "var(--status-success)",
                          }}>
                            {h.hook_score.toFixed(0)}%
                          </span>
                        </div>
                        <div style={{
                          fontSize: "12px",
                          fontWeight: 600,
                          color: "var(--text-primary)",
                        }}>
                          {h.headline}
                        </div>
                        <div style={{
                          fontSize: "11px",
                          color: "var(--text-secondary)",
                          lineHeight: 1.4,
                        }}>
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
