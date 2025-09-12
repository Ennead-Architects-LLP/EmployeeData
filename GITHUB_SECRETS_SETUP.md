# GitHub Secrets Setup for Daily Scraper

This document explains how to set up GitHub secrets for the daily employee data scraper to run automatically via GitHub Actions.

## Required Secrets

The daily scraper requires two GitHub secrets to be configured:

1. **SCRAPER_EMAIL** - Your Ennead email address
2. **SCRAPER_PASSWORD** - Your Ennead password

## How to Set Up GitHub Secrets

### Step 1: Navigate to Repository Settings

1. Go to your GitHub repository
2. Click on the **Settings** tab (at the top of the repository)
3. In the left sidebar, click on **Secrets and variables** → **Actions**

### Step 2: Add New Secrets

1. Click **New repository secret**
2. For the first secret:
   - **Name**: `SCRAPER_EMAIL`
   - **Secret**: Your full Ennead email address (e.g., `your.name@ennead.com`)
3. Click **Add secret**
4. Click **New repository secret** again
5. For the second secret:
   - **Name**: `SCRAPER_PASSWORD`
   - **Secret**: Your Ennead password
6. Click **Add secret**

### Step 3: Verify Secrets

After adding both secrets, you should see them listed in the repository secrets section. The values will be hidden for security.

## Credential Priority System

The scraper uses a three-tier fallback system for credentials:

1. **GitHub Secrets** (highest priority) - Used in GitHub Actions
2. **Local credentials.json** - Used for local development
3. **GUI Setup** - Interactive setup if neither of the above are available

## Testing the Setup

### Manual Trigger

You can test the GitHub Actions workflow manually:

1. Go to the **Actions** tab in your repository
2. Select **Daily Employee Data Scraper** workflow
3. Click **Run workflow**
4. Click **Run workflow** button to start

### Local Testing

To test locally without GitHub secrets:

1. Run the scraper locally - it will use `credentials.json` if available
2. If no `credentials.json` exists, it will show a GUI for credential setup
3. The GUI will create a `credentials.json` file for future use

## Security Notes

- GitHub secrets are encrypted and only accessible to GitHub Actions
- Never commit `credentials.json` to the repository
- The `credentials.json` file is already in `.gitignore`
- GitHub secrets are not visible in logs or outputs

## Troubleshooting

### Common Issues

1. **"No credentials found" error**
   - Ensure both `SCRAPER_EMAIL` and `SCRAPER_PASSWORD` secrets are set
   - Check that secret names match exactly (case-sensitive)

2. **Login failed in GitHub Actions**
   - Verify email and password are correct
   - Check if your account requires 2FA (may need additional setup)

3. **Workflow not running**
   - Check the cron schedule in `.github/workflows/daily-scraper.yml`
   - Ensure the workflow file is in the correct location

### Logs

Check the GitHub Actions logs for detailed information:
1. Go to **Actions** tab
2. Click on the latest workflow run
3. Click on **scrape-employee-data** job
4. Review the logs for any errors

## Workflow Schedule

The daily scraper runs automatically at:
- **Time**: 6:00 AM UTC daily
- **Manual**: Can be triggered manually from the Actions tab

To change the schedule, edit the `cron` expression in `.github/workflows/daily-scraper.yml`.
