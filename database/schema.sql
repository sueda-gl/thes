-- ============================================
-- AI Social Media Simulation Database Schema
-- ============================================

-- ============================================
-- AGENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    persona TEXT NOT NULL,           -- JSON: {age, gender, openness, etc.}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- POSTS TABLE (includes comments)
-- ============================================
CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    content TEXT NOT NULL,
    post_type TEXT NOT NULL,         -- 'campaign', 'organic', 'response', 'reshare'
    parent_post_id TEXT,              -- NULL = original post, else = comment/reshare
    created_step INTEGER NOT NULL,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    cascade_depth INTEGER DEFAULT 0,  -- 0=original, 1=1st reshare, 2=2nd reshare, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (parent_post_id) REFERENCES posts(post_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_agent ON posts(agent_id);
CREATE INDEX IF NOT EXISTS idx_posts_step ON posts(created_step);
CREATE INDEX IF NOT EXISTS idx_posts_parent ON posts(parent_post_id);
CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type);

-- ============================================
-- FOLLOWS TABLE (social graph)
-- ============================================
CREATE TABLE IF NOT EXISTS follows (
    follower_id TEXT NOT NULL,
    followee_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (follower_id, followee_id),
    FOREIGN KEY (follower_id) REFERENCES agents(agent_id),
    FOREIGN KEY (followee_id) REFERENCES agents(agent_id)
);

CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_follows_followee ON follows(followee_id);

-- ============================================
-- INTERACTIONS TABLE (likes only)
-- ============================================
CREATE TABLE IF NOT EXISTS interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    post_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL,  -- 'like'
    created_step INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    UNIQUE(agent_id, post_id)        -- Can't like same post twice
);

CREATE INDEX IF NOT EXISTS idx_interactions_agent ON interactions(agent_id);
CREATE INDEX IF NOT EXISTS idx_interactions_post ON interactions(post_id);
CREATE INDEX IF NOT EXISTS idx_interactions_step ON interactions(created_step);

-- ============================================
-- OBSERVATIONS TABLE (what agents saw)
-- ============================================
CREATE TABLE IF NOT EXISTS observations (
    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    post_id TEXT NOT NULL,
    seen_step INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

CREATE INDEX IF NOT EXISTS idx_observations_agent ON observations(agent_id);
CREATE INDEX IF NOT EXISTS idx_observations_step ON observations(seen_step);

-- ============================================
-- CAMPAIGNS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id TEXT PRIMARY KEY,
    campaign_type TEXT NOT NULL,     -- 'hope', 'fear'
    message TEXT NOT NULL,
    launch_step INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- CAMPAIGN EXPOSURES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS campaign_exposures (
    exposure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    campaign_id TEXT NOT NULL,
    post_id TEXT NOT NULL,           -- Which specific post was seen
    cascade_depth INTEGER NOT NULL,  -- 0=direct campaign, 1=1st reshare, etc.
    exposure_step INTEGER NOT NULL,
    responded BOOLEAN DEFAULT FALSE, -- Did they take any action?
    action_type TEXT,                -- 'like', 'comment', 'reshare', NULL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id),
    UNIQUE (agent_id, post_id)       -- Track unique exposures per post
);

CREATE INDEX IF NOT EXISTS idx_exposures_agent ON campaign_exposures(agent_id);
CREATE INDEX IF NOT EXISTS idx_exposures_campaign ON campaign_exposures(campaign_id);
CREATE INDEX IF NOT EXISTS idx_exposures_depth ON campaign_exposures(cascade_depth);

-- ============================================
-- SIMULATION METADATA TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS simulation_runs (
    run_id TEXT PRIMARY KEY,
    config TEXT NOT NULL,             -- JSON: all config parameters
    status TEXT NOT NULL,             -- 'running', 'completed', 'failed'
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_steps INTEGER,
    total_agents INTEGER,
    seed INTEGER
);

-- ============================================
-- BELIEF MEASUREMENTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS belief_measurements (
    agent_id TEXT NOT NULL,
    attribute TEXT NOT NULL,          -- 'environmental_concern', 'brand_trust', etc.
    value REAL NOT NULL,              -- [0, 1] normalized score
    step INTEGER NOT NULL,            -- When measured (T0=1439, T1=2880, T2=7200)
    reasoning TEXT,                   -- LLM's reasoning for the value
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (agent_id, attribute, step),
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

CREATE INDEX IF NOT EXISTS idx_beliefs_agent ON belief_measurements(agent_id);
CREATE INDEX IF NOT EXISTS idx_beliefs_step ON belief_measurements(step);
CREATE INDEX IF NOT EXISTS idx_beliefs_attribute ON belief_measurements(attribute);

