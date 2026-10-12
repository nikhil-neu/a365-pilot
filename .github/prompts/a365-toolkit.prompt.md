---
description: Start the guided a365-toolkit administrator setup and approval workflow.
agent: a365-toolkit
---

Follow the [a365-toolkit agent](../agents/a365-toolkit.agent.md) and
[chat deployment guide](../../docs/chat-deployment.md). Start offline. Make the first administrator interaction a native
`vscode/askQuestions` Action selector from the agent's structured-input contract.
Use native multi-select for services and native text entry for missing values; use
native single-select for every approval. Do not ask for typed chat answers. If the
tool is unavailable, explain the compatibility requirement and stop. Guide this administrator from selection through prerequisite
checks, exact plans, explicit approval in chat, execution and verification. Do not execute
any tenant change until its concrete plan has been displayed and explicitly approved.
