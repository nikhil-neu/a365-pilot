window.FILE_GOVERNANCE_SAMPLE = {
  "schemaVersion": 1,
  "dataKind": "sample",
  "name": "File governance demonstration",
  "tenantId": "fictional-tenant",
  "environment": "Demo sandbox",
  "capturedAt": "2026-10-14T09:00:00Z",
  "complete": false,
  "files": [
    {
      "id": "budget",
      "name": "FY27 budget.xlsx",
      "site": "Finance / Planning",
      "location": "https://sharepoint.example/sites/budget/FY27%20budget.xlsx",
      "agents": [
        {
          "id": "budget-assistant",
          "name": "Budget assistant",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        {
          "id": "leadership-briefing",
          "name": "Leadership briefing",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      ],
      "evidence": {
        "source": "Fictional file inventory",
        "checkedAt": "2026-10-14T09:00:00Z"
      },
      "observations": {
        "container": {
          "value": "Confidential",
          "state": "known",
          "evidence": {
            "source": "Fictional container observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "label": {
          "value": "Unlabeled",
          "state": "known",
          "evidence": {
            "source": "Fictional label observation \u2014 Confirmed unlabeled",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "sharing": {
          "value": "Anonymous link",
          "state": "known",
          "evidence": {
            "source": "Fictional sharing observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "dlp": {
          "value": "Simulation only",
          "state": "known",
          "evidence": {
            "source": "Fictional dlp observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "access": {
          "value": "Anonymous link present; agent-specific effective access not verified",
          "state": "known",
          "evidence": {
            "source": "Fictional access observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "inheritance": {
          "value": "File-specific sharing link; library permissions also inherited",
          "state": "known",
          "evidence": {
            "source": "Fictional inheritance observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "policy": {
          "value": "Finance sensitive data",
          "state": "known",
          "evidence": {
            "source": "Fictional policy observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "rule": {
          "value": "Financial information \u00b7 simulation without notifications",
          "state": "known",
          "evidence": {
            "source": "Fictional rule observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "exclusion": {
          "value": "No exclusion found in the sampled policy scope",
          "state": "known",
          "evidence": {
            "source": "Fictional exclusion observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "runtime": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional runtime observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "owner": {
          "value": "Finance data owner",
          "state": "known",
          "evidence": {
            "source": "Fictional owner observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "labelName": {
          "state": "notApplicable",
          "value": null,
          "evidence": {
            "source": "Fictional label observation \u2014 Confirmed unlabeled",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      }
    },
    {
      "id": "supplier",
      "name": "Supplier agreements.docx",
      "site": "Procurement / Contracts",
      "location": "https://sharepoint.example/sites/supplier/Supplier%20agreements.docx",
      "agents": [
        {
          "id": "procurement-assistant",
          "name": "Procurement assistant",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      ],
      "evidence": {
        "source": "Fictional file inventory",
        "checkedAt": "2026-10-14T09:00:00Z"
      },
      "observations": {
        "container": {
          "value": "Internal",
          "state": "known",
          "evidence": {
            "source": "Fictional container observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "label": {
          "value": "Labeled",
          "state": "known",
          "evidence": {
            "source": "Fictional label observation \u2014 Confidential",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "sharing": {
          "value": "External guest",
          "state": "known",
          "evidence": {
            "source": "Fictional sharing observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "dlp": {
          "value": "Scope excluded",
          "state": "known",
          "evidence": {
            "source": "Fictional dlp observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "access": {
          "value": "Guest permission recorded; guest use and agent effective access not verified",
          "state": "known",
          "evidence": {
            "source": "Fictional access observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "inheritance": {
          "value": "Guest access inherited from site membership",
          "state": "known",
          "evidence": {
            "source": "Fictional inheritance observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "policy": {
          "value": "Contract information protection",
          "state": "known",
          "evidence": {
            "source": "Fictional policy observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "rule": {
          "value": "Sensitive contracts \u00b7 enabled",
          "state": "known",
          "evidence": {
            "source": "Fictional rule observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "exclusion": {
          "value": "Procurement site explicitly excluded",
          "state": "known",
          "evidence": {
            "source": "Fictional exclusion observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "runtime": {
          "value": "Observed retrieval",
          "state": "known",
          "evidence": {
            "source": "Fictional runtime observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "owner": {
          "value": "Procurement data owner",
          "state": "known",
          "evidence": {
            "source": "Fictional owner observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "labelName": {
          "state": "known",
          "value": "Confidential",
          "evidence": {
            "source": "Fictional label observation \u2014 Confidential",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      }
    },
    {
      "id": "people",
      "name": "Workforce plan.xlsx",
      "site": "People / Planning",
      "location": "https://sharepoint.example/sites/people/Workforce%20plan.xlsx",
      "agents": [
        {
          "id": "people-assistant",
          "name": "People assistant",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      ],
      "evidence": {
        "source": "Fictional file inventory",
        "checkedAt": "2026-10-14T09:00:00Z"
      },
      "observations": {
        "container": {
          "value": "Confidential",
          "state": "known",
          "evidence": {
            "source": "Fictional container observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "label": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional label observation \u2014 Unknown",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "sharing": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional sharing observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "dlp": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional dlp observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "access": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional access observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "inheritance": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional inheritance observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "policy": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional policy observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "rule": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional rule observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "exclusion": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional exclusion observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "runtime": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional runtime observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "owner": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional owner observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "labelName": {
          "state": "unknown",
          "value": null,
          "evidence": {
            "source": "Fictional label observation \u2014 Unknown",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      }
    },
    {
      "id": "policy",
      "name": "Travel policy.pdf",
      "site": "Policies / Published",
      "location": "https://sharepoint.example/sites/policy/Travel%20policy.pdf",
      "agents": [
        {
          "id": "people-assistant",
          "name": "People assistant",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        {
          "id": "policy-assistant",
          "name": "Policy assistant",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      ],
      "evidence": {
        "source": "Fictional file inventory",
        "checkedAt": "2026-10-14T09:00:00Z"
      },
      "observations": {
        "container": {
          "value": "Internal",
          "state": "known",
          "evidence": {
            "source": "Fictional container observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "label": {
          "value": "Labeled",
          "state": "known",
          "evidence": {
            "source": "Fictional label observation \u2014 Internal",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "sharing": {
          "value": "Internal readers",
          "state": "known",
          "evidence": {
            "source": "Fictional sharing observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "dlp": {
          "value": "Policy in scope",
          "state": "known",
          "evidence": {
            "source": "Fictional dlp observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "access": {
          "value": "Internal group grant observed; membership expansion not assessed",
          "state": "known",
          "evidence": {
            "source": "Fictional access observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "inheritance": {
          "value": "Library permissions inherited",
          "state": "known",
          "evidence": {
            "source": "Fictional inheritance observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "policy": {
          "value": "Internal information protection",
          "state": "known",
          "evidence": {
            "source": "Fictional policy observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "rule": {
          "value": "Sensitive information \u00b7 enabled; predicate match not tested",
          "state": "known",
          "evidence": {
            "source": "Fictional rule observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "exclusion": {
          "value": "No exclusion found in sampled policy",
          "state": "known",
          "evidence": {
            "source": "Fictional exclusion observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "runtime": {
          "value": "Observed retrieval",
          "state": "known",
          "evidence": {
            "source": "Fictional runtime observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "owner": {
          "value": "Policy data owner",
          "state": "known",
          "evidence": {
            "source": "Fictional owner observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "labelName": {
          "state": "known",
          "value": "Internal",
          "evidence": {
            "source": "Fictional label observation \u2014 Internal",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      }
    },
    {
      "id": "notes",
      "name": "Project notes.docx",
      "site": "Delivery / Working",
      "location": "https://sharepoint.example/sites/notes/Project%20notes.docx",
      "agents": [
        {
          "id": "delivery-assistant",
          "name": "Delivery assistant",
          "relationship": "configured-source",
          "evidence": {
            "source": "Fictional configured source mapping",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      ],
      "evidence": {
        "source": "Fictional file inventory",
        "checkedAt": "2026-10-14T09:00:00Z"
      },
      "observations": {
        "container": {
          "value": "Internal",
          "state": "known",
          "evidence": {
            "source": "Fictional container observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "label": {
          "value": "Unlabeled",
          "state": "known",
          "evidence": {
            "source": "Fictional label observation \u2014 Confirmed unlabeled",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "sharing": {
          "value": "Internal readers",
          "state": "known",
          "evidence": {
            "source": "Fictional sharing observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "dlp": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional dlp observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "access": {
          "value": "Internal readers observed; agent effective access not verified",
          "state": "known",
          "evidence": {
            "source": "Fictional access observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "inheritance": {
          "value": "Site permissions inherited",
          "state": "known",
          "evidence": {
            "source": "Fictional inheritance observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "policy": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional policy observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "rule": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional rule observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "exclusion": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional exclusion observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "runtime": {
          "value": null,
          "state": "unknown",
          "evidence": {
            "source": "Fictional runtime observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "owner": {
          "value": "Delivery data owner",
          "state": "known",
          "evidence": {
            "source": "Fictional owner observation",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        },
        "labelName": {
          "state": "notApplicable",
          "value": null,
          "evidence": {
            "source": "Fictional label observation \u2014 Confirmed unlabeled",
            "checkedAt": "2026-10-14T09:00:00Z"
          }
        }
      }
    }
  ]
};
