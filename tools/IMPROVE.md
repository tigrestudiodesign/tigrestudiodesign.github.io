# Daily improvement runbook (Tigre Studio portfolio)

The site is one file: `index.html` (all pages are JS templates routed by `#hash`). Images in `img/`, PDFs in `downloads/`.
Live: https://tigrestudiodesign.github.io/ · Mirror: claude.ai artifact `847d3d62-0b4d-4884-8882-b925a16c168e` (shared "public", title "Henry Ortega · Portfolio").

## House style (Henry's rules)
- Headers in ALL CAPS. Peter Tarka feel: technical but fun, hot orange accent (#FF5A1F), technical micro-type, grid backdrops, knurled hardware.
- Tigre brand: ink #0B0B0C, paper #F2EEE6, the T mark on a 24 x 28 grid, the mirrored spectrum stripe (amber at centre).
- Never publish Nike-proprietary specifics. Never render, animate or extend other companies' characters, logos, liveries or campaign art (Sanrio, F1 teams, sponsors, Uniqlo/Coca-Cola/Vans/Adidas posters). Improve those pages only through layout, copy, credits and Henry's own technique.
- Every image must come from geometry Henry or Claude actually built. No generated images.
- Henry signs in to sites himself; never enter passwords.

## One run = one finished improvement
1. Serve the repo and run `python3 tools/visible_projects.py` (Henry, Nov 17 2026: only improve what is actually on the site). Pick ONLY from that list: pages a visitor reaches from the homepage or the top menu. Never work on pages reachable only by direct link (the games, unlinked studies, old pages). From the list, prefer pages shown on the homepage (Selected Work first), then the rest; among those, take the one improved least recently in `data/improve-log.json`. Nike pages (p01–p11): layout, copy and Henry's own role only; nothing Nike-proprietary.
2. Make ONE meaningful improvement that a visitor would notice: better renders (Blender Cycles via `python3 -c "import bpy"`; Henry's Rhino files can be read with `rhino3dm` when staged from his Mac), a clearer layout, an interactive demo, tighter copy, fixing anything broken or empty, mobile polish.
3. Verify: run `python3 tools/site_audit.py` (whole site, ~8 min) and fix anything it reports: zero JS errors, failed requests, broken images, mobile overflow or dead links. Hash links must land on a project page or an existing section id; in-page anchors on project pages are handled by the click handler near `route()`. Then serve locally (`python3 -m http.server`), screenshot desktop 1440 and mobile 390 with Playwright (`/usr/bin/google-chrome`), check zero console errors and zero 404s, and look at the screenshots.
4. Deploy: commit (reuse the last commit's author: `E=$(git log -1 --format=%ae)` with GIT_AUTHOR_*/GIT_COMMITTER_* env), `git fetch && git rebase origin/main`, push. Then artifact: `python3 tools/build_artifact.py tools/artifact_files.json /abs/out/index.html` and publish_files index.html to the artifact (base_version from get_artifact, shared_live "public").
5. Append `{date, project, change, files}` to `data/improve-log.json` in the same commit.

- Artifact images: tools/build_artifact.py only embeds image paths it can find. If a page builds paths in code (like R('kh__x') or GBI('02')), add a lookup map for that prefix in build_artifact.py, or the images will be blank in the artifact.
