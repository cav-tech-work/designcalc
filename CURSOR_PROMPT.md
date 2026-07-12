# Cursor prompt — take DesignCalc from repo to live Vercel deployment

Copy everything in the code block below into Cursor's Agent (Composer in agent mode),
with the `DesignCalc` folder open as your workspace. Let it run; approve terminal
commands when it asks. It will stop and ask you only when it needs an interactive login
(GitHub / Vercel) or a decision.

---

```
You are working in the DesignCalc repository (root of the currently open folder). It is a
Next.js 14 (App Router, TypeScript) frontend plus a Python serverless function in `api/`
that wraps a sound-system design engine and returns a valid ArrayCalc `.dbpr` file. It is
meant to deploy to Vercel as a single project (Next.js frontend + Python API together).

Read README.md, ARCHITECTURE.md, HANDOFF.md, and DEPLOY.md first for full context, then do
everything below. Work autonomously; only pause when you need me to complete an interactive
login or make a decision. Report what you did after each numbered step.

GOAL: get DesignCalc committed to a new GitHub repo and deployed live on Vercel, verified
working end to end.

Do these in order:

1. CLEAN UP
   - If a `.git` directory already exists, remove it (`rm -rf .git`) — it may be a corrupt
     partial repo from another environment. We want a fresh history.
   - Confirm `.gitignore` excludes `node_modules/`, `.next/`, `.vercel`, and `*.dbpr`
     EXCEPT `api/_engine/NewProject_Skeleton.dbpr` (that file MUST be committed — it is the
     blank ArrayCalc project the engine clones; the app breaks without it).

2. BUILD CHECK
   - Run `npm install`.
   - Run `npm run build`. It must end with a successful compile and type-check. If it
     fails, fix the errors (they will be TypeScript or Next config issues), then rebuild
     until green. Do not change engine behavior in `api/_engine/` to make the build pass.

3. GIT
   - `git init`, then stage everything and make one clean initial commit:
     "DesignCalc MVP: Simple mode — venue in, plan + parts + .dbpr out".
   - Verify `node_modules/` and `.next/` are NOT tracked.

4. GITHUB
   - Create a new PRIVATE GitHub repo named `designcalc` and push `main` to it.
   - Prefer the GitHub CLI: `gh repo create designcalc --private --source=. --remote=origin --push`.
   - If `gh` is not installed or not authenticated, tell me exactly what to do (install/auth),
     wait for me, then continue. Do not hardcode any token into files.

5. VERCEL
   - Deploy this repo to Vercel as a new project using the Vercel CLI (`npm i -g vercel`
     then `vercel` / `vercel --prod`). Framework preset: Next.js. Root directory: repo root.
     No environment variables are required.
   - Vercel must build BOTH the Next.js frontend and the Python function under `api/`
     (via @vercel/python). `vercel.json` is already configured (1024 MB, 30 s for
     `api/generate.py`). If Vercel asks to link/scope the project or log in, pause and let
     me complete it, then continue.
   - Produce a PRODUCTION deployment and report the live URL.

6. VERIFY THE LIVE DEPLOYMENT
   - Hit the deployed site's `POST /api/generate` with a test payload and confirm a 200
     with a JSON body containing `design`, `meta`, and a non-empty `dbpr_base64`. Example:
       curl -s -X POST "<LIVE_URL>/api/generate" \
         -H "Content-Type: application/json" \
         -d '{"width_ft":220,"depth_ft":450,"units":"ft"}' | head -c 400
   - Confirm the response’s `meta.integrity` is "ok".
   - Load the site root in a browser preview if available and confirm the form renders and
     "Generate design" returns a plan, subsystem cards, and a parts list.
   - Report the live URL, the GitHub repo URL, and a one-line status for each step.

HARD CONSTRAINTS (do not violate):
- Never modify, re-save, or post-process the generated `.dbpr` after the Python engine
  writes it. The API must only READ it. Altering it breaks the ArrayCalc integrity hash and
  causes a password prompt when opened.
- Do not delete or regenerate `api/_engine/NewProject_Skeleton.dbpr`.
- Do not change the design engine logic in `api/_engine/` (flatground_core.py, extensions.py,
  writer.py, engine.py, summary.py). You may only fix frontend/build/config issues.
- Keep the app stateless — no database, no auth, no stored files.
- Keep the API contract in `lib/types.ts` and `api/generate.py` in sync if you touch either.

If anything blocks you (auth, a build error you can't resolve, a Vercel setting), stop and
tell me precisely what you need. Otherwise, run to completion and give me the live URL.
```

---

## Notes for you (Joyjeet)

- Cursor's agent can run terminal commands, so it can do the git + `gh` + `vercel` steps
  itself. It will pause for the interactive **GitHub auth** and **Vercel login/link** the
  first time — that's expected; just complete those prompts and it continues.
- If you'd rather deploy through Vercel's GitHub integration (dashboard) instead of the
  Vercel CLI, tell Cursor "use the GitHub → Vercel dashboard flow instead of the CLI" and
  it will stop after the push and hand you the import step.
- The one genuinely new-at-runtime piece is the Python function on Vercel. If step 6 shows
  an API error, paste the Vercel **Functions** log back to me (here) and I'll fix it — the
  engine itself is tested, so it'll be a wiring/config detail.
