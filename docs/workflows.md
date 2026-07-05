# GitHub Actions workflows

## 1. Daily intelligence workflow

File: [.github/workflows/daily-update.yml](../.github/workflows/daily-update.yml)

This workflow runs every morning at 06:00 Australia/Sydney and can also be triggered manually. It:

- checks out the repository
- installs the Python and Node dependencies
- runs the collector and daily AI pipeline
- generates the daily JSON reports under data/daily
- commits the generated JSON artifacts back to the repository
- builds and deploys the dashboard artifact

## 2. Quality gate workflow

File: [.github/workflows/deploy.yml](../.github/workflows/deploy.yml)

This workflow runs on pushes to main and on manual dispatch. It:

- installs dependencies
- runs the backend unit tests
- runs linting with Ruff
- runs formatting checks with Black
- fails immediately on any issue
- deploys the frontend to GitHub Pages when the quality gates pass
