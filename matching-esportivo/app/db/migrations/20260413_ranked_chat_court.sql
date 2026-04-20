-- FASE 1: Ranked + Chat + Court Tables
-- UUID auto-generation + indexes

CREATE TABLE IF NOT EXISTS user_rank (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,
    mmr INTEGER DEFAULT 0 NOT NULL CHECK (mmr >= 0),
    division VARCHAR(20) DEFAULT 'bronze' NOT NULL,
    league VARCHAR(50) DEFAULT 'competitive' NOT NULL,
    wins INTEGER DEFAULT 0 NOT NULL,
    losses INTEGER DEFAULT 0 NOT NULL,
    win_rate FLOAT DEFAULT 0.0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    CONSTRAINT fk_user_rank_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_rank_mmr ON user_rank(mmr DESC);
CREATE INDEX idx_user_rank_division ON user_rank(division);
CREATE INDEX idx_user_rank_created_at ON user_rank(created_at DESC);

CREATE TABLE IF NOT EXISTS chat_room (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    event_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    CONSTRAINT fk_chat_room_event FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE CASCADE,
    CONSTRAINT uq_chat_room_event UNIQUE (event_id)
);

CREATE INDEX idx_chat_room_event ON chat_room(event_id);
CREATE INDEX idx_chat_room_created_at ON chat_room(created_at DESC);

CREATE TABLE IF NOT EXISTS chat_message (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    chat_room_id UUID NOT NULL,
    user_id UUID NOT NULL,
    content VARCHAR(500) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    CONSTRAINT fk_chat_message_room FOREIGN KEY (chat_room_id) REFERENCES chat_room(id) ON DELETE CASCADE,
    CONSTRAINT fk_chat_message_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE INDEX idx_chat_message_room ON chat_message(chat_room_id);
CREATE INDEX idx_chat_message_user ON chat_message(user_id);
CREATE INDEX idx_chat_message_created_at ON chat_message(created_at DESC);

CREATE TABLE IF NOT EXISTS court (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    owner_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    sport_type VARCHAR(50) NOT NULL,
    location GEOMETRY(Point, 4326) NOT NULL,
    price_per_hour DECIMAL(10, 2) DEFAULT 100.00 NOT NULL CHECK (price_per_hour > 0),
    photos_url TEXT[] DEFAULT ARRAY[]::TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    CONSTRAINT fk_court_owner FOREIGN KEY (owner_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE INDEX idx_court_owner ON court(owner_id);
CREATE INDEX idx_court_location ON court USING GIST(location);
CREATE INDEX idx_court_sport_type ON court(sport_type);
CREATE INDEX idx_court_created_at ON court(created_at DESC);

CREATE TABLE IF NOT EXISTS booking (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    court_id UUID NOT NULL,
    user_id UUID NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() AT TIME ZONE 'UTC' NOT NULL,
    CONSTRAINT fk_booking_court FOREIGN KEY (court_id) REFERENCES court(id) ON DELETE CASCADE,
    CONSTRAINT fk_booking_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT check_booking_times CHECK (start_time < end_time)
);

CREATE INDEX idx_booking_court ON booking(court_id);
CREATE INDEX idx_booking_user ON booking(user_id);
CREATE INDEX idx_booking_start_time ON booking(start_time DESC);
CREATE INDEX idx_booking_end_time ON booking(end_time DESC);
CREATE INDEX idx_booking_status ON booking(status);
CREATE INDEX idx_booking_created_at ON booking(created_at DESC);
