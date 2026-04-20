import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'data/models/court.dart';
import 'data/models/player_stats.dart';
import 'data/services/api_service.dart';
import 'data/services/auth_token_provider.dart';
import 'data/services/dio_api_service.dart';
import 'data/services/local_storage_service.dart';

final getIt = GetIt.instance;

/// Configura todas as dependências da aplicação
/// Deve ser chamado no main() antes de runApp()
Future<void> setupServiceLocator() async {
  // ==================== EXTERNAL ====================
  final prefs = await SharedPreferences.getInstance();
  getIt.registerSingleton<SharedPreferences>(prefs);

  final dio = Dio();
  getIt.registerSingleton<Dio>(dio);

  // ==================== SECURITY / AUTH ====================
  getIt.registerSingleton<AuthTokenProvider>(
    SharedPrefsAuthTokenProvider(getIt<SharedPreferences>()),
  );

  // ==================== SERVICES ====================
  getIt.registerSingleton<LocalStorageService>(
    LocalStorageService(getIt<SharedPreferences>()),
  );

  // Registra ApiService como abstrato, mas usa DioApiService como implementação.
  getIt.registerSingleton<ApiService>(
    DioApiService(
      getIt<Dio>(),
      getIt<AuthTokenProvider>(),
    ),
  );

  // ==================== STATE MANAGEMENT ====================
  // Os Notifiers serão registrados posteriormente durante a inicialização do app.
}

/// Substitui a implementação de ApiService por uma Mock
/// Útil para testes de integração
void useMockApiService(MockApiService mockService) {
  if (getIt.isRegistered<ApiService>()) {
    getIt.unregister<ApiService>();
  }
  getIt.registerSingleton<ApiService>(mockService);
}

/// Mock básico de ApiService para testes
class MockApiService implements ApiService {
  final Duration mockDelay = const Duration(milliseconds: 500);

  @override
  Future<PlayerStats> getPlayerStats(String playerId) async {
    await Future.delayed(mockDelay);
    return PlayerStats(
      id: playerId,
      name: 'Test Player',
      position: 'Goleiro',
      assists: 0,
      goals: 5,
      matches: 10,
      rating: 4.5,
      lastUpdated: DateTime.now(),
    );
  }

  @override
  Future<PlayerStatsResponse> getAllPlayerStats() async {
    await Future.delayed(mockDelay);
    return PlayerStatsResponse(
      stats: [
        PlayerStats(
          id: '1',
          name: 'Player 1',
          position: 'Atacante',
          assists: 5,
          goals: 15,
          matches: 20,
          rating: 4.8,
          lastUpdated: DateTime.now(),
        ),
      ],
      fetchedAt: DateTime.now(),
    );
  }

  @override
  Future<PlayerStats> updatePlayerStats(
    String playerId,
    Map<String, dynamic> updates,
  ) async {
    await Future.delayed(mockDelay);
    return PlayerStats(
      id: playerId,
      name: 'Updated Player',
      position: 'Defesa',
      assists: updates['assists'] ?? 0,
      goals: updates['goals'] ?? 0,
      matches: updates['matches'] ?? 10,
      rating: updates['rating'] ?? 4.5,
      lastUpdated: DateTime.now(),
    );
  }

  @override
  Future<CourtsResponse> getAvailableCourts({
    double? latitude,
    double? longitude,
    String? sport,
  }) async {
    await Future.delayed(mockDelay);
    return CourtsResponse(
      courts: [
        Court(
          id: '1',
          name: 'Quadra 1',
          location: 'Setor Bueno',
          latitude: latitude ?? -15.7942,
          longitude: longitude ?? -48.0676,
          sport: sport ?? 'Futebol',
          availableSlots: 2,
          totalSlots: 4,
          price: 150,
          lastChecked: DateTime.now(),
        ),
      ],
      fetchedAt: DateTime.now(),
    );
  }

  @override
  Future<Court> getCourtDetails(String courtId) async {
    await Future.delayed(mockDelay);
    return Court(
      id: courtId,
      name: 'Quadra Detalhes',
      location: 'Setor Bueno',
      latitude: -15.7942,
      longitude: -48.0676,
      sport: 'Futebol',
      availableSlots: 2,
      totalSlots: 4,
      price: 150,
      lastChecked: DateTime.now(),
    );
  }

  @override
  Future<Court> updateCourtSlots(String courtId, int availableSlots) async {
    await Future.delayed(mockDelay);
    return Court(
      id: courtId,
      name: 'Quadra Atualizada',
      location: 'Setor Bueno',
      latitude: -15.7942,
      longitude: -48.0676,
      sport: 'Futebol',
      availableSlots: availableSlots,
      totalSlots: 4,
      price: 150,
      lastChecked: DateTime.now(),
    );
  }
}
