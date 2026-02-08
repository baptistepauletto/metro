# GitHub Pages Setup Guide

This guide explains how to set up GitHub Pages to host the data.json file that your Matrix Portal will fetch every 5 minutes.

## Overview

The GitHub Actions workflow automatically:
1. Runs every 5 minutes
2. Fetches stock prices from Yahoo Finance
3. Calculates next metro departure from your schedule
4. Generates a `data.json` file
5. Commits it to the `gh-pages` branch

GitHub Pages then serves this file at: `https://[your-username].github.io/metro/data.json`

## Setup Steps

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** (top right)
3. Scroll down to **Pages** (left sidebar)
4. Under **Source**, select:
   - Branch: `gh-pages`
   - Folder: `/ (root)`
5. Click **Save**

### 2. Create the gh-pages Branch

The GitHub Actions workflow will create this automatically on its first run, but you can create it manually:

```bash
# Create and checkout gh-pages branch
git checkout --orphan gh-pages

# Add a placeholder file
echo '{"status": "pending"}' > data.json
git add data.json
git commit -m "Initialize gh-pages branch"

# Push to GitHub
git push origin gh-pages

# Switch back to main branch
git checkout master  # or 'main'
```

### 3. Update Config with Your GitHub Username

Edit `config.json` and replace `baptistebisson` with your GitHub username:

```json
{
  "github_pages_url": "https://YOUR_USERNAME.github.io/metro/data.json",
  ...
}
```

### 4. Test the Workflow

Push your changes to trigger the workflow:

```bash
git add .
git commit -m "Add scrolling display with GitHub Actions"
git push origin master
```

Go to the **Actions** tab on GitHub to watch the workflow run.

### 5. Verify GitHub Pages is Working

After the workflow completes successfully:

1. Wait 1-2 minutes for GitHub Pages to deploy
2. Visit: `https://YOUR_USERNAME.github.io/metro/data.json`
3. You should see JSON with metro, stock, and time data

Example output:
```json
{
  "updated": "2026-02-08T20:30:00Z",
  "metro": {
    "station": "Rosemont",
    "next_departure": "20:40",
    "minutes_until": 10,
    "line_color": "#D95700"
  },
  "stock": {
    "symbol": "XEQT",
    "price": 37.83,
    "change_percent": 1.2,
    "market_open": false
  },
  "time": {
    "display": "15:30",
    "timezone": "America/Montreal",
    "date": "FEB 8"
  }
}
```

## Troubleshooting

### Workflow Not Running

**Issue**: No workflows appear in the Actions tab

**Solution**:
- Make sure `.github/workflows/update-display-data.yml` is committed
- Check that GitHub Actions is enabled in Settings → Actions
- Wait a few minutes after pushing

### 404 Error on data.json URL

**Issue**: `https://username.github.io/metro/data.json` returns 404

**Solutions**:
1. **Check GitHub Pages is enabled** (Settings → Pages)
2. **Verify gh-pages branch exists**:
   ```bash
   git fetch origin gh-pages
   git branch -a
   ```
3. **Check workflow logs** for errors in the Actions tab
4. **Wait a few minutes** - GitHub Pages can take time to deploy

### Workflow Failing

**Issue**: Workflow fails with errors

**Check**:
1. **Python script errors**: View logs in Actions tab
2. **Schedule file exists**: Make sure `schedule.json` is in the repo root
3. **Dependencies installed**: Workflow should install `requests` and `pytz`

### CORS Errors on Matrix Portal

**Issue**: Matrix Portal can't fetch data due to CORS

**Solution**: GitHub Pages automatically serves with proper CORS headers. This shouldn't be an issue, but if it is:
- Verify you're using the correct URL (https, not http)
- Check that GitHub Pages is serving the file (visit in browser first)

## Testing Locally

Before deploying to the Matrix Portal, test the Python script locally:

```bash
# Install dependencies
pip install requests pytz

# Run the script
python .github/scripts/update_data.py

# Check the generated file
cat data.json
```

You should see the JSON output with your current metro/stock/time data.

## Customization

### Change Update Frequency

Edit `.github/workflows/update-display-data.yml`:

```yaml
on:
  schedule:
    - cron: '*/5 * * * *'  # Change to '*/10 * * * *' for every 10 minutes
```

**Note**: Minimum interval is 5 minutes. Less frequent updates save GitHub Actions minutes.

### Change Stock Symbol

Edit `config.json`:

```json
{
  "stock_symbol": "AAPL",  # Change to any valid Yahoo Finance symbol
  ...
}
```

Then commit and push. The next workflow run will use the new symbol.

### Change Metro Station

1. Edit `config.json` with your new station details
2. Regenerate schedule: `python build_schedule.py`
3. Commit both `config.json` and `schedule.json`
4. Push to GitHub

## GitHub Actions Limits

GitHub provides generous free tier limits:

- **Public repos**: Unlimited Actions minutes
- **Private repos**: 2,000 minutes/month

At 5-minute intervals, the workflow runs ~8,640 times/month, using approximately:
- **Public repo**: No cost
- **Private repo**: ~300-500 minutes/month (well within free tier)

Each run takes ~30-45 seconds.

## Security Notes

- The workflow uses `GITHUB_TOKEN` which is automatically provided
- No secrets or API keys needed (Yahoo Finance is free)
- Your WiFi credentials stay in `secrets.py` on your local device only

## Next Steps

Once GitHub Pages is working:

1. Copy the new `code.py` to your Matrix Portal
2. Update `secrets.py` if needed
3. The display should automatically fetch data from GitHub Pages
4. Monitor the serial console for any errors

**The display will update every 5 minutes with fresh data automatically!**
