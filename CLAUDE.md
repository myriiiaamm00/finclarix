# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**FinClariX** — a web app that helps young expats and students understand financial contracts (rental agreements, bank account terms, etc.) by analysing them with AI and explaining each clause in plain language, with risk levels (High / Medium / Low) and multilingual support.

Core user flow: upload a PDF → select language → receive per-clause explanations with risk classification (🔴 High / 🟡 Medium / 🟢 Low).

## Status

This repository is in its early/scaffolding stage. No application code exists yet — the tech stack has not been finalized and no build/test commands are defined. Update this file as soon as the stack is chosen and the project is scaffolded.

## When the Stack Is Decided

Add sections here for:
- **Build & dev commands** (e.g., `npm run dev`, `npm run build`, `npm test`, how to run a single test)
- **Tech stack** (framework, AI/LLM integration, PDF parsing library, i18n approach)
- **Architecture** (how PDF upload → clause extraction → AI explanation pipeline works, auth if any, data model)
- **Environment variables** required (AI API keys, etc.)
