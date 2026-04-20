import 'package:flutter/foundation.dart';
import '../data/models/player_stats.dart';
import '../data/services/api_service.dart';
import '../data/services/local_storage_service.dart';
import '../service_locator.dart';

/// Estado de carregamento
enum LoadingState { idle, loading, success, error }

/// Notifier que gerencia o estado global de estatísticas de jogadores
/// - Sincroniza dados entre telas automaticamente
/// - Persiste dados localmente
/// - Restaura estado ao retomar o app
class PlayerStatsNotifier extends ChangeNotifier {
  final ApiService _apiService;
  final LocalStorageService _localStorage;

  // Estado privado
  List<PlayerStats> _stats = [];
  LoadingState _state = LoadingState.idle;
  String _errorMessage = '';
  DateTime? _lastFetch;

  // Getters públicos
  List<PlayerStats> get stats => _stats;
  LoadingState get state => _state;
  String get errorMessage => _errorMessage;
  bool get isLoading => _state == LoadingState.loading;
  bool get hasError => _state == LoadingState.error;

  /// Indica se o cache é válido (menos de 30 minutos)
  bool get isCacheValid => _localStorage.isCacheExpired() == false;

  /// Tempo desde a última busca (em minutos)
  int get minutesSinceLastFetch {
    if (_lastFetch == null) return -1;
    return DateTime.now().difference(_lastFetch!).inMinutes;
  }

  PlayerStatsNotifier(this._apiService, this._localStorage) {
    _initialize();
  }

  /// Inicializa carregando dados do cache
  Future<void> _initialize() async {
    await _restoreFromCache();
  }

  /// Restaura dados do cache local
  Future<void> _restoreFromCache() async {
    try {
      final cachedStats = await _localStorage.getPlayerStats();
      if (cachedStats.isNotEmpty) {
        _stats = cachedStats;
        _state = LoadingState.success;
        notifyListeners();
      }
    } catch (e) {
      print('Erro ao restaurar cache: $e');
    }
  }

  /// Busca estatísticas do servidor e persiste localmente
  Future<void> fetchAllPlayerStats({bool forceRefresh = false}) async {
    // Se cache é válido e não é refresh forçado, ignora requisição
    if (isCacheValid && !forceRefresh) {
      return;
    }

    _state = LoadingState.loading;
    _errorMessage = '';
    notifyListeners();

    try {
      final response = await _apiService.getAllPlayerStats();
      _stats = response.stats;
      _lastFetch = response.fetchedAt;
      _state = LoadingState.success;

      // Persiste no cache
      await _localStorage.savePlayerStats(_stats);
    } catch (e) {
      _state = LoadingState.error;
      _errorMessage = e.toString();
      print('Erro ao buscar stats: $e');
    }

    notifyListeners();
  }

  /// Busca estatísticas de um jogador específico
  Future<PlayerStats?> fetchPlayerStats(String playerId) async {
    try {
      return await _apiService.getPlayerStats(playerId);
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    }
  }

  /// Atualiza estatísticas de um jogador localmente e no servidor
  /// Mantém otimismo - atualiza UI imediatamente
  Future<void> updatePlayerStats(
    String playerId,
    Map<String, dynamic> updates,
  ) async {
    try {
      // Otimismo: atualiza localmente primeiro
      final index = _stats.indexWhere((s) => s.id == playerId);
      if (index != -1) {
        final current = _stats[index];
        _stats[index] = current.copyWith(
          assists: updates['assists'] ?? current.assists,
          goals: updates['goals'] ?? current.goals,
          rating: updates['rating'] ?? current.rating,
          matches: updates['matches'] ?? current.matches,
          lastUpdated: DateTime.now(),
        );
        notifyListeners();
      }

      // Sincroniza com servidor
      await _apiService.updatePlayerStats(playerId, updates);

      // Persiste no cache
      await _localStorage.savePlayerStats(_stats);

      _state = LoadingState.success;
    } catch (e) {
      _state = LoadingState.error;
      _errorMessage = e.toString();
      // Recarrega stats do servidor para descartar otimismo
      await fetchAllPlayerStats(forceRefresh: true);
    }

    notifyListeners();
  }

  /// Busca estatísticas de um jogador específico por nome
  PlayerStats? findByName(String name) {
    try {
      return _stats.firstWhere(
        (s) => s.name.toLowerCase().contains(name.toLowerCase()),
      );
    } catch (e) {
      return null;
    }
  }

  /// Busca estatísticas de jogadores por posição
  List<PlayerStats> findByPosition(String position) {
    return _stats
        .where((s) => s.position.toLowerCase() == position.toLowerCase())
        .toList();
  }

  /// Limpa todos os dados
  Future<void> clearAll() async {
    _stats = [];
    _state = LoadingState.idle;
    _errorMessage = '';
    _lastFetch = null;
    await _localStorage.clearPlayerStats();
    notifyListeners();
  }

  /// Força atualização sem mudança de estado
  /// Útil quando uma tela atualizou dados e quer notificar outras
  void refreshUI() {
    notifyListeners();
  }
}
