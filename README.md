# The Token Ledger

Daily digest of LLM API pricing and model changes across providers, built fully on a free stack.

- **Source:** OpenRouter `/models` endpoint (covers 50+ providers)
- **AI synthesis:** OpenRouter free tier (Gemini Flash)
- **Hosting:** GitHub Pages
- **Email:** Resend
- **Cross-post:** Dev.to
- **Schedule:** GitHub Actions cron daily 07:15 UTC

## Adding subscribers

Edit `subscribers.txt` (one email per line) on GitHub and commit. The next run picks them up.

## Required secrets

Set under Settings → Secrets and variables → Actions:

- `OPENROUTER_KEY`
- `RESEND_KEY`
- `DEVTO_KEY` (optional)

## Manual run

Actions tab → "Daily Digest" → Run workflow.
