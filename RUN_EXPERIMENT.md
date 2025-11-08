# Running the Thesis Experiment

## ✅ Pre-Flight Checklist Complete

- ✅ 200 personas generated
- ✅ Activity floor implemented (0.3-1.0)
- ✅ Median collapse fix implemented (hybrid THOUGHTS+RATING)
- ✅ Documentation fixed (engine.py, config.py)
- ✅ Experiment design validated

---

## 🚀 Command to Run Experiment

### Step 1: Activate Virtual Environment
```bash
cd /Users/suedagul/thes
source venv/bin/activate
```

### Step 2: Run Thesis Experiment
```bash
python run_thesis_experiment.py
```

---

## ⏱️ What to Expect

### Runtime
- **Expected:** 45-60 minutes
- **Progress updates:** Every 100 steps
- **Total steps:** 2000 (~33 simulated hours)

### Cost
- **Expected:** $20-25
- **LLM calls:** ~18,500 total
  - Decisions: ~18,000 calls
  - Belief measurements: ~440 calls (200 at T0, 120 at T1, 120 at T2)

### Progress Output
You'll see:
```
STEP 1/2000
------------------------------------------------------------
👀 OBSERVATION PHASE
✓ 45/200 agents online
✓ 12 total observations

🧠 DECISION PHASE
- 45/200 agents online and deciding
✓ Batch 1: 45 agents decided
Actions: {'none': 38, 'like': 4, 'post': 2, 'reshare': 1}

⚡ ACTION EXECUTION
✓ Executed: 4 likes, 0 comments, 2 posts, 1 reshares
```

### Key Checkpoints
- **Step 399:** T0 baseline measurement (all 200 agents)
- **Step 400:** Campaign injection (60 Hope, 60 Fear)
- **Step 800:** T1 immediate effect (120 targeted agents)
- **Step 2000:** T2 sustained effect (120 targeted agents)

---

## 🛑 If Something Goes Wrong

### Rate Limit Error (429)
```
Error: Rate limit exceeded
```
**Solution:** The code has retry logic, but if persistent:
1. Stop the run (Ctrl+C)
2. Reduce concurrency in `run_thesis_experiment.py`:
   ```python
   config.LLM_MAX_CONCURRENT = 20  # Reduce from 50
   ```
3. Restart

### API Error (404 - Deployment Not Found)
```
Error: DeploymentNotFound
```
**Solution:** Check your Azure deployment name
1. Open `config.py` or `run_thesis_experiment.py`
2. Update `LLM_MODEL` to match your Azure deployment:
   ```python
   config.LLM_MODEL = "your-actual-deployment-name"
   ```

### Out of Memory
```
MemoryError
```
**Solution:** Unlikely with 200 agents, but if it happens:
1. Close other applications
2. Or reduce to 100 agents temporarily

---

## 📊 After Completion

The script will automatically:
1. ✅ Save database to `data/thesis_experiment_YYYYMMDD_HHMMSS.db`
2. ✅ Generate analysis report (if `analysis/belief_analysis.py` works)
3. ✅ Print LLM usage statistics and cost

### Next Steps
1. **Validate results:**
   ```python
   # Check T0 correlation with persona
   python -c "from analysis.belief_analysis import validate_t0_correlation; validate_t0_correlation('data/thesis_experiment_*.db')"
   ```

2. **Extract data for statistical analysis:**
   ```python
   # Export belief measurements to CSV
   python -c "
   import sqlite3
   import pandas as pd
   conn = sqlite3.connect('data/thesis_experiment_*.db')  # Use actual filename
   df = pd.read_sql('SELECT * FROM belief_measurements', conn)
   df.to_csv('belief_data.csv', index=False)
   print(f'Exported {len(df)} measurements')
   "
   ```

3. **Run statistical tests (R or Python):**
   - Repeated measures ANOVA
   - Hope vs Fear comparisons
   - Cascade depth analysis

---

## 📝 What Gets Generated

### Database File
- **Location:** `data/thesis_experiment_YYYYMMDD_HHMMSS.db`
- **Size:** ~50-100 MB
- **Contains:**
  - All agent personas
  - All posts (organic + campaign)
  - All interactions (likes, comments, reshares)
  - All belief measurements (with THOUGHTS text)
  - All campaign exposures (with cascade depth)
  - Network structure (follows)

### Analysis Report (if generated)
- **Location:** `data/results/belief_analysis_YYYYMMDD_HHMMSS.md`
- **Contains:**
  - Belief trajectories over time
  - Hope vs Fear comparisons
  - Cascade depth effects
  - Summary statistics

---

## 🔍 Monitor During Run

### What to Watch
1. **Agents going online:** Should see ~25-35% online at any time
2. **Organic posts:** Should accumulate gradually (few per step)
3. **Campaign responses:** After step 400, should see likes/reshares
4. **Belief measurements:** 
   - T0 (step 399): ~2-3 minutes for 200 agents
   - T1/T2 (steps 800, 2000): ~1-2 minutes for 120 agents

### Good Signs
- ✅ LLM responses completing successfully
- ✅ Actions being executed (not all "none")
- ✅ Cascades forming (reshares happening)
- ✅ Online agent count fluctuating realistically

### Red Flags
- 🔴 All agents always offline (bug in Activity)
- 🔴 No actions ever (LLM not responding)
- 🔴 Rate limit errors every request (concurrency too high)
- 🔴 Belief measurements all 0.5 (median collapse not fixed)

---

## 💾 Backup Your Data

After completion:
```bash
# Copy database to safe location
cp data/thesis_experiment_*.db ~/Desktop/thesis_backup.db

# Or compress it
tar -czf thesis_experiment_backup.tar.gz data/thesis_experiment_*.db
```

---

## 🎯 Expected Results

### If Everything Works
- ✅ T0 beliefs correlate with persona (r > 0.7)
- ✅ Variance not compressed (σ ≈ 0.08)
- ✅ Some belief changes detected (if framing matters)
- ✅ Rich qualitative THOUGHTS data

### If Hope/Fear Framing Matters
- Hope group: ΔT1-T0 ≈ +0.2 to +0.4
- Fear group: ΔT1-T0 ≈ 0 to +0.3
- Difference: p < 0.05

### If Null Result
- Still valuable! You can:
  - Show methodology works (T0 validates)
  - Quote rich qualitative data
  - Explore personality moderations
  - Frame as exploratory pilot study

---

## ⏸️ Pausing/Resuming

**Note:** The current implementation does NOT support pause/resume.
If you need to stop:
- Ctrl+C will save partial data to database
- You'll need to start fresh (don't resume from partial run)

For long runs, consider:
- Running in `tmux` or `screen` session
- Using `nohup` to survive SSH disconnects
- Running overnight

---

## 🆘 Emergency Contact

If critical issues arise:
1. Check `CRITICAL_REVIEW.md` for troubleshooting
2. Check database: `sqlite3 data/thesis_experiment_*.db "SELECT COUNT(*) FROM agents"`
3. Check LLM client logs (if verbose mode enabled)

---

**Good luck! 🚀**

Expected completion: ~1 hour from now
Expected result: Novel LLM-agent social media simulation data for bachelor's thesis

