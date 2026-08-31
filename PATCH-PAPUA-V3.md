# Papua V3 — OG Image / Video Page Patch

Files in this patch:
- `generate.py`
- `videos.json`
- `templates/index.template.html`
- `templates/video.template.html`

What this fixes:
1. All existing `videos.json` entries now have local OG URLs under `https://viral18plus.github.io/papua/covers/` using the existing cover filenames/extensions.
2. The generator validates OG URLs before publishing and fails the build if an entry is empty or points outside the Papua GitHub Pages covers path.
3. Homepage OG/Twitter image now uses the generator's `__OG_IMAGE__` value instead of hardcoded `cover.jpg`.
4. Video page `makeVideoFrame()` now receives the complete video object, so the cover thumbnail and Google Drive player both work without the undefined-variable error.
5. Existing Adsterra scripts/configuration are intentionally unchanged.
6. Cloudflare Worker, GitHub App, secrets, Drive IDs, and cover files are not changed by this patch.

Deployment:
- Upload/replace these files in the root of `viral18plus/papua`.
- Do NOT delete or replace the existing `covers/` folder.
- GitHub Actions will regenerate `index.html` and all video pages automatically.
