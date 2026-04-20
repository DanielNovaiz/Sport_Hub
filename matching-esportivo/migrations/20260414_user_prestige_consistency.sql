-- INTEGRITY MODULE 2: UserPrestige + guardrails de consistência XP

CREATE TABLE IF NOT EXISTS user_prestige (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    attribute_name VARCHAR(50) NOT NULL,
    prestige_level INTEGER NOT NULL DEFAULT 0 CHECK (prestige_level >= 0),
    residual_xp INTEGER NOT NULL DEFAULT 0 CHECK (residual_xp >= 0 AND residual_xp <= 59),
    total_prestige_xp INTEGER NOT NULL DEFAULT 0 CHECK (total_prestige_xp >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_prestige_user_attribute UNIQUE (user_id, attribute_name)
);

CREATE INDEX IF NOT EXISTS idx_user_prestige_user_id ON user_prestige(user_id);
CREATE INDEX IF NOT EXISTS idx_user_prestige_attribute_name ON user_prestige(attribute_name);
