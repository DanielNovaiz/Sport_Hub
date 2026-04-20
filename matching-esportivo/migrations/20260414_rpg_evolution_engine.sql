-- Migração MODO B: RPG & Evolution Engine

ALTER TABLE player_stats
    ADD COLUMN IF NOT EXISTS shoot_long INTEGER NOT NULL DEFAULT 50 CHECK (shoot_long >= 0 AND shoot_long <= 99),
    ADD COLUMN IF NOT EXISTS shoot_mid INTEGER NOT NULL DEFAULT 50 CHECK (shoot_mid >= 0 AND shoot_mid <= 99),
    ADD COLUMN IF NOT EXISTS shoot_short INTEGER NOT NULL DEFAULT 50 CHECK (shoot_short >= 0 AND shoot_short <= 99),
    ADD COLUMN IF NOT EXISTS finishing INTEGER NOT NULL DEFAULT 50 CHECK (finishing >= 0 AND finishing <= 99),
    ADD COLUMN IF NOT EXISTS velocity INTEGER NOT NULL DEFAULT 50 CHECK (velocity >= 0 AND velocity <= 99),
    ADD COLUMN IF NOT EXISTS jump INTEGER NOT NULL DEFAULT 50 CHECK (jump >= 0 AND jump <= 99),
    ADD COLUMN IF NOT EXISTS agility INTEGER NOT NULL DEFAULT 50 CHECK (agility >= 0 AND agility <= 99),
    ADD COLUMN IF NOT EXISTS energy INTEGER NOT NULL DEFAULT 50 CHECK (energy >= 0 AND energy <= 99),
    ADD COLUMN IF NOT EXISTS strength INTEGER NOT NULL DEFAULT 50 CHECK (strength >= 0 AND strength <= 99),
    ADD COLUMN IF NOT EXISTS balance INTEGER NOT NULL DEFAULT 50 CHECK (balance >= 0 AND balance <= 99),
    ADD COLUMN IF NOT EXISTS ball_control INTEGER NOT NULL DEFAULT 50 CHECK (ball_control >= 0 AND ball_control <= 99),
    ADD COLUMN IF NOT EXISTS vision INTEGER NOT NULL DEFAULT 50 CHECK (vision >= 0 AND vision <= 99),
    ADD COLUMN IF NOT EXISTS dribble INTEGER NOT NULL DEFAULT 50 CHECK (dribble >= 0 AND dribble <= 99),
    ADD COLUMN IF NOT EXISTS steal INTEGER NOT NULL DEFAULT 50 CHECK (steal >= 0 AND steal <= 99),
    ADD COLUMN IF NOT EXISTS block INTEGER NOT NULL DEFAULT 50 CHECK (block >= 0 AND block <= 99),
    ADD COLUMN IF NOT EXISTS perim_def INTEGER NOT NULL DEFAULT 50 CHECK (perim_def >= 0 AND perim_def <= 99),
    ADD COLUMN IF NOT EXISTS post_def INTEGER NOT NULL DEFAULT 50 CHECK (post_def >= 0 AND post_def <= 99),
    ADD COLUMN IF NOT EXISTS rebound INTEGER NOT NULL DEFAULT 50 CHECK (rebound >= 0 AND rebound <= 99),
    ADD COLUMN IF NOT EXISTS reb_predict INTEGER NOT NULL DEFAULT 50 CHECK (reb_predict >= 0 AND reb_predict <= 99),
    ADD COLUMN IF NOT EXISTS combativeness INTEGER NOT NULL DEFAULT 50 CHECK (combativeness >= 0 AND combativeness <= 99);

ALTER TABLE match_performance
    ADD COLUMN IF NOT EXISTS field_goals_made INTEGER NOT NULL DEFAULT 0 CHECK (field_goals_made >= 0),
    ADD COLUMN IF NOT EXISTS field_goals_attempted INTEGER NOT NULL DEFAULT 0 CHECK (field_goals_attempted >= 0),
    ADD COLUMN IF NOT EXISTS steals INTEGER NOT NULL DEFAULT 0 CHECK (steals >= 0),
    ADD COLUMN IF NOT EXISTS blocks INTEGER NOT NULL DEFAULT 0 CHECK (blocks >= 0);

CREATE TABLE IF NOT EXISTS user_xp (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    attribute_name VARCHAR(50) NOT NULL,
    level INTEGER NOT NULL DEFAULT 0 CHECK (level >= 0),
    residual_xp INTEGER NOT NULL DEFAULT 0 CHECK (residual_xp >= 0 AND residual_xp <= 59),
    total_xp INTEGER NOT NULL DEFAULT 0 CHECK (total_xp >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_xp_user_attribute UNIQUE (user_id, attribute_name)
);

CREATE INDEX IF NOT EXISTS idx_user_xp_user_id ON user_xp(user_id);
CREATE INDEX IF NOT EXISTS idx_user_xp_attribute_name ON user_xp(attribute_name);

CREATE TABLE IF NOT EXISTS user_achievement (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    tier VARCHAR(20) NOT NULL DEFAULT 'Bronze',
    execution_count INTEGER NOT NULL DEFAULT 0 CHECK (execution_count >= 0),
    bonus_attribute VARCHAR(50),
    bonus_value INTEGER NOT NULL DEFAULT 0 CHECK (bonus_value >= 0 AND bonus_value <= 99),
    last_triggered_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_achievement_user_code UNIQUE (user_id, code)
);

CREATE INDEX IF NOT EXISTS idx_user_achievement_user_id ON user_achievement(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievement_code ON user_achievement(code);
