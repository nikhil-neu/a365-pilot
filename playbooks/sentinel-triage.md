# Sentinel pilot incident triage

1. Confirm tenant, workspace, analytic rule ID and incident time. Check that the alert
   came from the intended pilot rule and not a similarly named resource.
2. Correlate agent IDs with the approved watchlist and registry. Pilot-user DLP events
   alone do not establish agent involvement. Check the original alert's entity mapping
   in the portal without exporting prompt or response content.
3. Verify connector health, event freshness and the effective DLP policy/rule scope.
   Empty or missing evidence stays unknown. Save identifiers, timestamps and evidence
   references in the access-controlled incident record.
4. Follow [containment](containment.md) to select an exact response. Any blocking,
   permission change or other containment needs a new concrete plan and human approval.
5. Record the decision, evidence, approved action and readback. Check runtime effects
   separately; do not close the incident solely because a write returned success.

The Sentinel automation resource only adds a task referencing this playbook, and is
deployed disabled. It does not run code, revoke access or send communications.
