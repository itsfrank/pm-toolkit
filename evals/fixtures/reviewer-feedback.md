# Reviewer feedback on the EU data residency PRD draft

Product review, 2026-10-22. Reviewer: staff architect, Connect team (role only).
Artifact: work/2026-10-05-eu-data-residency/prd.md (draft of 2026-10-20)

Verbatim comments:
1. "Nobody looked at Kestrel Connect. Scheduled exports are staged in a US bucket before
   delivery to the customer's bucket, for every tenant. Any residency PRD has to cover
   where exports and integrations move data, not just where it is stored."
2. "Same pattern as the Lookout miss in June: we keep forgetting data paths owned by
   teams that aren't in the main design doc."
3. "I'd prefer a data-flow diagram near the top of the PRD."
