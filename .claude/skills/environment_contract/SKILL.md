---
name: environment-contract
description: >-
  Establish or review the public interface between a grid environment
  and a learner before implementation or integration.
---

# Environment contract procedure

1. Read the task requirements and existing public interface documentation.
2. Identify unresolved requirements. Do not silently invent them.
3. Establish:
   - Observation representation and valid values.
   - Action representation and valid values.
   - reset() arguments and return values.
   - step() arguments and return values.
   - Meaning of termination and truncation.
   - Seeding behavior, if required.
   - Information the learner is permitted to access.
4. Separate public interface details from private simulator rules.
5. Return the contract and unresolved questions to the orchestrator.

# Output format

## Public interface
Document signatures and value meanings.

## Learner-visible information
List permitted observations and interface metadata.

## Private simulator details
List categories that must not be passed to the learner specialist.
Do not reproduce private implementation details in the handoff.

## Assumptions and blockers
State unresolved decisions explicitly.
