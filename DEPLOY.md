# DesignCalc — GitHub + Vercel deploy runbook

Follow these steps on your Mac (in Terminal). They take ~10 minutes and get DesignCalc
live on a public URL. You need: a GitHub account, a Vercel account (free tier is fine),
Node 18+ and Git installed.

---

## Step 0 — one-time cleanup

A partial `.git` folder was left by the build environment. Remove it so you start clean:

```bash
cd ~/Downloads/SoundDesign_TrainingDump/DesignCalc
rm -rf .git
```

## Step 1 — verify it builds locally (recommended)

```bash
npm install
npm run build
```

You want to see `✓ Compiled successfully`. (The frontend build doesn't run the Python
function — that runs on Vercel. To test the whole thing locally, see Step 6.)

## Step 2 — initialise git and make the first commit

```bash
git init
git add -A
git commit -m "DesignCalc MVP: Simple mode — venue in, plan + parts + .dbpr out"
```

`node_modules` and `.next` are already git-ignored, so they won't be committed.

## Step 3 — create the GitHub repo and push

**Option A — GitHub CLI (fastest, if you have `gh`):**

```bash
gh repo create designcalc --private --source=. --remote=origin --push
```

**Option B — manual:**
1. Go to github.com → **New repository** → name it `designcalc` → **Private** → *Create*
   (don't add a README/gitignore; the repo already has them).
2. Then:

```bash
git remote add origin https://github.com/<your-username>/designcalc.git
git branch -M main
git push -u origin main
```

## Step 4 — import into Vercel

1. Go to **vercel.com** → **Add New… → Project**.
2. **Import Git Repository** → pick `designcalc` (authorize GitHub if prompted).
3. Vercel auto-detects **Next.js** — leave the framework preset as is.
4. **Root Directory:** leave as `./` (the repo root).
5. Build & Output settings: defaults are correct (`next build`). No env vars needed.
6. Click **Deploy**.

Vercel builds the Next.js frontend **and** the Python function in `api/` automatically
(`@vercel/python`). First build takes ~1–2 min.

## Step 5 — verify the live deployment

1. Open the deployment URL Vercel gives you (e.g. `designcalc.vercel.app`).
2. Enter a venue (e.g. width **220**, depth **450**) → **Generate design**.
3. Confirm: the plan renders, cards + parts appear, **Download .dbpr** works.
4. Open the downloaded `.dbpr` in **ArrayCalc** → it must open with **no validation
   warning and no password prompt**. That's the acceptance test.

If the API call fails, open the Vercel deployment → **Functions** tab → check the
`api/generate` logs. The function returns a `trace` field on errors to help debug.

## Step 6 — (optional) run the full stack locally

The `npm run dev` server does **not** run the Python function. To test frontend + API
together locally, use the Vercel CLI:

```bash
npm i -g vercel
vercel dev
```

This serves the app and the Python function on `http://localhost:3000`.

---

## Notes

- **Custom domain:** in the Vercel project → **Settings → Domains**, add your domain and
  follow the DNS instructions. Not required for the MVP.
- **Private vs public repo:** either works with Vercel. Keep it private for now.
- **Redeploys:** every `git push` to `main` triggers an automatic Vercel deploy. Preview
  deployments are created for other branches / PRs — handy once your dev team joins.
- **Python runtime:** Vercel uses Python 3.12 by default; the function only uses the
  standard library, so there's nothing to pin. `api/requirements.txt` is intentionally empty.
- **The skeleton file** `api/_engine/NewProject_Skeleton.dbpr` is committed and required —
  it's the blank ArrayCalc project the engine clones. Don't remove it.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Vercel build fails on Python | Confirm `api/generate.py` is at the repo root under `api/`, and `vercel.json` is present. |
| `.dbpr` won't open / asks for password | The file was altered after generation. Ensure nothing post-processes it; the API must only read it. |
| API times out on huge venues | Raise `maxDuration`/`memory` in `vercel.json` (already 30 s / 1 GB). |
| Plan looks cramped on very deep fields | Known v1 polish item — label spacing on deep venues. Cosmetic only. |
