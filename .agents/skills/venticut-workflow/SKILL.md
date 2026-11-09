---
name: venticut-workflow
description: Enforces VentiCut development standards, SDLC branching, multi-agent architecture, and PR workflows without emojis.
---

# VentiCut Development Skill

This skill guides the implementation of the VentiCut multi-agent AI video repurposing pipeline.

## General Guidelines
- Strict zero-emoji policy across all responses, commits, documentation, and code.
- Always branch off `staging` using `feat/<agent-or-feature-name>`.
- Always verify Ruff linting (`ruff check .`, `ruff format --check .`) and pytest tests before pushing.
- Always provide the user with a ready-to-use PR title and description for merging into `staging`.

## Agent System Overview
1. Ingestion / Downloader: Fetches video from YouTube (yt-dlp) or file upload.
2. Video Understanding Agent: Analyzes the overarching context, topic, pacing, and speakers.
3. Transcription Agent: Generates precise timestamped transcripts (Whisper/Groq/Gemini).
4. Viral Clip Finder Agent: Scores segment virality (hook, retention, emotional peak) and marks 15-60s cuts.
5. Hook Generator Agent: Crafts opening visual hooks, headline text, and engagement triggers.
6. Video Editing Agent: Determines camera tracking, 9:16 smart cropping, and cut sequences.
7. Caption Agent: Produces dynamic, animated subtitles with word-level highlights.
8. Quality Review Agent: Validates narrative coherence, audio sync, and clip quality before finalizing.

## Execution Principle
- LLMs decide (timestamps, hooks, crop focus, virality scores).
- Deterministic tools execute (FFmpeg cuts, crops, renders; yt-dlp downloads; whisper transcribes).

## Free API References
- Gemini API: Free tier on Google AI Studio (https://aistudio.google.com) - large context window, multimodal video/audio comprehension.
- Groq Cloud: Free tier on Groq Console (https://console.groq.com) - high-speed Whisper audio transcription and Llama-3 inference.
- yt-dlp & FFmpeg: 100% free, open-source local binaries.
