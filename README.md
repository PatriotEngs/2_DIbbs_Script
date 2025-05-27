# DIBBS Scraper (Render Deployment)

This project scrapes FSC codes from the DLA DIBBS portal, filters them based on issue dates and quantity, saves the result to Excel, and uploads it to Google Drive.

## Configuration

Set these environment variables on Render or in your `.env` file for local runs:

- `ISSUED_FROM=YYYY-MM-DD`
- `ISSUED_TO=YYYY-MM-DD`
- `MIN_QTY=10`

## Setup

1. Upload your `service_account.json` from Google Cloud to Render.
2. Connect this repo to Render.com.
3. Enable the cron job as defined in `render.yaml`.

> Google Drive API must be enabled and the service account must have access to the target Drive folder.
