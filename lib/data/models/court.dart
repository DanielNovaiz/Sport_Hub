import 'package:freezed_annotation/freezed_annotation.dart';

part 'court.freezed.dart';
part 'court.g.dart';

@freezed
class Court with _$Court {
  const factory Court({
    required String id,
    required String name,
    required String location,
    required double latitude,
    required double longitude,
    required String sport,
    required int availableSlots,
    required int totalSlots,
    required double price,
    required DateTime lastChecked,
  }) = _Court;

  factory Court.fromJson(Map<String, dynamic> json) =>
      _$CourtFromJson(json);
}

@freezed
class CourtsResponse with _$CourtsResponse {
  const factory CourtsResponse({
    required List<Court> courts,
    required DateTime fetchedAt,
  }) = _CourtsResponse;

  factory CourtsResponse.fromJson(Map<String, dynamic> json) =>
      _$CourtsResponseFromJson(json);
}
