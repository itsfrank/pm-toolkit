---
title: Tern Replay architecture
page_id: 7103
url: https://tern.wiki.example/spaces/TERN/pages/7103
space: TERN
path: TERN > Engineering
modified: 2026-08-20
labels: [architecture]
size_chars: 387
---

# Tern Replay architecture

## Pipeline
Browser and mobile SDKs send compressed snapshot batches to the Tern capture API (us-west-2).
A stream processor stitches batches into sessions and writes them to object storage.

## Limits
- Maximum session length 4 hours; longer sessions are split.
- Capture API accepts up to 3,000 batches per second per workspace.

## Ownership
Replay platform team, tech lead Ivo Marsh.
