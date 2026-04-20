-- Migração MODO B: gamificação (PlayerStats + MatchPerformance)

CREATE TABLE IF NOT EXISTS player_stats (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    position VARCHAR(20) NOT NULL DEFAULT 'meia',
    overall INTEGER NOT NULL DEFAULT 50 CHECK (overall >= 0 AND overall <= 100),
    playstyle_archetype VARCHAR(50) NOT NULL DEFAULT 'Balanced',
    pace INTEGER NOT NULL DEFAULT 50 CHECK (pace >= 0 AND pace <= 100),
    shooting INTEGER NOT NULL DEFAULT 50 CHECK (shooting >= 0 AND shooting <= 100),
    passing INTEGER NOT NULL DEFAULT 50 CHECK (passing >= 0 AND passing <= 100),
    defense INTEGER NOT NULL DEFAULT 50 CHECK (defense >= 0 AND defense <= 100),
    physical INTEGER NOT NULL DEFAULT 50 CHECK (physical >= 0 AND physical <= 100),
    technique INTEGER NOT NULL DEFAULT 50 CHECK (technique >= 0 AND technique <= 100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_player_stats_user_id ON player_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_position ON player_stats(position);
CREATE INDEX IF NOT EXISTS idx_player_stats_overall ON player_stats(overall DESC);
CREATE INDEX IF NOT EXISTS idx_player_stats_archetype ON player_stats(playstyle_archetype);

CREATE TABLE IF NOT EXISTS match_performance (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    event_id VARCHAR(36) REFERENCES event(id) ON DELETE SET NULL,
    sport_type VARCHAR(50) NOT NULL,
    goals INTEGER NOT NULL DEFAULT 0 CHECK (goals >= 0),
    assists INTEGER NOT NULL DEFAULT 0 CHECK (assists >= 0),
    points INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
    rebounds INTEGER NOT NULL DEFAULT 0 CHECK (rebounds >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_match_performance_user_id ON match_performance(user_id);
CREATE INDEX IF NOT EXISTS idx_match_performance_event_id ON match_performance(event_id);
CREATE INDEX IF NOT EXISTS idx_match_performance_sport_type ON match_performance(sport_type);
CREATE INDEX IF NOT EXISTS idx_match_performance_created_at ON match_performance(created_at DESC);
