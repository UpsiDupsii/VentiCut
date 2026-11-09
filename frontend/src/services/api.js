/**
 * API Service for VentiCut Frontend
 */

const BASE_URL = "/api/v1";

export async function submitYoutubeJob(videoUrl, webhookUrl = null) {
  const resp = await fetch(`${BASE_URL}/clips/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      video_url: videoUrl,
      webhook_url: webhookUrl || null,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to submit YouTube job");
  }
  return resp.json();
}

export async function submitUploadJob(file, webhookUrl = null) {
  const formData = new FormData();
  formData.append("file", file);
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
