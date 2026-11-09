/**
 * API Service for VentiCut Frontend
 */

const BASE_URL = "/api/v1";

export async function submitYoutubeJob(videoUrl, webhookUrl = null, captionStyle = "hormozi_glow") {
  const resp = await fetch(`${BASE_URL}/clips/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      video_url: videoUrl,
      webhook_url: webhookUrl || null,
      caption_style: captionStyle,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit YouTube job");
  }
  return resp.json();
}

export async function submitUploadJob(file, webhookUrl = null, captionStyle = "hormozi_glow") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("caption_style", captionStyle);
  if (webhookUrl) {
    formData.append("webhook_url", webhookUrl);
  }

  const resp = await fetch(`${BASE_URL}/clips/upload`, {
    method: "POST",
    body: formData,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to upload video file");
  }
  return resp.json();
}

export async function fetchJobDetails(jobId) {
  const resp = await fetch(`${BASE_URL}/clips/jobs/${jobId}`);
  if (!resp.ok) {
    throw new Error("Failed to retrieve job details");
  }
  return resp.json();
}

export async function fetchCaptionStyles() {
  const resp = await fetch(`${BASE_URL}/clips/caption-styles`);
  if (!resp.ok) {
    throw new Error("Failed to load caption styles");
  }
  return resp.json();
}

export async function rerenderClip(jobId, clipId, { captionStyle, hookVariantId, hookStyle }) {
  const resp = await fetch(`${BASE_URL}/clips/jobs/${jobId}/clips/${clipId}/rerender`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      caption_style: captionStyle,
      hook_variant_id: hookVariantId || null,
      hook_style: hookStyle || null,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to re-render clip");
  }
  return resp.json();
}

export async function adminLogin(usernameOrEmail, password) {
  const resp = await fetch(`${BASE_URL}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username_or_email: usernameOrEmail,
      password: password,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || "Authentication failed");
  }
  return resp.json();
}

export async function fetchAdminStats(token) {
  const resp = await fetch(`${BASE_URL}/admin/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!resp.ok) {
    throw new Error("Failed to load admin stats");
  }
  return resp.json();
}
