# W22 — SEO & Growth Employee

**Status:** IMPLEMENTATION / REAL-STACK EVIDENCE IN PROGRESS  
**Issue:** #910

## Purpose

W22 resumes the original workforce roadmap at Phase W7 after the W17–W21 product-experience and business-network slices.

The first slice operationalizes the existing `ai_seo_growth_employee` role through its already-governed semantic domain and Tool Registry bindings.

## Boundary

Research → Opportunity Analysis → Recommendation → Growth Report → Experiment Proposal → Approval → Audit/Provenance

## Implemented scope

- keyword research artifact
- content opportunity analysis
- on-page recommendations
- technical SEO checks
- internal-link recommendations
- content briefs
- search-performance ingestion artifact
- growth reporting artifact
- approval-gated SEO experiment proposal
- tenant-scoped storage provenance
- provider fail-closed semantics

## Safety boundary

SEO/search providers are not assumed to be available. The first slice records governed research/proposal artifacts and reports `provider_execution=not_configured` rather than fabricating external search execution or ranking impact.

`seo_experiment_proposal` is an external-impact proposal and remains approval-gated.

## Not claimed

- live search-engine API execution
- actual search ranking or traffic impact
- autonomous SEO experiment deployment
- production deployment
- customer acceptance/revenue
- Production Certification

## Definition of Done

Role/operation contract → registered Tool → tenant-safe handler → approval/policy enforcement → provenance → automated tests → real-stack PostgreSQL evidence → CI/security gates → documentation reconciliation.
