# Publish the BrandLens source repository

The current artifact is a local source package; it is not yet on a public Git host. Create a new repository through your own GitHub account or use a judge-accessible repository approved for the event, then run these commands from the extracted project folder.

```powershell
git init
git add .
git status
git commit -m "Add BrandLens Round 2 MVP"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/brandlens-round2.git
git push -u origin main
```

Replace `YOUR-USERNAME` and the repository path with the actual repository you created. The remote URL above is a placeholder, not a live link.

Before pushing:

- Check `git status` and ensure no database, `.env` file, API key, confidential draft or private evidence is staged.
- Confirm the event's official build window. Do not change timestamps or backdate commits to imply earlier work.
- Review and understand the code as a team; disclose AI assistance and reused packages/templates as required.
- Fill `CONTRIBUTIONS.md` with actual contributions and real commit/implementation evidence.
- Add the real repository URL to the submitted report after the push succeeds. Do not claim the repo is public until you have checked its visibility and opened it in a signed-out browser.
