-- Índice para ranking regional por overall_score (PlayerStats.overall)
-- Requisito: Top jogadores ordenados por overall_score

CREATE INDEX IF NOT EXISTS idx_player_stats_overall_score
ON player_stats(overall DESC);
