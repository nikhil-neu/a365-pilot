# a365-toolkit — capability overview

One administrator workflow across Entra, Defender, Purview and Sentinel.

Discover what is missing, prepare a reviewable deployment plan, execute approved changes and establish which controls actually work.

| Service | Capability | Delivery |
| --- | --- | --- |
| Entra | Create report-only high-risk agent CA; separately promote or disable the policy. | Approved changes |
| Defender | Read available hunting evidence; deploy the XDR-to-Sentinel connector. | Reads + deployment |
| Purview | Enable unified audit; create a scoped DLP policy and rule in simulation mode. | Approved changes |
| Sentinel | Workspace, connectors, 3 hunts, watchlist, 2 rules, workbook and incident-task automation. | Deploy + activate |

## Deployment sequence

1  Select tenant and workload scope. 2  Assess prerequisites and existing settings. 3  Review and approve each exact plan. 4  Deploy, then verify data and behavior. 5  Approve activation; review drift afterward.

## Current boundaries

Development/test live targets only. Defender Security for AI setup is separate. DLP enforcement is not automated. Response playbooks are human procedures; executable response runbooks are planned.

Service licenses, permissions and availability remain prerequisites. Created resources and successful readback do not establish runtime protection.

DEVELOPMENT STATUS  |  Live deployment and production readiness are not yet validated.

[Download PDF](assets/a365-toolkit-one-pager.pdf)
