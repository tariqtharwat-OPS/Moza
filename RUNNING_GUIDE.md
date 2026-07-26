# MOZA Running Guide

> Quick-start guide to run the MOZA stack locally.
> For full context, see `PROJECT_STATE.md` and `EXECUTION_PLAN.md`.

---

## ⚠️ Prerequisite: NTFS Drive

**The project MUST be on an NTFS drive.** Node.js v24+ crashes with `EISDIR: illegal operation on a directory, readlink` on FAT32/exFAT drives.

Check your drive format:
```
wmic logicaldisk where "caption='X:'" get FileSystem
```
If it shows `FAT32` or `exFAT`, move the project to an NTFS drive (e.g., `C:\Moza`).

---

## 1. Start the Backend

```bash
cd backend
set PYTHONPATH=backend
python -m uvicorn moza.main:app --host 0.0.0.0 --port 8000
```

- First startup may take ~15s (Playwright/Litellm imports).
- Verify: open `http://localhost:8000/docs` — you should see the Swagger UI.

## 2. Start the Frontend

```bash
cd frontend
npm install --prefer-offline --no-audit --no-fund
npm run dev
```

- **First install:** `--prefer-offline --no-audit --no-fund` avoids npm audit/fund hangs.
- Verify: `http://localhost:3000` — you should see the MOZA UI with "Describe a task to execute."

## 3. Run Tests

```bash
# All unit + integration tests (81 total, no live deps)
cd backend
set PYTHONPATH=backend
python -m pytest tests/ -v

# Live benchmarks (requires GROQ_API_KEY + Playwright)
set GROQ_API_KEY=your_key_here
python tests/live/test_browser_live_benchmark.py
python tests/live/test_autonomous_research_benchmark.py
```

## 4. Verify the Frontend Build

```bash
cd frontend
npm run build
```

Expected output:
```
✓ Compiled successfully in ~19s
✓ Generating static pages (4/4)
Route (app)                                 Size  First Load JS
┌ ○ /                                     4.7 kB         108 kB
└ ○ /_not-found                            993 B         104 kB
```

## 5. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `EISDIR: illegal operation on a directory, readlink` | Project on FAT32/exFAT drive | Move to NTFS drive |
| `Cannot find module '@jridgewell/trace-mapping'` | Corrupted npm install | `npm install --prefer-offline --no-audit --no-fund` |
| Backend `ModuleNotFoundError` | `PYTHONPATH` not set | `set PYTHONPATH=backend` |
| Backend slow to start (15s+) | Cold imports (Playwright, litellm) | Normal. Subsequent restarts are faster with warm cache. |
| `self is not defined` in browser console | Expected with `TerminalComponent` — it uses `next/dynamic({ ssr: false })` | Ignore if it doesn't break the UI. |
| Frontend builds but `npm run dev` hangs after "Ready" | Port 3000 already in use | Kill old node processes: `taskkill /f /im node.exe` |
