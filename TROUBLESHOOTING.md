# Troubleshooting Guide

## Issue: Simulation Stuck After Batch 1

### Root Cause Analysis

**Problem:** The simulation would hang after processing Batch 1 of agents in the Decision Phase.

**Root Cause:** Event loop conflict (deadlock)

### Technical Explanation

The issue was caused by **nested event loops** creating a deadlock:

```
Streamlit Event Loop (running in background)
    └── asyncio.run(run_simulation())  ← Creates NEW event loop
            └── LLM async calls
                └── DEADLOCK! Cannot coordinate between loops
```

**Why this happened:**
1. Streamlit runs its own async event loop
2. `asyncio.run()` creates a **brand new** event loop
3. Python doesn't allow nested event loops by default
4. The inner loop (simulation) couldn't properly coordinate with the outer loop (Streamlit)
5. Result: Async calls hang indefinitely

### The Fix

**Applied 3 solutions:**

#### 1. nest-asyncio Package
Added `nest-asyncio` to allow nested event loops:
```python
import nest_asyncio
nest_asyncio.apply()  # Patches asyncio to allow nesting
```

#### 2. Reduced Concurrency
Changed `LLM_MAX_CONCURRENT` from 10 to 5:
- Reduces chance of rate limiting
- Gives OpenAI API more breathing room
- More stable for free-tier accounts

#### 3. Better Error Handling
Added:
- 30-second timeout per API request
- Clear error messages showing exactly what failed
- Exponential backoff with visible retry messages
- API key validation before running

### Error Messages You Might See Now

**Good (working):**
```
⚡ ACTION EXECUTION
  ✓ Executed: 13 likes, 2 comments, 5 posts
```

**If there's a problem, you'll see:**
```
⚠️  Request timeout (attempt 1/3)
   Waiting 2s before retry...
```

or

```
⚠️  API Error (attempt 1/3): Rate limit exceeded
   Waiting 2s before retry...
```

### Verification Steps

Before running simulation:

1. **Check API key is set:**
```bash
cat .env | grep OPENAI_API_KEY
```
Should show your actual key (sk-proj-xxx or sk-xxx), not the placeholder.

2. **Verify package installed:**
```bash
pip show nest-asyncio
```
Should show version 1.6.0 or higher.

3. **Check OpenAI credits:**
Visit https://platform.openai.com/usage
- Verify you have available credits
- Check you haven't hit rate limits

### Performance Expectations

**Normal behavior:**
- Step 1-2: 30-60 seconds (warm-up, fewer agents active)
- Step 3+: 1-3 minutes per step (more agents, campaign reactions)
- **Total time: 10-20 minutes for full simulation**

**Per step breakdown:**
- Observation Phase: Fast (< 1 second)
- Decision Phase: **Slowest** (1-3 minutes) - waiting for OpenAI
- Action Execution: Fast (< 1 second)

### If It Still Hangs

**Option 1: Reduce load**
In Streamlit sidebar:
- Agents: 50 instead of 100
- Steps: 5 instead of 10
- This cuts API calls by 75%!

**Option 2: Check rate limits**
- Free tier: 3 requests/minute
- Tier 1: 60 requests/minute
- Our code does 5 concurrent requests
- If you're on free tier, it will be VERY slow

**Option 3: Upgrade OpenAI account**
- Add credits to your account
- Upgrade to Tier 1 for higher rate limits

### Understanding the Shutdown Error

If you press Ctrl+C and see:
```
RuntimeError: Event loop is closed
```

This is **normal** and **harmless**. It's just Streamlit trying to clean up after the event loop is already closed. The fix with nest-asyncio prevents the deadlock that caused you to need Ctrl+C in the first place.

### Cost Reminder

- Each simulation: ~$0.40
- 50 agents, 5 steps: ~$0.05 (good for testing)
- 100 agents, 10 steps: ~$0.40 (full simulation)

### Success Indicators

**Simulation is working when you see:**
```
STEP 3/10
------------------------------------------------------------

  🎯 CAMPAIGN INJECTION
  ✓ Hope campaign → 50 agents
  ✓ Fear campaign → 50 agents

  👀 OBSERVATION PHASE
  ✓ 81 total observations

  🧠 DECISION PHASE
  - 55/100 agents active this step
  ✓ Batch 1: 10 agents decided   ← Progress!
  ✓ Batch 2: 10 agents decided   ← More progress!
  ✓ Batch 3: 10 agents decided
  ...
```

Each batch should complete within 20-40 seconds. If a single batch takes more than 2 minutes, there's likely an API issue.

## Quick Reference

**Start simulation:**
```bash
cd /Users/suedagul/thes
source venv/bin/activate
streamlit run main.py
```

**Check if it's working:**
- Look for batch completion messages
- Should see progress every 20-40 seconds
- No error messages

**If stuck:**
1. Wait 2 minutes first (might just be slow API)
2. Check terminal for error messages
3. Verify API key in .env
4. Check OpenAI credits
5. Try with fewer agents/steps

## Files Modified

To fix this issue, these files were updated:

1. `main.py` - Added nest-asyncio and better error handling
2. `llm/client.py` - Added timeout and retry messages
3. `config.py` - Reduced LLM_MAX_CONCURRENT to 5
4. `requirements.txt` - Added nest-asyncio package

All changes are backward compatible and improve stability.

