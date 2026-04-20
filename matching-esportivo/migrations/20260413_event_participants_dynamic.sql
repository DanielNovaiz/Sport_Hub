-- Modo B Expansion: eventos dinâmicos com inscrições e sugestões

ALTER TABLE event
ADD COLUMN IF NOT EXISTS max_participants INTEGER NOT NULL DEFAULT 10;

CREATE TABLE IF NOT EXISTS event_participant (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id),
    event_id VARCHAR(36) NOT NULL REFERENCES event(id),
    joined_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL,
    CONSTRAINT uq_event_participant_user_event UNIQUE (user_id, event_id)
);

ALTER TABLE "user"
ADD COLUMN IF NOT EXISTS location geometry(POINT, 4326);

CREATE INDEX IF NOT EXISTS idx_event_participant_event_id ON event_participant(event_id);
CREATE INDEX IF NOT EXISTS idx_event_participant_user_id ON event_participant(user_id);
CREATE INDEX IF NOT EXISTS idx_event_participant_status ON event_participant(status);
CREATE INDEX IF NOT EXISTS idx_user_location ON "user" USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_user_location_geography ON "user" USING GIST((location::geography));

CREATE INDEX IF NOT EXISTS idx_event_location ON event USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_event_status ON event(status);
CREATE INDEX IF NOT EXISTS idx_event_scheduled_time ON event(scheduled_time);