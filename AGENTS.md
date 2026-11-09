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
- After completing work on a branch:
  - Run `ruff check .`, `ruff format --check .`, and `pytest`.
  - Commit cleanly and push the branch to GitHub.
  - Provide a clear, copy-pasteable Pull Request title and description targeting `staging`.
  - The user reviews, merges into `staging`, and deletes the feature branch.
- After a cohesive set of features is ready on `staging`, a release PR is prepared for `staging -> main` with release notes.

## 3. Architecture Principles
- Multi-Agent System: Each agent has a single, well-defined responsibility.
- Separation of Concerns: LLMs make decisions; deterministic tools (FFmpeg, OpenCV, yt-dlp, Whisper) execute media processing.
- Prioritize Free APIs and Open Source tools:
  - Google Gemini API (Google AI Studio - free tier for multimodal reasoning and text).
  - Groq API (console.groq.com - free tier for fast Whisper transcription and Llama models).
  - Local tools: FFmpeg, yt-dlp, faster-whisper / whisper.
- UI/UX Design: Clean, modern interface styled to complement the branding and color palette of `assets/logo.png`.
