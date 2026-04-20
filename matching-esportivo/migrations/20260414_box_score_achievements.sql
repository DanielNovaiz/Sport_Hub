-- MODO B: Box Score dinâmico + conquistas futebol/vôlei

ALTER TABLE match_performance
    ADD COLUMN IF NOT EXISTS sub_type VARCHAR(20),
    ADD COLUMN IF NOT EXISTS tackles INTEGER NOT NULL DEFAULT 0 CHECK (tackles >= 0),
    ADD COLUMN IF NOT EXISTS dribbles INTEGER NOT NULL DEFAULT 0 CHECK (dribbles >= 0),
    ADD COLUMN IF NOT EXISTS aces INTEGER NOT NULL DEFAULT 0 CHECK (aces >= 0),
    ADD COLUMN IF NOT EXISTS attacks INTEGER NOT NULL DEFAULT 0 CHECK (attacks >= 0),
    ADD COLUMN IF NOT EXISTS defenses INTEGER NOT NULL DEFAULT 0 CHECK (defenses >= 0),
    ADD COLUMN IF NOT EXISTS sets INTEGER NOT NULL DEFAULT 0 CHECK (sets >= 0);

CREATE INDEX IF NOT EXISTS idx_match_performance_sub_type ON match_performance(sub_type);
