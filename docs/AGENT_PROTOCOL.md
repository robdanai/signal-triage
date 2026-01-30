# Agent Communication Protocol

This document defines the communication protocol for Signal Triage agents, enabling cloud-based AI agents to coordinate and execute pipeline tasks.

---

## Protocol Version

**Version:** 1.0.0  
**Last Updated:** January 29, 2026

---

## Message Format

### Request Message

All agent execution requests follow this JSON schema:

```json
{
  "agent": "agent_name",
  "task": "task_identifier",
  "input": {
    "document_path": "path/to/document.pdf",
    "document_url": "https://example.com/filing.pdf",
    "options": {
      "industry": "Retail",
      "geography": "US",
      "output_format": "json"
    }
  },
  "context": {
    "session_id": "uuid-v4",
    "execution_id": "uuid-v4",
    "prior_agents": ["author", "librarian"],
    "handoff_data": {
      "document_chunks": [...],
      "provenance": {...}
    },
    "config_version": "1.0.0",
    "timestamp": "2026-01-29T12:00:00Z"
  },
  "metadata": {
    "requester": "analyst@company.com",
    "priority": "normal",
    "timeout_seconds": 300
  }
}
```

### Response Message

All agent responses follow this JSON schema:

```json
{
  "agent": "agent_name",
  "status": "success|failed|partial",
  "output": {
    "primary_result": {...},
    "metadata": {...}
  },
  "handoff_to": "next_agent_name",
  "handoff_data": {
    "key": "value"
  },
  "execution_metadata": {
    "execution_time_ms": 1234,
    "confidence_score": 0.95,
    "warnings": [],
    "errors": []
  },
  "provenance": {
    "sources": [
      {
        "type": "document",
        "path": "path/to/document.pdf",
        "pages": [1, 2, 3],
        "sections": ["7.02", "7.03"]
      },
      {
        "type": "api",
        "provider": "SEC EDGAR",
        "endpoint": "/cgi-bin/browse-edgar",
        "timestamp": "2026-01-29T12:00:00Z"
      }
    ]
  },
  "audit_trail": {
    "config_version": "1.0.0",
    "agent_version": "1.0.0",
    "execution_id": "uuid-v4",
    "timestamp": "2026-01-29T12:05:00Z"
  }
}
```

---

## Agent-Specific Protocols

### Author (Ingestion & APIs)

**Task:** `ingest_document`

**Request:**
```json
{
  "agent": "author",
  "task": "ingest_document",
  "input": {
    "document_path": "path/to/document.pdf",
    "document_type": "credit_agreement|indenture|10k|8k"
  }
}
```

**Response:**
```json
{
  "agent": "author",
  "status": "success",
  "output": {
    "document_chunks": [
      {
        "text": "chunk text",
        "page": 1,
        "section": "Article VII",
        "start_idx": 0,
        "end_idx": 500
      }
    ],
    "provenance": {
      "source_path": "path/to/document.pdf",
      "page_count": 150,
      "ingestion_timestamp": "2026-01-29T12:00:00Z"
    }
  },
  "handoff_to": "librarian",
  "handoff_data": {
    "document_chunks": [...],
    "document_type": "credit_agreement"
  }
}
```

---

### Librarian (Covenant Extraction)

**Task:** `extract_covenants`

**Request:**
```json
{
  "agent": "librarian",
  "task": "extract_covenants",
  "input": {
    "document_chunks": [...],
    "extraction_options": {
      "include_lme_detection": true,
      "include_capital_structure": true,
      "include_ebitda_analysis": true
    }
  },
  "context": {
    "handoff_data": {
      "document_chunks": [...],
      "document_type": "credit_agreement"
    }
  }
}
```

