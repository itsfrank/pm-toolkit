---
title: PRD: Replay privacy masking
page_id: 7112
url: https://tern.wiki.example/spaces/TERN/pages/7112
space: TERN
path: TERN > Product
modified: 2026-08-28
labels: [prd]
size_chars: 297
---

# PRD: Replay privacy masking

Status: approved 2026-08-28. Owner: Ola Brandt.

## Problem
Customers worry that replays capture personal data typed into forms.

## Requirements
- R1: mask all text inputs by default.
- R2: let admins unmask specific fields by CSS selector.
- R3: never record password fields, even when unmasked.
