# Local evidence dashboard

Every `scripts/a365.py --out artifacts/name.json` report also produces `name.md` and `name.html`.
Open the HTML locally for a per-operation view of status, evidence, impact and rollback.
It is static, HTML-escaped, uses a restrictive content security policy and contacts no
external service. It displays the same evidence as the machine-readable report.

The separate [Sentinel pack](../sentinel/README.md) now includes an Azure workbook
against verified Log Analytics tables. Follow [administrator deployment](../docs/admin-deployment.md)
for its approved installation. Defender Advanced Hunting tables are not assumed to exist
in that workspace. Publishing a dashboard or sharing tenant evidence requires its own
explicit instruction. The administrator deployment CLI emits JSON evidence only.

## Agent Knowledge Exposure

Open [the local viewer](knowledge-exposure/index.html) for configured knowledge sources,
container/content classification evidence and advisory review findings. The initial
dataset is fictional sample data. See [format and usage](knowledge-exposure/README.md).
