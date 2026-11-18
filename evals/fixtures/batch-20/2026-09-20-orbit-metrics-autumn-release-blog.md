# What's new at Orbit Metrics: the Autumn release

Source: orbitmetrics.example/blog (public blog post, copied) | Author: Orbit Metrics product team | Published: 2026-09-20

Autumn is here, and so is a big batch of improvements to Orbit Metrics. Here is what we shipped over the last few weeks, and what is coming next.

## Real-time anomaly detection (in preview)
Our headline feature this season is real-time anomaly detection. Orbit now watches your key metrics as events arrive and flags unusual movements without you having to set a threshold by hand. Real-time anomaly detection is available on the Enterprise plan only and is labelled "in preview" while we gather feedback from early users. Preview features may change before general availability, and we will share pricing details later.

How it works, in short:
- Pick a metric or a funnel step.
- Orbit learns a baseline from recent history, including weekday and seasonal patterns.
- When a value falls outside the expected band, the anomaly shows up in the feed and can be sent to Slack, email or a webhook.

Early users told us the biggest win was catching broken tracking within minutes. We are tuning sensitivity controls based on that feedback.

## Hosting: a new region in Frankfurt
We know that where data lives matters to many of you. Our Frankfurt hosting region launched in September 2026. New workspaces can choose it at sign-up, and existing customers can talk to their account team about moving. Frankfurt joins our existing US and UK regions.

## Dashboard improvements
- Faster loading for dashboards with more than 20 tiles.
- A new "compare to previous period" toggle on every chart.
- Folder-level sharing, so teams can give access to a whole group of dashboards at once.
- Dark mode for the whole app, finally.

## Integrations
- Two new warehouse connectors for batch imports.
- Improved Slack digest with chart thumbnails.
- A refreshed API reference with runnable examples.

## Customer spotlight
Fernwood Outdoor, a mid-sized retailer, told us the new folder sharing cut their dashboard request backlog in half. "We used to answer the same access questions every week," said their head of data. "Now it is a two-click job."

## Coming up
We are working on:
1. Saved segments shared across workspaces.
2. A mobile app for viewing dashboards.
3. More granular roles.

We will write about these in the winter release post. As always, you can see the full changelog in the help centre, and you can tell us what you want next through the feedback form.

## Thank you
Thanks to everyone who joined our beta programme and sent in feedback. If you want to try anomaly detection or any of the other features, contact your account manager or start a trial from our website.

The Orbit Metrics team

## Under the hood: engineering notes
A few smaller changes that did not make the headline list:
- We moved the event ingestion queue to a new storage layer, which reduced tail latency for large batch imports.
- Funnel queries now stream partial results, so the first rows appear sooner on long date ranges.
- The CSV export no longer truncates column headers longer than 64 characters.
- Single sign-on setup has a guided checklist, with clearer errors for mismatched certificates.
- We fixed a rare bug where a deleted dashboard could still show in search for a few minutes.

## Frequently asked questions
**Do I need to change anything to get the new features?** No. Everything rolls out automatically except preview features, which your workspace admin can switch on from the settings page.

**Will existing dashboards change?** No. Existing dashboards keep their layout and filters.

**Where can I read more?** The help centre has a page for each feature, and our community forum has a thread for feedback on the Autumn release.