**Response:**
```json
{
  "agent": "librarian",
  "status": "success",
  "output": {
    "covenants": [
      {
        "type": "leverage_ratio",
        "limit": "6.5",
        "section": "7.01",
        "page": 45,
        "evidence": "The Borrower shall not permit..."
      }
    ],
    "baskets": [
      {
        "basket_type": "asset_sale",
        "limit_amount": "100000000",
        "currency": "USD",
        "section": "7.02(b)",
        "page": 47
      }
    ],
    "signals": [
      {
        "type": "dropdown",
        "severity": "high",
        "category": "lme",
        "evidence": "transfer to unrestricted subsidiary",
        "section": "7.02",
        "page": 48
      }
    ],
    "collateral_leakage_flags": [
      {
        "type": "unrestricted_subsidiary_transfer",
        "risk_score": 8.5,
        "estimated_leakage_amount": "200000000",
        "section": "7.02",
        "page": 48
      }
    ],
    "capital_structure": {
      "tranches": [
        {
          "name": "First Lien Term Loan",
          "amount": "500000000",
          "seniority": "senior_secured",
          "page": 12
        }
      ]
    },
    "ebitda_analysis": {
      "risk_score": 7.2,
      "high_risk_addbacks": ["run_rate_synergies", "anticipated_savings"],
      "page": 89
    }
  },
  "handoff_to": "quant",
  "handoff_data": {
    "baskets": [...],
    "covenant_limits": {...},
    "collateral_leakage_flags": [...]
  },
  "provenance": {
    "sources": [
      {"type": "document", "path": "...", "pages": [45, 47, 48]}
    ]
  }
}
```

---

### Quant (Waterfall & Sensitivity)

**Task:** `calculate_waterfall`

**Request:**
```json
{
  "agent": "quant",
  "task": "calculate_waterfall",
  "input": {
    "enterprise_value": "150000000",
    "tranches": [
      {
        "name": "Senior Secured",
        "amount": "100000000",
        "seniority": 1
      },
      {
        "name": "Mezzanine",
        "amount": "100000000",
        "seniority": 2
      }
    ],
    "collateral_value": "120000000",
    "sensitivity_options": {
      "ev_range": ["100000000", "200000000"],
      "ev_step": "10000000"
    }
  },
  "context": {
    "handoff_data": {
      "collateral_leakage_flags": [
        {
          "estimated_leakage_amount": "20000000"
        }
      ]
    }
  }
}
```

**Response:**
```json
{
  "agent": "quant",
  "status": "success",
  "output": {
    "waterfall": {
      "enterprise_value": "150000000",
      "adjusted_collateral": "100000000",
      "recoveries": [
        {
          "tranche": "Senior Secured",
          "amount": "100000000",
          "recovery_percentage": "1.0",
          "recovery_amount": "100000000"
        },
        {
          "tranche": "Mezzanine",
          "amount": "100000000",
          "recovery_percentage": "0.5",
          "recovery_amount": "50000000"
        }
      ],
      "fulcrum_security": "Mezzanine",
      "apr_violations": []
    },
    "situational_summary": "At EV of $150M, Senior Secured recovers 100%, Mezzanine recovers 50%. Fulcrum is Mezzanine. LME adjustment reduced collateral by $20M.",
    "tornado_drivers": [
      {"variable": "EV", "impact": 0.8},
      {"variable": "Collateral", "impact": 0.5}
    ]
  },
  "handoff_to": "auditor",
  "handoff_data": {
    "recovery_model": {...},
    "situational_summary": "..."
  }
}
```

---

### Benchmarker (Market Context)

**Task:** `get_market_context`

**Request:**
```json
{
  "agent": "benchmarker",
  "task": "get_market_context",
  "input": {
    "ticker": "ABC",
    "industry": "Retail",
    "geography": "US",
    "analysis_date": "2026-01-29"
  }
}
```

**Response:**
```json
{
  "agent": "benchmarker",
  "status": "success",
  "output": {
    "market_multiples": {
      "ebitda_multiple": "6.5",
      "source": "SEC EDGAR comparable transactions",
      "date": "2026-01-29"
    },
    "precedent_recovery_rates": [
      {
        "company": "Comparable Corp",
        "industry": "Retail",
        "year": 2025,
        "tranche": "1st Lien",
        "recovery_percentage": "0.65",
        "source": "Court filings"
      }
    ],
    "critical_variance_flags": [
      {
        "type": "recovery_divergence",
        "model_value": "0.90",
        "market_value": "0.65",
        "variance": "0.25",
        "severity": "high"
      }
    ],
    "yield_spreads": {
      "current_spread_bps": 850,
      "benchmark": "US Treasury 10Y",
      "date": "2026-01-29"
    }
  },
  "handoff_to": "auditor",
  "handoff_data": {
    "precedent_recovery_rates": [...],
    "critical_variance_flags": [...]
  },
  "provenance": {
    "sources": [
      {
        "type": "api",
        "provider": "SEC EDGAR",
        "timestamp": "2026-01-29T12:00:00Z"
      }
    ]
  }
}
```

