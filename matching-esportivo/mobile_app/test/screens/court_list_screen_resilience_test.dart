import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:geolocator/geolocator.dart';

import 'package:matching_esportivo_mobile/core/app_exception.dart';
import 'package:matching_esportivo_mobile/models/court_marketplace.dart';
import 'package:matching_esportivo_mobile/screens/court_list_screen.dart';
import 'package:matching_esportivo_mobile/services/api_service.dart';

class _PermissionDeniedLocationService implements CourtLocationService {
  @override
  Future<LocationPermission> checkPermission() async =>
      LocationPermission.whileInUse;

  @override
  Future<Position> getCurrentPosition() {
    throw const PermissionDeniedException('GPS permission denied in test');
  }

  @override
  Future<bool> isLocationServiceEnabled() async => true;

  @override
  Future<LocationPermission> requestPermission() async =>
      LocationPermission.whileInUse;
}

class _ResilientCourtsApiService extends ApiService {
  _ResilientCourtsApiService();

  @override
  Future<List<CourtMarketplaceItem>> getNearbyCourts({
    required double latitude,
    required double longitude,
    double radiusKm = 15,
    String? sportType,
    int limit = 100,
  }) async {
    throw AppException('Falha PostGIS nearby (simulada)');
  }

  @override
  Future<List<CourtMarketplaceItem>> getCourts({
    String? sportType,
    int limit = 100,
  }) async {
    return const [
      CourtMarketplaceItem(
        id: 'court-1',
        ownerId: 'owner-1',
        name: 'Arena Novo Mundo',
        description: 'Quadra indoor com iluminação LED',
        sportType: 'futebol',
        pricePerHour: 120,
        photosUrl: [],
        latitude: -16.7320,
        longitude: -49.2670,
      ),
    ];
  }
}

void main() {
  testWidgets(
      'CourtListScreen usa fallback Novo Mundo e captura AppException sem quebrar o fluxo',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: CourtListScreen(
          userId: 'user-1',
          apiService: _ResilientCourtsApiService(),
          locationService: _PermissionDeniedLocationService(),
        ),
      ),
    );

    // Evita pumpAndSettle por causa de shimmer animado contínuo.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pump(const Duration(milliseconds: 300));

    expect(
      find.text(
          'Sem GPS disponível. Usando referência de Goiânia (setor Novo Mundo).'),
      findsOneWidget,
    );

    expect(
      find.text(
          'Conexão instável no setor Novo Mundo. Exibindo quadras próximas em modo resiliente.'),
      findsOneWidget,
    );

    expect(find.text('Arena Novo Mundo'), findsOneWidget);

    // A AppException do endpoint nearby foi tratada e não exposta como erro fatal bruto.
    expect(find.text('Falha PostGIS nearby (simulada)'), findsNothing);
  });
}
