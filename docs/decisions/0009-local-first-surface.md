# 0009 — Local-first surface: CLI + file exports, no web server

**Status:** Accepted · 2026-07-22 · supersedes the API/HUD tier in SPEC §2/§4

## Context
The brainstorm centered a Next.js HUD talking to a FastAPI gateway. But this tool
is run locally by an allocator; the whole point of the `./amb` harness (ADR-0001)
is that the CLI *is* the interface. A web server exists only to bridge a browser
to the core over HTTP — with no browser in the loop, FastAPI/uvicorn add a
dependency, a process to run, and an attack surface for zero local benefit. The
operator explicitly flagged this.

## Decision
The product surface is the **CLI plus file deliverables**: the memo is exported as
Markdown, JSON (audit map), a self-contained Equi-styled **HTML** (print-to-PDF in
any browser), and a formatted **XLSX** workbook (shortlist · all-fund metrics ·
audit trail). No FastAPI, no uvicorn, no Next.js. `fastapi`/`uvicorn` are removed
from dependencies; `./amb serve`/`ui` are replaced by `./amb export`.

## Consequences
- One fewer server to run and secure; `./amb setup` stays lean and offline-capable.
- Deliverables are portable artifacts an IC can open directly (Excel, browser, PDF).
- A browser HUD remains *possible* later — the core is untouched and already has a
  clean seam — but it is explicitly out of scope until a real multi-user need appears.

## Alternatives considered
- **Keep FastAPI + Next.js HUD (as specified):** a lot of surface to build and run
  for a single-user local tool; the CLI already covers every workflow.
- **FastAPI now, HUD later:** still pays the server cost immediately with no
  consumer; defer the whole tier until the HUD is actually being built.
