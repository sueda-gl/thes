# Quick Start Guide - Fast Testing

## 🚀 Optimized for Fast Iteration

The default configuration is now optimized for **quick testing**:

### Default Settings (Fast Mode)
- **Agents:** 20 (instead of 100)
- **Steps:** 4 (instead of 10)
- **Campaign Launch:** Step 2 (instead of 3)
- **Concurrency:** 3 requests at a time
- **Max Tokens:** 200 per response

### Performance
- **Time:** ~2-3 minutes per run
- **Cost:** ~$0.10 per run
- **API Calls:** ~60-80 total

## 📊 Testing Progression

Follow this testing strategy:

### Phase 1: Minimal Test (Verify it works)
```
Agents: 10
Steps: 3
Campaign Launch: 2

Time: ~1 minute
Cost: ~$0.03
Purpose: Verify no errors
```

### Phase 2: Small Test (See patterns)
```
Agents: 20
Steps: 4
Campaign Launch: 2

Time: ~2-3 minutes
Cost: ~$0.10
Purpose: See if campaigns work
```

### Phase 3: Medium Test (First real data)
```
Agents: 50
Steps: 7
Campaign Launch: 3

Time: ~8 minutes
Cost: ~$0.40
Purpose: Get preliminary results
```

### Phase 4: Full Simulation (Thesis data)
```
Agents: 100
Steps: 10
Campaign Launch: 3

Time: ~15-20 minutes
Cost: ~$1.20
Purpose: Final results for thesis
```

## 🎯 What Each Configuration Tests

### Why Start Small?

**10 agents, 3 steps:**
- ✅ Verifies API key works
- ✅ Tests all code paths
- ✅ Very cheap (~$0.03)
- ✅ Fast feedback
- ❌ Not enough data for statistics
- ❌ Results not meaningful

**20 agents, 4 steps (Default):**
- ✅ Cheap (~$0.10)
- ✅ Fast (~2-3 min)
- ✅ Enough to see patterns
- ⚠️ Some statistical tests may fail (low N)
- ⚠️ Results directional, not conclusive

**50 agents, 7 steps:**
- ✅ Reasonable cost (~$0.40)
- ✅ Moderate time (~8 min)
- ✅ Better statistical power
- ✅ Can identify trends
- ⚠️ May need more for publication

**100 agents, 10 steps:**
- ✅ Full statistical power
- ✅ Publication-quality results
- ✅ Network effects visible
- ❌ More expensive (~$1.20)
- ❌ Takes longer (~20 min)

## 💡 Recommended Testing Flow

**Day 1: Debug and verify**
1. Run 10 agents, 3 steps (verify no errors)
2. Run 20 agents, 4 steps (see if campaigns work)
3. Fix any issues you find

**Day 2: Collect preliminary data**
1. Run 50 agents, 7 steps (3 different seeds)
2. Check if results make sense
3. Verify metrics look reasonable

**Day 3: Final data collection**
1. Run 100 agents, 10 steps (5 different seeds)
2. Collect comprehensive data
3. Export for thesis analysis

**Total cost:** ~$0.15 + ~$1.20 + ~$6.00 = **~$7-8 for complete thesis**

## 🐛 Current Bugs Fixed

All major bugs have been fixed:
- ✅ Campaign posts now appear in feeds
- ✅ Engagement tracking works properly
- ✅ Statistical tests handle edge cases
- ✅ Parser handles varied LLM responses
- ✅ Event loop issues resolved

## ⚡ Quick Commands

**Start Streamlit:**
```bash
cd /Users/suedagul/thes
source venv/bin/activate
streamlit run main.py
```

**Delete old database (fresh start):**
```bash
rm -f data/simulation.db
```

**Check current settings:**
```bash
cat config.py | grep "NUM_AGENTS\|SIMULATION_STEPS"
```

## 📈 Success Indicators

**Good test run:**
```
STEP 2/4
  🎯 CAMPAIGN INJECTION
  ✓ Hope campaign → 10 agents
  ✓ Fear campaign → 10 agents
  
  👀 OBSERVATION PHASE
  ✓ 45 total observations  ← Should be > 0
  
  🧠 DECISION PHASE
  Actions: {'like': 3, 'comment': 5, 'post': 2}  ← Mixed actions
  
✓ Simulation complete!
✓ Cost: $0.10
```

**Warning signs:**
```
⚠️  0 observations after campaign  ← Campaigns not in feeds
⚠️  Actions: {'none': 20}  ← No engagement at all
⚠️  Cost: $0.00  ← LLM not being called
```

## 🎓 For Your Thesis

**Testing phase (now):** Use 20 agents, 4 steps
**Data collection (later):** Use 100 agents, 10 steps

This gives you:
- Fast iteration during development
- Full data when you're ready
- Cost-effective approach
- Good scientific rigor

**You're all set for fast iteration testing! 🚀**

