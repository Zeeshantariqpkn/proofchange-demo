# GitHub Setup

ProofChange is designed as a GitHub App. This document describes the
minimal setup required for live integration.

## 1. Create a GitHub App

- Permissions:
  - **Pull requests:** Read
  - **Checks:** Write
  - **Contents:** Read
- Subscribe to events:
  - `pull_request`
- Webhook URL: `https://<your-host>/webhooks/github`
- Webhook secret: generate a strong random value.

## 2. Install the App

Install the App on the target repository. Note the installation ID.

## 3. Configure environment

```env
GITHUB_APP_ID=...
GITHUB_PRIVATE_KEY_PATH=/path/to/private-key.pem
GITHUB_WEBHOOK_SECRET=...
GITHUB_INSTALLATION_ID=...