# DIBBS Scraper (Render Deployment)

This project scrapes FSC codes from the DLA DIBBS portal, filters them based on issue dates and quantity, saves the result to Excel, and uploads it to Google Drive.

## Behavior

- `issued_from` = yesterday
- `issued_to` = end of next month
- `min_qty` = 5

## Setup

1. Upload your `service_account.json` from Google Cloud to Render.
2. Connect this repo to Render.com.
3. Enable the cron job as defined in `render.yaml`.

> Google Drive API must be enabled and the service account must have access to the target Drive folder.
