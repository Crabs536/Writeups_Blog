# Crabs536 Security Writeups

A Markdown-first security/CTF blog designed for GitHub Pages.

## Included

- Responsive dark/light theme
- Markdown writeups under `content/posts/`
- Automatic import of the three HackMD sources in `data/hackmd_sources.json`
- Search and tag filtering
- Code blocks, tables, task lists and images
- `/admin/` page to select a `.md` file, add metadata and download a publication-ready Markdown post
- Safe GitHub publishing flow: no Personal Access Token is stored in frontend JavaScript
- GitHub Actions deployment to Pages
- Daily scheduled rebuild so HackMD changes can be mirrored

## 1. Create the repository

Create a public repository named:

`Crabs536/security-writeups`

Then upload the contents of this folder to the repository root and commit to `main`.

## 2. Enable GitHub Pages

Repository → **Settings → Pages → Build and deployment → Source: GitHub Actions**.

The workflow `.github/workflows/pages.yml` will build and deploy the site.

Expected URL:

`https://crabs536.github.io/security-writeups/`

If you choose a different repository name, edit `site.json`:

```json
{
  "github_repo": "your-repo-name",
  "base_path": "/your-repo-name"
}
```

For a user site repository named `Crabs536.github.io`, use `"base_path": ""`.

## 3. HackMD import

The importer reads `data/hackmd_sources.json` and requests the raw Markdown form of each note by appending `.md` to the note URL. The imported content is generated during the GitHub Actions build and does not need to be committed.

If a note is private or cannot be fetched, the build remains online and shows a placeholder with the original source URL.

## 4. Add a Markdown post

### Browser workflow

Open `/admin/` on the deployed blog:

1. Select a `.md` file.
2. Set title, tags, date and slug.
3. Download the prepared `.md` file.
4. Click **Open GitHub upload**.
5. Upload the prepared file into `content/posts/` and commit.
6. GitHub Actions rebuilds the site automatically.

This deliberately avoids putting a GitHub token in a static web page.

### Direct GitHub workflow

Repository → `content/posts/` → **Add file → Upload files** → choose `.md` → Commit changes.

## 5. Local preview

```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/sync_hackmd.py # requires internet
python scripts/build.py
python -m http.server 8000 -d public
```

Open `http://localhost:8000/security-writeups/` only if testing with the same base path. For easier local preview, temporarily set `base_path` to an empty string in `site.json`.

## Content ownership

Only publish writeups and images you own or have permission to redistribute. The HackMD importer preserves the original source URL in post metadata.
