-- Season system: 3-month seasons, seasonal ranks, milestones and reward grants

CREATE TABLE IF NOT EXISTS season (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(16) NOT NULL UNIQUE,
    starts_at TIMESTAMP NOT NULL,
    ends_at TIMESTAMP NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_season_status ON season(status);
CREATE INDEX IF NOT EXISTS idx_season_starts_at ON season(starts_at);
CREATE INDEX IF NOT EXISTS idx_season_ends_at ON season(ends_at);

CREATE TABLE IF NOT EXISTS season_rank (
    id VARCHAR(36) PRIMARY KEY,
    season_id VARCHAR(36) NOT NULL REFERENCES season(id),
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id),
    xp_total INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 0,
    matches_played INTEGER NOT NULL DEFAULT 0,
    wins INTEGER NOT NULL DEFAULT 0,
    losses INTEGER NOT NULL DEFAULT 0,
    last_match_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_season_rank_season_user UNIQUE (season_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_season_rank_season_id ON season_rank(season_id);
CREATE INDEX IF NOT EXISTS idx_season_rank_user_id ON season_rank(user_id);
CREATE INDEX IF NOT EXISTS idx_season_rank_xp_total ON season_rank(xp_total DESC);

CREATE TABLE IF NOT EXISTS season_milestone (
    id VARCHAR(36) PRIMARY KEY,
    season_id VARCHAR(36) NOT NULL REFERENCES season(id),
    required_level INTEGER NOT NULL,
    reward_kind VARCHAR(32) NOT NULL,
    frame_code VARCHAR(80),
    xp_multiplier DOUBLE PRECISION NOT NULL DEFAULT 1,
    title VARCHAR(120) NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_season_milestone_season_level UNIQUE (season_id, required_level)
);

CREATE INDEX IF NOT EXISTS idx_season_milestone_season_id ON season_milestone(season_id);
CREATE INDEX IF NOT EXISTS idx_season_milestone_required_level ON season_milestone(required_level);

CREATE TABLE IF NOT EXISTS season_reward_grant (
    id VARCHAR(36) PRIMARY KEY,
    season_id VARCHAR(36) NOT NULL REFERENCES season(id),
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id),
    milestone_id VARCHAR(36) NOT NULL REFERENCES season_milestone(id),
    reward_kind VARCHAR(32) NOT NULL,
    frame_code VARCHAR(80),
    xp_multiplier DOUBLE PRECISION NOT NULL DEFAULT 1,
    activation_at TIMESTAMP,
    expires_at TIMESTAMP,
    claimed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_season_reward_grant UNIQUE (season_id, user_id, milestone_id)
);

CREATE INDEX IF NOT EXISTS idx_season_reward_grant_season_id ON season_reward_grant(season_id);
CREATE INDEX IF NOT EXISTS idx_season_reward_grant_user_id ON season_reward_grant(user_id);
CREATE INDEX IF NOT EXISTS idx_season_reward_grant_milestone_id ON season_reward_grant(milestone_id);
CREATE INDEX IF NOT EXISTS idx_season_reward_grant_reward_kind ON season_reward_grant(reward_kind);