---

### Auditor (Stress-Testing)

**Task:** `stress_test_model`

**Request:**
```json
{
  "agent": "auditor",
  "task": "stress_test_model",
  "input": {
    "recovery_model": {...},
    "precedent_recovery_rates": [...],
    "critical_variance_flags": [...],
    "test_scenarios": ["base", "downside", "severe_downside"]
  }
}
```

**Response:**
```json
{
  "agent": "auditor",
  "status": "success",
  "output": {
    "stress_test_results": {
      "base": {"senior_recovery": "1.0", "junior_recovery": "0.5"},
      "downside": {"senior_recovery": "0.9", "junior_recovery": "0.0"},
      "severe_downside": {"senior_recovery": "0.6", "junior_recovery": "0.0"}
    },
    "apr_validation": {
      "passed": true,
      "violations": []
    },
    "variance_reconciliation": {
      "critical_variances": 1,
      "reconciled": 0,
      "unreconciled": 1,
      "details": [
        {
          "type": "recovery_divergence",
          "status": "unreconciled",
          "explanation": "Model assumes higher recovery; requires justification"
        }
      ]
    },
    "audit_trail": {
      "config_version": "1.0.0",
      "document_sources": ["credit_agreement.pdf"],
      "market_data_dates": ["2026-01-29"],
      "reproducibility_hash": "abc123"
    },
    "pass_fail_status": "failed",
    "gate_recommendation": "do_not_publish"
  },
  "handoff_to": "reporter",
  "handoff_data": {
    "pass_fail_status": "failed",
    "audit_trail": {...}
  }
}
```

---

### Comparator (Delta Analysis)

**Task:** `compare_analyses`

**Request:**
```json
{
  "agent": "comparator",
  "task": "compare_analyses",
  "input": {
    "current_analysis": {...},
    "prior_analysis": {...},
    "comparison_type": "temporal|peer"
  }
}
```

**Response:**
```json
{
  "agent": "comparator",
  "status": "success",
  "output": {
    "score_deltas": {
      "prior_score": 45,
      "current_score": 62,
      "delta": 17,
      "change_percentage": 37.8
    },
    "tier_deltas": {
      "prior_tier": "medium",
      "current_tier": "high",
      "tier_change": "upgraded"
    },
    "new_signals": [
      {"type": "dropdown", "severity": "high", "first_seen": "2026-01-29"}
    ],
    "removed_signals": [],
    "material_change_narrative": "Score increased 17 points (+37.8%) due to new dropdown risk identified in Section 7.02. Tier upgraded from Medium to High."
  },
  "handoff_to": "reporter",
  "handoff_data": {
    "comparison_summary": {...}
  }
}
```

---

### Reporter (Final Report)

**Task:** `generate_report`

**Request:**
```json
{
  "agent": "reporter",
  "task": "generate_report",
  "input": {
    "all_agent_outputs": {...},
    "report_type": "single_document|portfolio_summary",
    "output_format": "json|markdown|pdf"
  },
  "context": {
    "handoff_data": {
      "auditor_pass_fail": "failed",
      "audit_trail": {...},
      "comparison_summary": {...}
    }
  }
}
```

**Response:**
```json
{
  "agent": "reporter",
  "status": "success",
  "output": {
    "report": {
      "document_name": "ABC Corp Credit Agreement",
      "analysis_date": "2026-01-29",
      "score": 62,
      "tier": "high",
      "top_signals": [
        {
          "type": "dropdown",
          "severity": "high",
          "evidence": "...",
          "section": "7.02",
          "page": 48
        }
      ],
      "recovery_summary": {
        "enterprise_value": "150000000",
        "fulcrum_security": "Mezzanine",
        "senior_recovery": "1.0",
        "junior_recovery": "0.5"
      },
      "market_context": {
        "ebitda_multiple": "6.5",
        "precedent_recovery": "0.65",
        "critical_variance": true
      },
      "comparison": {
        "vs_prior": "+17 points",
        "material_changes": "New dropdown risk"
      },
      "analyst_checklist": [
        "Investigate unrestricted subsidiary transfer language",
        "Confirm collateral coverage assumptions"
      ]
    },
    "published": false,
    "publish_gate_reason": "Auditor failed: unreconciled Critical Variance",
    "audit_trail": {...}
  }
}
```

