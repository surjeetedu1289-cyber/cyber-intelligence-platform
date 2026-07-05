# GitHub Pages Deployment Guide

This project is deployed as a static React site on GitHub Pages.

## Deployment URL

https://surjeetedu1289-cyber.github.io/cyber-intelligence-platform/

## Required Repository Settings

1. Open repository settings.
2. Go to Pages.
3. Set Source to GitHub Actions.
4. Save the configuration.

## Required Secrets

1. Add repository secret `ANTHROPIC_API_KEY`.
2. Ensure the key can be used by GitHub Actions.

## Workflows

1. `Daily Intelligence Update` in [.github/workflows/daily-update.yml](../.github/workflows/daily-update.yml)
2. `Build Validation` in [.github/workflows/deploy.yml](../.github/workflows/deploy.yml)

## Daily Intelligence Update Behavior

1. Runs every day at 06:00 Australia/Sydney.
2. Runs ingestion and AI enrichment.
3. Exports static JSON files into `frontend/public/data/`.
4. Commits refreshed JSON to the repository.
5. Builds and deploys `frontend/dist` to GitHub Pages.

Generated static JSON files:

1. `frontend/public/data/dashboard.json`
2. `frontend/public/data/news.json`
3. `frontend/public/data/trends.json`
4. `frontend/public/data/executive-summary.json`
5. `frontend/public/data/regulations.json`
6. `frontend/public/data/threats.json`
7. `frontend/public/data/research.json`

## Build Validation Behavior

1. Runs on every pull request targeting `main`.
2. Runs Python lint and format checks.
3. Runs unit tests.
4. Runs TypeScript checks.
5. Builds the React dashboard.

## Manual Trigger

1. Open Actions tab.
2. Select `Daily Intelligence Update`.
3. Click Run workflow.
4. Select `main` and run.

## Verification Checklist

1. Open deployed URL and confirm dashboard renders.
2. Confirm browser network requests load `/cyber-intelligence-platform/data/*.json`.
3. Confirm no runtime calls to backend API routes.
4. Confirm latest `generatedAt` values in JSON files after daily run.
