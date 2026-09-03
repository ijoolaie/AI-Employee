# Phase 13.6 — Agent Evaluation / Test Center

**Status:** implementation slice complete; CI evidence pending

## Contract

Phase 13.6 adds a deterministic, side-effect-free evaluation boundary for completed Agent/Test Center runs. The evaluator is intentionally a pure application service: it does not execute arbitrary test code, mutate run state, call models, or access credentials.

Supported expectations are:

- exact JSON result equality (`equals`);
- required and forbidden result keys;
- explicit approval requirement;
- required evidence keys.

Results are immutable `EvaluationResult` values containing pass/fail, a deterministic score, reasons, and the evaluation contract version.

## Safety negatives

The evaluator rejects result/evidence payloads containing keys associated with prompts, memory, embeddings, secrets, tokens, passwords, authorization material, tool arguments, or failure details. This is a negative boundary test, not a claim that arbitrary payloads are safe to persist elsewhere.

Approval-gated cases fail closed unless the supplied approval state is `approved`.

## Evidence boundary

Evaluation consumes already-produced Test Center result/evidence payloads and classifies its output as engineering/product evidence. It does not imply production acceptance or customer acceptance.

## Verification target

- deterministic unit tests;
- approval-path negative/positive coverage;
- sensitive-payload negative coverage;
- terminal-run lifecycle guard;
- CI, CodeQL and Architecture Guard on the pull request.

Issue: #240