---

## REST API Endpoints

### Agent Execution

**Endpoint:** `POST /api/v1/agent/{agent_name}/execute`

**Request Body:** Agent request message (see above)

**Response:** Agent response message (see above)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/agent/librarian/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent": "librarian",
    "task": "extract_covenants",
    "input": {
      "document_path": "path/to/document.pdf"
    }
  }'
```

### Pipeline Execution

**Endpoint:** `POST /api/v1/pipeline/execute`

**Request Body:**
```json
{
  "document_path": "path/to/document.pdf",
  "options": {
    "industry": "Retail",
    "geography": "US",
    "skip_audit_gate": false
  }
}
```

**Response:**
```json
{
  "execution_id": "uuid-v4",
  "status": "running|completed|failed",
  "current_agent": "quant",
  "progress": {
    "completed_agents": ["author", "librarian"],
    "remaining_agents": ["quant", "benchmarker", "auditor", "comparator", "reporter"]
  },
  "result": {...}
}
```

### Agent Status

**Endpoint:** `GET /api/v1/agent/{agent_name}/status`

**Response:**
```json
{
  "agent": "librarian",
  "status": "available|busy|error",
  "version": "1.0.0",
  "health": "healthy",
  "metrics": {
    "avg_execution_time_ms": 1234,
    "success_rate": 0.98,
    "last_execution": "2026-01-29T12:00:00Z"
  }
}
```

---

## WebSocket Protocol (Real-Time Updates)

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/pipeline');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Agent ${update.agent} status: ${update.status}`);
};
```

### Message Types

**Progress Update:**
```json
{
  "type": "progress",
  "execution_id": "uuid-v4",
  "current_agent": "quant",
  "status": "running",
  "progress_percentage": 60,
  "timestamp": "2026-01-29T12:00:00Z"
}
```

**Agent Complete:**
```json
{
  "type": "agent_complete",
  "execution_id": "uuid-v4",
  "agent": "librarian",
  "status": "success",
  "output_summary": {
    "covenants_found": 15,
    "signals_found": 8
  },
  "timestamp": "2026-01-29T12:00:00Z"
}
```

**Pipeline Complete:**
```json
{
  "type": "pipeline_complete",
  "execution_id": "uuid-v4",
  "status": "success",
  "report_id": "uuid-v4",
  "published": true,
  "timestamp": "2026-01-29T12:00:00Z"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "agent": "agent_name",
  "status": "failed",
  "error": {
    "code": "AGENT_ERROR_CODE",
    "message": "Human-readable error message",
    "details": {...},
    "stack_trace": "..."
  },
  "recovery_suggestions": [
    "Check input format",
    "Verify document is readable"
  ]
}
```

### Common Error Codes

| Code | Description | Recovery Action |
|------|-------------|-----------------|
| `INVALID_INPUT` | Input doesn't match schema | Fix request format |
| `DOCUMENT_NOT_FOUND` | Document path doesn't exist | Verify path |
| `EXTRACTION_FAILED` | Couldn't extract covenants | Check document quality |
| `API_RATE_LIMIT` | External API rate limit hit | Wait and retry |
| `AUDITOR_GATE_FAILED` | Auditor blocked publication | Reconcile Critical Variance |
| `TIMEOUT` | Agent execution timeout | Increase timeout or simplify input |

---

## Authentication & Authorization

### API Keys

```bash
# Set API key for cloud deployment
export SIGNAL_TRIAGE_API_KEY="your-api-key"

# Include in requests
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:8000/api/v1/agent/librarian/execute
```

### Rate Limiting

- **Default:** 100 requests/minute per API key
- **Burst:** Up to 10 concurrent pipeline executions
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Monitoring & Observability

### Metrics

- `agent_execution_time_ms` - Time to complete agent task
- `agent_success_rate` - Success rate per agent
- `pipeline_completion_rate` - Full pipeline success rate
- `api_response_time_ms` - API endpoint latency

### Health Checks

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "agents": {
    "author": "healthy",
    "librarian": "healthy",
    "quant": "healthy"
  },
  "external_apis": {
    "sec_edgar": "healthy",
    "redis": "healthy"
  }
}
```

---

## Versioning

Protocol follows semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes to message format
- **MINOR:** Backward-compatible additions
- **PATCH:** Bug fixes

Current version: **1.0.0**
