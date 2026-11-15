---
title: Postmortem: replay ingest outage 2026-07
page_id: 7113
url: https://tern.wiki.example/spaces/TERN/pages/7113
space: TERN
path: TERN > Engineering
modified: 2026-07-19
labels: [incident]
size_chars: 224
---

# Postmortem: replay ingest outage 2026-07

On 2026-07-14 the capture API rejected batches for 47 minutes after a certificate expired.
About 8% of sessions that day were incomplete. Action items: certificate expiry alerts in
Lookout, and a runbook for manual rotation.
