# Usage Alerts: first 30 days after GA

Owner: Sam Whitlock, PM | Status: reviewed | Updated: 2026-10-05

This note reports early adoption and quality numbers for Usage Alerts after general availability. Measurements cover the first 30 days. Sources: product analytics for workspace activity, and the notification service logs for muting behaviour.

## Summary
- 1,240 workspaces created at least one alert in the first 30 days after GA.
- The false-positive rate (alerts muted within an hour as noise) is 3.2%.
- Email remains the most used channel; webhooks are second.
- No major incidents were attributed to the alerting service during the period.

## Adoption
| Segment | Observation |
|---|---|
| Team plan workspaces | Most of the alert creators; many created several alerts |
| Enterprise workspaces | Fewer, but heavier users, often with webhooks into on-call tools |
| Free workspaces | Small share; most reached the limit quickly |

Typical first alerts were on event volume drops for a key event, and on error-event spikes. Several customers asked about anomaly detection, which remains a non-goal for this release.

## Quality
We define a false positive as an alert that the recipient mutes within an hour of firing, treating that as a signal the alert was noise. This is a proxy and not a perfect measure: some users mute alerts for other reasons. The rate is within the guardrail we set in the PRD, and spam reports on notification emails stayed low.

Contributing causes of noisy alerts, from support tickets:
1. Thresholds set too close to normal daily variation.
2. Alerts on low-volume events where small changes cross the threshold.
3. Alerts set on weekends when traffic is naturally lower.

## Acknowledgement
Roughly half of fired alerts were opened or muted within 24 hours. The target of 60% was set for the end of beta; this is being tracked and discussed in the next product review.

## Feedback themes
- Users want alerts that account for weekday patterns.
- Users want to send alerts to chat tools directly, without webhooks.
- Admins want a view of all alerts in a workspace.

## Next steps
| Action | Owner |
|---|---|
| Add guidance on thresholds in the docs | Docs and Sam Whitlock |
| Explore a workspace alert overview | Insights team |
| Review acknowledgement results | Sam Whitlock, Jonah Feld |
| Revisit noisy-alert causes with Support | Owen Hale |

## Method notes
Workspaces counted once regardless of how many alerts they created. Internal test workspaces are excluded. Muting events are counted per alert firing and per recipient.

## Appendix: notification delivery
Delivery success for email was high, and webhook failures were mostly customer endpoints returning errors; the retry policy of three retries with backoff handled most of them. A small number of customers reported delayed emails that turned out to be spam filtering on their side. Support has a macro for this case.

## Appendix: who to ask
- Metrics definitions: Sam Whitlock.
- Notification service: Infrastructure, Mei Arakawa.
- Support patterns: Owen Hale.
- Dashboard integration: the Insights team, Kai Lund.

## Appendix: reading this note
All figures cover only the first 30 days. Please do not extrapolate to later months or compare directly with other products' definitions of noise.
