import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/player_stats.dart';
import '../models/court.dart';

/// Serviço de persistência local para cache de dados
class LocalStorageService {
  static const String _playerStatsKey = 'player_stats_cache';
  static const String _courtsKey = 'courts_cache';
  static const String _userProfileKey = 'user_profile_cache';
  static const String _matchStateKey = 'match_entry_state';
  static const String _lastSyncKey = 'last_sync_timestamp';

  final SharedPreferences _prefs;

  LocalStorageService(this._prefs);

  /// ==================== PLAYER STATS ====================

  /// Salva cache de estatísticas de jogadores
  Future<void> savePlayerStats(List<PlayerStats> stats) async {
    final json = jsonEncode(stats.map((s) => s.toJson()).toList());
    await _prefs.setString(_playerStatsKey, json);
    await _updateLastSync();
  }

  /// Recupera cache de estatísticas
  Future<List<PlayerStats>> getPlayerStats() async {
    final json = _prefs.getString(_playerStatsKey);
    if (json == null) return [];

    try {
      final list = jsonDecode(json) as List;
      return list
          .map((item) => PlayerStats.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      print('Erro ao desserializar stats: $e');
      return [];
    }
  }

  /// Limpa cache de stats
  Future<void> clearPlayerStats() => _prefs.remove(_playerStatsKey);

  /// ==================== COURTS ====================

  /// Salva cache de quadras disponíveis
  Future<void> saveCourts(List<Court> courts) async {
    final json = jsonEncode(courts.map((c) => c.toJson()).toList());
    await _prefs.setString(_courtsKey, json);
    await _updateLastSync();
  }

  /// Recupera cache de quadras
  Future<List<Court>> getCourts() async {
    final json = _prefs.getString(_courtsKey);
    if (json == null) return [];

    try {
      final list = jsonDecode(json) as List;
      return list
          .map((item) => Court.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      print('Erro ao desserializar courts: $e');
      return [];
    }
  }

  /// Limpa cache de quadras
  Future<void> clearCourts() => _prefs.remove(_courtsKey);

  /// ==================== USER PROFILE ====================

  /// Salva perfil do usuário
  Future<void> saveUserProfile(Map<String, dynamic> profile) async {
    final json = jsonEncode(profile);
    await _prefs.setString(_userProfileKey, json);
  }

  /// Recupera perfil do usuário
  Future<Map<String, dynamic>?> getUserProfile() async {
    final json = _prefs.getString(_userProfileKey);
    if (json == null) return null;

    try {
      return jsonDecode(json) as Map<String, dynamic>;
    } catch (e) {
      print('Erro ao desserializar perfil: $e');
      return null;
    }
  }

  /// Limpa perfil do usuário
  Future<void> clearUserProfile() => _prefs.remove(_userProfileKey);

  /// ==================== MATCH STATE (HYDRATION) ====================

  /// Salva estado de entrada de partida em edição
  /// Permite restaurar se o app fechar
  Future<void> saveMatchState(Map<String, dynamic> matchState) async {
    final json = jsonEncode(matchState);
    await _prefs.setString(_matchStateKey, json);
  }

  /// Recupera estado de partida em edição
  Future<Map<String, dynamic>?> getMatchState() async {
    final json = _prefs.getString(_matchStateKey);
    if (json == null) return null;

    try {
      return jsonDecode(json) as Map<String, dynamic>;
    } catch (e) {
      print('Erro ao desserializar match state: $e');
      return null;
    }
  }

  /// Limpa estado de partida
  Future<void> clearMatchState() => _prefs.remove(_matchStateKey);

  /// ==================== UTILITIES ====================

  /// Atualiza timestamp da última sincronização
  Future<void> _updateLastSync() async {
    await _prefs.setInt(_lastSyncKey, DateTime.now().millisecondsSinceEpoch);
  }

  /// Retorna tempo em minutos desde a última sincronização
  int getMinutesSinceLastSync() {
    final lastSync = _prefs.getInt(_lastSyncKey);
    if (lastSync == null) return -1;

    final diff = DateTime.now().millisecondsSinceEpoch - lastSync;
    return (diff / (1000 * 60)).toInt();
  }

  /// Verifica se o cache expirou (padrão: 30 minutos)
  bool isCacheExpired({int expireAfterMinutes = 30}) {
    return getMinutesSinceLastSync() > expireAfterMinutes;
  }

  /// Limpa todo o cache
  Future<void> clearAll() async {
    await clearPlayerStats();
    await clearCourts();
    await clearUserProfile();
    await clearMatchState();
    await _prefs.remove(_lastSyncKey);
  }
}
