# Quick Start: GitHub Pages Deployment

## What We've Set Up

✅ **Build Infrastructure**
- `scripts/build_static_site.py` - Generates all HTML pages & exports data
- `.github/workflows/build.yml` - Auto-builds on every push
- `web/static/js/search.js` - Client-side fuzzy search (Fuse.js)

✅ **GitHub Pages Config**
- `docs/.nojekyll` - Disables Jekyll (we use raw HTML)
- `CNAME` - Custom domain template (edit if needed)
- `.gitignore` updated to track `docs/`

✅ **Templates Updated**
- `base.html` now includes Fuse.js & search.js
- Ready for static site generation

---

## 5-Minute Setup

### 1. Create GitHub Repo (if you don't have one)

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/pari-pakuru.git
git branch -M main
```

### 2. Build the Site

```bash
python scripts/build_static_site.py
```

You should see:
```
📖 Exporting dictionary data...
✅ Exported 4343 entries
🔤 Generating entry pages...
✅ Generated 4343 entry pages
📚 Generating browse pages...
✅ Generated XX browse pages
📦 Copying static assets...
✅ Copied XX static files
📄 Generating static pages...
✅ Generated 3 static pages

✨ Build complete!
📂 Output: docs/
🌐 Ready for GitHub Pages!
```

### 3. Test Locally (Optional)

```bash
cd docs
python -m http.server 8000
# Visit http://localhost:8000/
```

### 4. Push to GitHub

```bash
git add .
git commit -m "feat: GitHub Pages static site

- Auto-generated from Flask templates
- Client-side search with Fuse.js
- Deploys on every push"
git push -u origin main
```

### 5. Enable GitHub Pages

1. Go to your repo on GitHub
2. **Settings** → **Pages**
3. Select:
   - Source: **GitHub Actions** (automatic)
   - OR: Deploy from branch → main → docs folder
4. Save

### 6. Watch the Deployment

- Go to **Actions** tab
- Watch "Build Static Site" run
- Once done, visit:
  ```
  https://YOUR_USERNAME.github.io/pari-pakuru/
  ```

**That''s it! 🎉 Your site is live!**

---

## After First Deployment

### When You Update the Database

```bash
python scripts/build_static_site.py
git add docs/
git commit -m "Update: Rebuild with latest data"
git push
```

Auto-deploys in seconds!

### When You Update Templates

Just push—the build workflow handles it:
```bash
git add web/templates/
git commit -m "Update: Improve design"
git push
```

---

## File Structure

```
pari-pakuru/
├── .github/workflows/
│   └── build.yml                    # CI/CD pipeline
├── docs/                            # GitHub Pages output (auto-generated)
│   ├── index.html
│   ├── data/
│   │   └── dictionary.json
│   ├── entries/
│   │   ├── p001.html
│   │   ├── p002.html
│   │   └── ...
│   ├── browse/
│   │   ├── nouns.html
│   │   ├── verbs.html
│   │   └── ...
│   └── static/
│       ├── css/
│       ├── js/
│       │   └── search.js            # NEW: Client-side search
│       └── ...
├── web/
│   ├── app.py                       # (No longer needed for GitHub Pages)
│   ├── static/
│   ├── templates/
│   │   └── base.html                # UPDATED: Now includes Fuse.js
│   └── ...
├── scripts/
│   └── build_static_site.py         # NEW: Build script
├── .gitignore                       # UPDATED: Track docs/
├── GITHUB_PAGES_GUIDE.md            # Full deployment guide
├── CNAME                            # Custom domain (optional)
└── ...
```

---

## How Search Works

1. **Build time**: `build_static_site.py` exports database to `docs/data/dictionary.json`
2. **First load**: Browser downloads JSON (~5-10MB)
3. **Search**: Fuse.js performs fuzzy search in client-side JS
   - No network requests needed
   - Instant results (< 100ms)
   - Works offline

---

## Troubleshooting

### Build fails locally?
```bash
python scripts/build_static_site.py --dry-run
```
Shows what would happen without writing files.

### GitHub Actions failing?
1. Check **Actions** tab for error logs
2. Common issues:
   - Missing `skiri_pawnee.db` (it''s ignored by git—expected)
   - Python version mismatch (workflow uses Python 3.10)

### Site not live?
1. Check **Settings** → **Pages** → Deploy from "GitHub Actions"
2. Check **Actions** tab—did the build succeed?
3. Check that `docs/` folder exists and has content

### Search returns no results?
Open DevTools (F12) → **Console**:
```javascript
// Should show:
// "Loaded 4343 dictionary entries"
```

If it says 0 entries, `dictionary.json` didn''t export correctly.

---

## Next Steps

1. ✅ Build the site: `python scripts/build_static_site.py`
2. ✅ Push to GitHub: `git push`
3. ✅ Enable Pages in Settings
4. ✅ Visit your live site!

For more details, see `GITHUB_PAGES_GUIDE.md`
