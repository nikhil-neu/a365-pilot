> Superseded: use the [a365-toolkit executive brief](a365-toolkit-executive-brief.md) and [one-pager](a365-toolkit-one-pager.md). This document records the earlier pilot scope.

# Agent 365 Security Operations Pilot

A structured approach to assessing agent security readiness and testing governance controls in a dedicated development or test tenant.

## Purpose

Help administrators establish what is configured, identify evidence gaps, and evaluate controlled changes before considering wider use.

## Capabilities and delivery

| Capability | What the pilot provides | Delivery |
| --- | --- | --- |
| Assess readiness | Read tenant identity, licenses, roles, policies and available registry, risk and telemetry evidence. | Tenant reads |
| Plan controls | Preview selected scope, required permissions, expected impact and recovery steps. | Offline + reads |
| Build artifacts | Generate neutral configuration, reviewable plans and JSON, Markdown and HTML reports. | Offline |
| Validate and review | Run mocked tests, compare inventory with an approved baseline and inspect control evidence. | Offline + reads |
| Apply changes | Create report-only Conditional Access; explicitly promote or disable it; block or unblock a package. | Approved write |
| Prepare response | Simulate containment for a named agent and review response scope, evidence and recovery. | Offline + reads |

## Controlled pilot approach

Explicit tenant selection. Read-only by default. Human approval before changes. Report-only controls first. Preserve evidence and recovery instructions. No prompt or response content collection by the toolkit.

## Prerequisites and boundaries

Live checks depend on licensing, permissions and service availability. Purview configuration, connector setup and platform-specific actions use documented administrator steps. Beta and preview dependencies are identified.

Coverage: Entra, Agent 365, Defender, Purview, Foundry and Copilot Studio; supported custom and third-party agents. Coverage combines automation and runbooks.

Configuration evidence does not establish runtime enforcement.

[Current toolkit executive brief PDF](assets/a365-toolkit-executive-brief.pdf)
