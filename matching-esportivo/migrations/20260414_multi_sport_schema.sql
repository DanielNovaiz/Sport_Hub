-- Migração MODO B: Futebol, Goleiro, Vôlei e sub_type de partida/evento

ALTER TABLE player_stats
    ADD COLUMN IF NOT EXISTS short_finish INTEGER NOT NULL DEFAULT 50 CHECK (short_finish >= 0 AND short_finish <= 99),
    ADD COLUMN IF NOT EXISTS long_shot INTEGER NOT NULL DEFAULT 50 CHECK (long_shot >= 0 AND long_shot <= 99),
    ADD COLUMN IF NOT EXISTS heading INTEGER NOT NULL DEFAULT 50 CHECK (heading >= 0 AND heading <= 99),
    ADD COLUMN IF NOT EXISTS free_kick INTEGER NOT NULL DEFAULT 50 CHECK (free_kick >= 0 AND free_kick <= 99),
    ADD COLUMN IF NOT EXISTS short_pass INTEGER NOT NULL DEFAULT 50 CHECK (short_pass >= 0 AND short_pass <= 99),
    ADD COLUMN IF NOT EXISTS long_pass INTEGER NOT NULL DEFAULT 50 CHECK (long_pass >= 0 AND long_pass <= 99),
    ADD COLUMN IF NOT EXISTS crossing INTEGER NOT NULL DEFAULT 50 CHECK (crossing >= 0 AND crossing <= 99),
    ADD COLUMN IF NOT EXISTS dribbling INTEGER NOT NULL DEFAULT 50 CHECK (dribbling >= 0 AND dribbling <= 99),
    ADD COLUMN IF NOT EXISTS ball_shielding INTEGER NOT NULL DEFAULT 50 CHECK (ball_shielding >= 0 AND ball_shielding <= 99),
    ADD COLUMN IF NOT EXISTS sprint INTEGER NOT NULL DEFAULT 50 CHECK (sprint >= 0 AND sprint <= 99),
    ADD COLUMN IF NOT EXISTS acceleration INTEGER NOT NULL DEFAULT 50 CHECK (acceleration >= 0 AND acceleration <= 99),
    ADD COLUMN IF NOT EXISTS stamina INTEGER NOT NULL DEFAULT 50 CHECK (stamina >= 0 AND stamina <= 99),
    ADD COLUMN IF NOT EXISTS tackle INTEGER NOT NULL DEFAULT 50 CHECK (tackle >= 0 AND tackle <= 99),
    ADD COLUMN IF NOT EXISTS interception INTEGER NOT NULL DEFAULT 50 CHECK (interception >= 0 AND interception <= 99),
    ADD COLUMN IF NOT EXISTS marking INTEGER NOT NULL DEFAULT 50 CHECK (marking >= 0 AND marking <= 99),
    ADD COLUMN IF NOT EXISTS reflexes INTEGER NOT NULL DEFAULT 50 CHECK (reflexes >= 0 AND reflexes <= 99),
    ADD COLUMN IF NOT EXISTS elasticity INTEGER NOT NULL DEFAULT 50 CHECK (elasticity >= 0 AND elasticity <= 99),
    ADD COLUMN IF NOT EXISTS box_presence INTEGER NOT NULL DEFAULT 50 CHECK (box_presence >= 0 AND box_presence <= 99),
    ADD COLUMN IF NOT EXISTS distribution INTEGER NOT NULL DEFAULT 50 CHECK (distribution >= 0 AND distribution <= 99),
    ADD COLUMN IF NOT EXISTS spike_power INTEGER NOT NULL DEFAULT 50 CHECK (spike_power >= 0 AND spike_power <= 99),
    ADD COLUMN IF NOT EXISTS spike_accuracy INTEGER NOT NULL DEFAULT 50 CHECK (spike_accuracy >= 0 AND spike_accuracy <= 99),
    ADD COLUMN IF NOT EXISTS serve_power INTEGER NOT NULL DEFAULT 50 CHECK (serve_power >= 0 AND serve_power <= 99),
    ADD COLUMN IF NOT EXISTS serve_tactical INTEGER NOT NULL DEFAULT 50 CHECK (serve_tactical >= 0 AND serve_tactical <= 99),
    ADD COLUMN IF NOT EXISTS reception INTEGER NOT NULL DEFAULT 50 CHECK (reception >= 0 AND reception <= 99),
    ADD COLUMN IF NOT EXISTS floor_defense INTEGER NOT NULL DEFAULT 50 CHECK (floor_defense >= 0 AND floor_defense <= 99),
    ADD COLUMN IF NOT EXISTS coverage INTEGER NOT NULL DEFAULT 50 CHECK (coverage >= 0 AND coverage <= 99),
    ADD COLUMN IF NOT EXISTS setting INTEGER NOT NULL DEFAULT 50 CHECK (setting >= 0 AND setting <= 99),
    ADD COLUMN IF NOT EXISTS creativity INTEGER NOT NULL DEFAULT 50 CHECK (creativity >= 0 AND creativity <= 99),
    ADD COLUMN IF NOT EXISTS game_vision INTEGER NOT NULL DEFAULT 50 CHECK (game_vision >= 0 AND game_vision <= 99),
    ADD COLUMN IF NOT EXISTS lateral_agility INTEGER NOT NULL DEFAULT 50 CHECK (lateral_agility >= 0 AND lateral_agility <= 99),
    ADD COLUMN IF NOT EXISTS reaction INTEGER NOT NULL DEFAULT 50 CHECK (reaction >= 0 AND reaction <= 99),
    ADD COLUMN IF NOT EXISTS coordination INTEGER NOT NULL DEFAULT 50 CHECK (coordination >= 0 AND coordination <= 99);

ALTER TABLE event
    ADD COLUMN IF NOT EXISTS sub_type VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_event_sub_type ON event(sub_type);
