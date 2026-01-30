---
name: Agent Enhancement
about: Propose an enhancement to one of the 7 agents
title: '[AGENT] '
labels: enhancement, agent
assignees: ''

---

## Agent

Which agent does this enhancement affect?

- [ ] Author (Ingestion & APIs)
- [ ] Librarian (Covenant Extraction)
- [ ] Quant (Waterfall & Sensitivity)
- [ ] Benchmarker (Market Context)
- [ ] Auditor (Stress-Testing)
- [ ] Comparator (Delta Analysis)
- [ ] Reporter (Final Reports)
- [ ] Orchestration (Pipeline)

## Enhancement Description

**Brief summary:**
<!-- Describe the enhancement in 1-2 sentences -->

**Problem it solves:**
<!-- What problem does this enhancement address? -->

**Proposed solution:**
<!-- How would you implement this? -->

## Impact on Other Agents

**Handoffs affected:**
<!-- Which agent handoffs would change? (e.g., Librarian → Quant) -->

**New dependencies:**
<!-- Would this create new dependencies on other agents? -->

## Example

**Input:**
```
<!-- Example input to the agent -->
```

**Expected Output:**
```
<!-- Example output after enhancement -->
```

## Implementation Checklist

- [ ] Update agent code in primary files
- [ ] Update agent mandate (`.cursor/agents/<agent>.md`)
- [ ] Add tests for new functionality
- [ ] Update `agent-registry.json` if interface changes
- [ ] Update `AGENT_PROTOCOL.md` if message format changes
- [ ] Update `ROADMAP.md` if this affects pipeline
- [ ] Update relevant documentation

## Additional Context

<!-- Any additional context, precedents, or research -->

## Related Issues/PRs

<!-- Link to related issues or pull requests -->
