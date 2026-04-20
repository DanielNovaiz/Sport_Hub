import 'package:freezed_annotation/freezed_annotation.dart';

part 'player_stats.freezed.dart';
part 'player_stats.g.dart';

@freezed
class PlayerStats with _$PlayerStats {
  const factory PlayerStats({
    required String id,
    required String name,
    required String position,
    required int assists,
    required int goals,
    required int matches,
    required double rating,
    required DateTime lastUpdated,
  }) = _PlayerStats;

  factory PlayerStats.fromJson(Map<String, dynamic> json) =>
      _$PlayerStatsFromJson(json);
}

@freezed
class PlayerStatsResponse with _$PlayerStatsResponse {
  const factory PlayerStatsResponse({
    required List<PlayerStats> stats,
    required DateTime fetchedAt,
  }) = _PlayerStatsResponse;

  factory PlayerStatsResponse.fromJson(Map<String, dynamic> json) =>
      _$PlayerStatsResponseFromJson(json);
}
