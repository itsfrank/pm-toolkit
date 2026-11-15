# Initiative brief: Regional access policies (RAP)

Owner: Govern team. PM: Aisha Karim. EM: Lukas Brenner. Date: 2026-09-15. Status: In build.

## Problem
Enterprise admins want to restrict who can see their analytics data based on where the
viewer is and where the data lives. Today Kestrel Govern only supports role-based access.

## What we're building
- Policies that allow or deny access to a tenant's data by viewer location (country list).
- Policies that restrict Kestrel employee access (support, success) to approved locations.
- Audit log entries for every policy decision.

## Timeline
- Private beta: 2026-11 (target).
- GA: 2027 H1 (target, not committed).

## Dependencies and overlaps
- Needs the tenant home region from Project Fjord metadata.
- Support console integration (Lookout) not yet scoped with Support Engineering.

## Packaging
Undecided. Pricing & Packaging to advise.
