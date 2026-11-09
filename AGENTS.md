# VentiCut Project Rules and Preferences

## 1. Zero Emoji Policy
- Do not use emojis anywhere: in code, comments, documentation, commit messages, PR descriptions, or assistant responses.

## 2. SDLC and Branching Strategy
- Staging and Main branches:
  - `main` is production/release.
  - `staging` is integration.
- Every new agent, feature, fix, or chore must be developed on a dedicated branch branched off `staging`:
  - `feat/<feature-name>`
  - `fix/<fix-name>`
  - `chore/<chore-name>`
- Local Review First Policy:
  - After completing feature development and local test verification, DO NOT automatically push the branch to GitHub or prompt to open a PR.
  - Instead, run the local server, provide a comprehensive local verification guide, and ask for the user's confirmation to review locally first.
  - Only after the user explicitly confirms that local testing is satisfactory, push the branch to GitHub and supply the copy-pasteable PR title and description targeting `staging`.
  - Always remind the user to delete the feature branch after merging the PR on GitHub to prevent branch clutter.
- After a cohesive set of features is ready on `staging`, a release PR is prepared for `staging -> main` with release notes.

## 3. Architecture Principles
- Multi-Agent System: Each agent has a single, well-defined responsibility.
- Separation of Concerns: LLMs make decisions; deterministic tools (FFmpeg, OpenCV, yt-dlp, Whisper) execute media processing.
- Background Tasks & Asynchronous Execution: Return immediate responses to clients, process heavy media workflows in background workers, and dispatch status updates via Webhooks.
- Prioritize Free APIs and Open Source tools:
  - Google Gemini API (Google AI Studio - free tier for multimodal reasoning and text).
  - Groq API (console.groq.com - free tier for fast Whisper transcription and Llama models).
  - Local tools: FFmpeg, yt-dlp, faster-whisper / whisper.
- UI/UX Design & Frontend Architecture:
  - Clean, modern enterprise interface styled to complement the branding and color palette of `assets/logo.png`.
  - Built with React.js using modular, single-responsibility components in separate `.jsx` files (e.g. `Navbar.jsx`, `VideoIngestion.jsx`, `ExecutionMonitor.jsx`, individual tab components, `AdminModal.jsx`) for clean debugging and maintenance.

## 4. Change Tracking and Reporting
- Step-by-Step Reporting: In every turn where code or project files are modified, clearly report the chronological steps taken and why.
- Ordered File Manifest: Provide a sequential list of all files created, modified, or removed with clickable links and brief explanations of what was changed in each file to facilitate self-review and project comprehension.
