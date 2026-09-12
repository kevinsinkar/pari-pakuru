# GitHub Pages Deployment Guide

This guide walks through deploying Pâri Pakûru' to GitHub Pages.

## Overview

Your site has been converted to a **fully static site** that runs entirely in the browser:
- ✅ No backend server needed
- ✅ Instant search with Fuse.js
- ✅ Free hosting on GitHub Pages
- ✅ Auto-deploys on every git push

## Prerequisites

1. **GitHub Account** - [Create one](https://github.com/signup) if you don't have one
2. **Git installed** - Already have it (you're using it!)
3. **Python 3.8+** - For building the site locally

## Step 1: Create a GitHub Repository

### If you don't have one yet:

```bash
cd your-pari-pakuru-repo
git init
git remote add origin https://github.com/YOUR_USERNAME/pari-pakuru.git
git branch -M main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### If you already have a repo:

Just make sure your remote is set:
```bash
git remote -v
```

Should show something like:
```
origin  https://github.com/YOUR_USERNAME/pari-pakuru.git (fetch)
origin  https://github.com/YOUR_USERNAME/pari-pakuru.git (push)
```

## Step 2: Update .gitignore

Make sure the `docs/` folder is NOT ignored (so it gets deployed). Check your `.gitignore`:

```bash
# Remove or comment out any line that ignores docs/
# Should NOT have:
# docs/

# DO keep these ignored:
.venv/
__pycache__/
*.pyc
skiri_pawnee.db
```

## Step 3: Build the Static Site Locally (Optional)

Test the build on your machine before pushing:

```bash
python scripts/build_static_site.py
```

This creates a `docs/` folder with all static files. You can view it locally:

```bash
cd docs
python -m http.server 8000
# Then visit http://localhost:8000/
```

## Step 4: Push to GitHub

```bash
git add .
git commit -m "feat: GitHub Pages static site build

- Static HTML generation from Flask templates
- Client-side search with Fuse.js
- Auto-deployment via GitHub Actions
- Fully works on GitHub Pages"
git push -u origin main
```

## Step 5: Enable GitHub Pages

1. Go to your GitHub repository
2. Settings → Pages
3. **Source**: "GitHub Actions" (it auto-detects the workflow)
   - OR manually: "Deploy from a branch" → `main` → `docs` folder
4. Save

## Step 6: Watch the Deployment

1. Go to your repo's **Actions** tab
2. You should see "Build Static Site" workflow running
3. Wait for it to complete (usually 1-2 minutes)
4. Once done, your site is live at:
   ```
   https://YOUR_USERNAME.github.io/pari-pakuru/
   ```

## Custom Domain (Optional)

If you have a custom domain:

1. Update the `CNAME` file in your repo:
   ```
   your-domain.com
   ```

2. Update DNS settings at your domain registrar to point to GitHub Pages
   (see [GitHub docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site))

## How It Works

### Build Process

1. **Every push to `main` triggers the workflow**
   - `.github/workflows/build.yml` runs
   - Python script exports dictionary data to JSON
   - Generates ~4300 static HTML entry pages
   - Copies CSS/JS assets
   - Outputs to `docs/` folder

2. **GitHub Actions deploys the `docs/` folder**
   - Automatically published to GitHub Pages
   - Live within seconds

### Client-Side Search

The site uses **Fuse.js** for fuzzy search, all in the browser:
- Loads `data/dictionary.json` once
- Searches 4300+ entries instantly
- Works offline after initial load
- No backend needed

## Rebuilding After Updates

### When you update the database:

```bash
python scripts/build_static_site.py
git add docs/
git commit -m "Update: Rebuild static site with latest data"
git push
```

Auto-deploys in seconds!

### When you update templates:

Just push and the build workflow handles it:
```bash
git add web/templates/
git commit -m "Update: Improve search template"
git push
```

## Troubleshooting

### Site not updating?
- Check the **Actions** tab for build errors
- Verify `docs/` folder exists and is tracked by git
- Check GitHub Pages settings (Settings → Pages)

### Search not working?
- Open browser DevTools (F12) → Console
- Check for errors loading `data/dictionary.json`
- Make sure `web/static/js/search.js` is present

### Links broken?
- Links use `/entries/P001.html` format (absolute paths)
- Make sure `docs/` is deployed at the repo root
- For subdirectory deployment, update all links to include base path

## Next Steps

1. **Push to GitHub** (you're ready!)
2. **Monitor the build** in Actions tab
3. **Share your site** - it's now live for the world!

## Performance Notes

- **First load**: ~5-10MB (downloads `dictionary.json`)
- **Subsequent loads**: Instant (cached in browser)
- **Search speed**: <100ms for all 4300 entries
- **Works offline**: Yes, after first load

## Limits & Trade-offs

✅ **What still works:**
- All dictionary searching and browsing
- Pronunciation audio/video (if included)
- Lesson content and static pages
- Flashcard sets (pre-generated)

⚠️ **What changed:**
- Community feedback is read-only (no new submissions)
- Admin queue is static snapshots
- Real-time stats won't update
- No user accounts/personalization

---

**Questions?** Check the [GitHub Pages documentation](https://docs.github.com/en/pages)
