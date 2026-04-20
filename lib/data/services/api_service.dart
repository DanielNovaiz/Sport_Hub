import '../models/player_stats.dart';
import '../models/court.dart';

/// Contrato abstrato para chamadas API
/// Permite substituição fácil por MockApiService nos testes
abstract class ApiService {
  /// Busca estatísticas de um jogador por ID
  Future<PlayerStats> getPlayerStats(String playerId);

  /// Busca todas as estatísticas de jogadores
  Future<PlayerStatsResponse> getAllPlayerStats();

  /// Atualiza estatísticas de um jogador
  Future<PlayerStats> updatePlayerStats(
    String playerId,
    Map<String, dynamic> updates,
  );

  /// Busca quadras disponíveis
  Future<CourtsResponse> getAvailableCourts({
    double? latitude,
    double? longitude,
    String? sport,
  });

  /// Busca detalhes de uma quadra
  Future<Court> getCourtDetails(String courtId);

  /// Atualiza vagas disponíveis em uma quadra
  Future<Court> updateCourtSlots(String courtId, int availableSlots);
}
