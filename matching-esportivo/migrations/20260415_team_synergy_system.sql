-- Team Synergy System: duplas/trios com histórico de vitórias conjuntas

CREATE TABLE IF NOT EXISTS team_synergy (
    id VARCHAR(36) PRIMARY KEY,
    club_id VARCHAR(36) NOT NULL REFERENCES club(id),
    members_key VARCHAR(512) NOT NULL,
    group_size INTEGER NOT NULL CHECK (group_size BETWEEN 2 AND 3),
    status VARCHAR(16) NOT NULL DEFAULT 'none',
    matches_together INTEGER NOT NULL DEFAULT 0,
    wins_together INTEGER NOT NULL DEFAULT 0,
    win_rate DOUBLE PRECISION NOT NULL DEFAULT 0,
    sport_type VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_team_synergy_club_members UNIQUE (club_id, members_key)
);

CREATE INDEX IF NOT EXISTS idx_team_synergy_club_id ON team_synergy(club_id);
CREATE INDEX IF NOT EXISTS idx_team_synergy_members_key ON team_synergy(members_key);
CREATE INDEX IF NOT EXISTS idx_team_synergy_status ON team_synergy(status);
