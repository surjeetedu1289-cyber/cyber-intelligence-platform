# Executive Cyber Intelligence Platform

## Overview

This platform has been extended from a dashboard into an Executive Decision Support System for:

- CISO
- CIO
- CTO
- Heads of Information Security
- Heads of IAM
- Security Architects
- Risk and Compliance leaders
- Financial Services executives

## Architecture

### Core modules

- `backend/intelligence/registry.py`: Configurable source registry loader and health metadata.
- `backend/intelligence/engine.py`: Enrichment, framework mapping, quality scoring, dashboards, widgets, daily brief, reports, and search.
- `backend/intelligence/pipeline.py`: Runtime ingestion pipeline using API-first collection, RSS fallback, HTML parsing fallback, deduplication, enrichment, persistence, and snapshot publishing.
- `backend/intelligence/persistence.py`: Upsert service for normalized intelligence records keyed by dedupe hash.
- `backend/intelligence/scheduler.py`: Scheduling metadata for collection and report cadence.
- `backend/intelligence/reliability.py`: Retry helper for resilient integrations.
- `config/source_registry.json`: Configurable enterprise source registry definition.

### Storage model

- `backend/models/intelligence_record.py`: PostgreSQL-compatible and SQLite-friendly normalized schema for enriched intelligence records.

## Source Registry

The source registry is configuration-driven (`config/source_registry.json`) and includes:

- Name
- Category
- RSS feed
- Official website
- API
- Refresh frequency
- Trust score
- Executive relevance score
- Geographic coverage
- Industry coverage
- Supported frameworks
- Collection method
- Last successful sync

## REST APIs

### Source and health

- `GET /v2/source-registry`

### Ingestion and persistence runtime

- `POST /v2/executive/pipeline/run`

### Dashboards and widgets

- `GET /v2/executive/dashboards`
- `GET /v2/executive/dashboards/{dashboard_id}`
- `GET /v2/executive/widgets/{dashboard_id}/{widget_id}`

### Daily briefing and reports

- `GET /v2/executive/daily-brief`
- `GET /v2/executive/reports/{report_type}` (`weekly|monthly|board|pdf|ppt|email|teams`)

### Search

- `GET /v2/executive/search`

Supported filters:

- framework
- control
- country
- industry
- threat_actor
- mitre_technique
- cve
- technology
- vendor
- regulator
- identity_topic
- cloud_topic
- ai_topic
- risk_level

### Scheduling metadata

- `GET /v2/executive/scheduler`

## Executive dashboards

Implemented dashboard families:

- Executive Summary
- Australian Regulatory Intelligence
- Global Cyber & Standards
- Identity & Access Management
- AI Security & Agentic AI
- Threat Intelligence
- Financial Services Risk & Compliance
- Research & Emerging Technology
- Executive Trends
- Critical Alerts

## Quality scoring

Each enriched article is scored on:

- Authority
- Timeliness
- Business impact
- Executive relevance
- Australian relevance
- Identity relevance
- AI relevance
- Financial services relevance
- Threat intelligence value
- Technical accuracy

## Testing

Added endpoint tests in:

- `tests/test_executive_intelligence_v2.py`
