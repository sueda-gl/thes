# Secondary/Tertiary Exposure Tracking Fix

## 🐛 The Problem

**Symptom:** Secondary and tertiary engagement appeared the same as first-hand engagement in metrics.

**Root Cause:** The original code incorrectly assumed that **ANY post** from someone exposed to a campaign was spreading that campaign. This led to massive over-counting of secondary exposures.

### Example of the Bug:
1. Agent A sees Hope campaign
2. Agent A posts about their breakfast
3. Agent B sees Agent A's breakfast post  
4. System incorrectly counts Agent B as having secondary exposure to Hope campaign

## 🔍 Original Flawed Logic

```python
# WRONG: Counted ALL posts from campaign-exposed agents
for item in feed:
    post_author = item.get('agent_id')
    
    # Check if post is FROM someone exposed to a campaign
    if post_author in self.campaign_assignments:
        campaign_type = self.campaign_assignments[post_author]
        campaigns_seen_in_feed.add(campaign_type)
```

This meant if 50 agents were exposed to Hope campaign and each posted 5 times about random topics, all their followers would be counted as having secondary exposure to Hope.

## ✅ The Fix

Changed the logic to **only track exposure from actual campaign posts**:

```python
# CORRECT: Only count actual campaign posts
for item in feed:
    post_id = item.get('post_id', '')
    post_type = item.get('post_type', '')
    
    # Only count actual campaign posts
    if post_type == 'campaign':
        # Extract campaign type from post_id
        if 'hope' in post_id:
            campaigns_seen_in_feed.add('hope')
        elif 'fear' in post_id:
            campaigns_seen_in_feed.add('fear')
```

## 📊 Impact

**Before Fix:**
- Any post from campaign-exposed agents counted as spreading the campaign
- Secondary/tertiary numbers artificially inflated
- Made it impossible to measure true viral spread

**After Fix:**
- Only actual campaign posts trigger secondary exposure
- More accurate measurement of campaign reach
- Secondary exposure should now be lower than direct exposure (as expected)

## ⚠️ Current Limitations

The fix has one limitation: it doesn't track secondary exposure from **organic posts about campaigns**. When Agent A creates an organic post discussing the campaign, Agent B won't get secondary exposure from seeing it.

This is a trade-off between:
- **False positives** (counting all posts as campaign-related) - AVOIDED ✅
- **False negatives** (missing some campaign-related organic posts) - ACCEPTED

Without content analysis or explicit tagging of campaign-related posts, this is the most accurate approach.

## 💡 Future Improvements

To fully solve this, the system would need one of:
1. **Content tagging**: Mark posts as campaign-related when created
2. **Content analysis**: Analyze post text for campaign themes
3. **Response tracking**: Link organic posts to their campaign inspiration

For now, tracking only explicit campaign posts provides the most reliable metrics.
