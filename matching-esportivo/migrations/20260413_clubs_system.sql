-- Clubes Esportivos: entidades, relações e suporte a eventos privados

CREATE TABLE IF NOT EXISTS club (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(1000),
    owner_id VARCHAR(36) NOT NULL REFERENCES "user"(id),
    sport_type VARCHAR(50) NOT NULL,
    privacy_type VARCHAR(20) NOT NULL,
    location geometry(POINT, 4326) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS club_member (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id),
    club_id VARCHAR(36) NOT NULL REFERENCES club(id),
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_club_member_user_club UNIQUE (user_id, club_id)
);

ALTER TABLE event
ADD COLUMN IF NOT EXISTS club_id VARCHAR(36) REFERENCES club(id);

CREATE INDEX IF NOT EXISTS idx_club_owner_id ON club(owner_id);
CREATE INDEX IF NOT EXISTS idx_club_sport_type ON club(sport_type);
CREATE INDEX IF NOT EXISTS idx_club_privacy_type ON club(privacy_type);
CREATE INDEX IF NOT EXISTS idx_club_location ON club USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_club_location_geography ON club USING GIST((location::geography));

CREATE INDEX IF NOT EXISTS idx_club_member_club_id ON club_member(club_id);
CREATE INDEX IF NOT EXISTS idx_club_member_user_id ON club_member(user_id);
CREATE INDEX IF NOT EXISTS idx_club_member_status ON club_member(status);

CREATE INDEX IF NOT EXISTS idx_event_club_id ON event(club_id);