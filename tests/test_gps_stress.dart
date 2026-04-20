import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:provider/provider.dart';
import 'package:flutter/material.dart';

// Importar os serviços e notifiers
import 'package:matching_esportivo_mobile/presentation/providers/court_list_notifier.dart';
import 'package:matching_esportivo_mobile/data/services/location_service.dart';
import 'package:matching_esportivo_mobile/service_locator.dart';

void main() {
  group('GPS Stress Tests - CourtList Navigation', () {
    late CourtListNotifier notifier;

    setUp(() async {
      // Setup
      await setupServiceLocator();
      useMockApiService(MockApiService());

      notifier = CourtListNotifier(
        getIt.get(),
        getIt.get(),
      );
    });

    tearDown(() async {
      await notifier.dispose();
    });

    testWidgets(
      'GPS Strong → GPS Lost → GPS Strong durante fetchAvailableCourts',
      (WidgetTester tester) async {
        // 1. Estado inicial: GPS forte, carregando quadras
        print('📍 [1] Iniciando com GPS forte...');
        expect(notifier.gpsStatus, GPSSignalStatus.disabled); // Inicial

        // 2. Solicita localização
        print('📍 [2] Solicitando localização do usuário...');
        await notifier.requestUserLocation();
        await tester.pumpAndSettle();

        // 3. Simula sucesso na localização
        expect(
          notifier.lastLocationStatus,
          anyOf(
            LocationStatus.success,
            LocationStatus.timeout, // Fallback OK
          ),
        );
        print('✅ [3] Localização obtida (forte ou fallback)');

        // 4. Inicia busca de quadras
        print('📍 [4] Iniciando busca de quadras...');
        final fetchFuture = notifier.fetchAvailableCourts(
          useUserLocation: true,
          sport: 'Futebol',
        );

        // Aguarda um pouco para a requisição começar
        await Future.delayed(Duration(milliseconds: 100));

        // 5. Simula PERDA DE SINAL durante a navegação
        print('⚠️ [5] SIMULANDO PERDA DE SINAL GPS...');
        notifier.simulateGPSLoss();
        await tester.pumpAndSettle();

        expect(notifier.gpsStatus, GPSSignalStatus.lost);
        expect(notifier.errorMessage, contains('GPS perdido'));
        print('⚠️ [5] Sinal perdido detectado!');

        // 6. Aguarda fetch terminar
        await fetchFuture;
        await tester.pumpAndSettle();

        // 7. Verifica que ainda temos fallback de localização
        expect(notifier.userLatitude, isNotNull);
        expect(notifier.userLongitude, isNotNull);
        print('✅ [7] Fallback de localização mantém app funcionando');

        // 8. Simula RECUPERAÇÃO do sinal
        print('📍 [8] SIMULANDO RECUPERAÇÃO DE SINAL GPS...');
        notifier.simulateGPSRecovery();
        await tester.pumpAndSettle();

        expect(notifier.gpsStatus, GPSSignalStatus.strong);
        expect(notifier.errorMessage, isEmpty);
        print('✅ [8] Sinal recuperado!');

        // 9. Refetch com novo sinal
        print('📍 [9] Refetching quadras com novo sinal...');
        await notifier.fetchAvailableCourts(forceRefresh: true);
        await tester.pumpAndSettle();

        expect(notifier.state, LoadingState.success);
        print('✅ [9] Quadras atualizadas com sucesso!');
      },
    );

    testWidgets(
      'Múltiplas oscilações de sinal durante CourtList scroll',
      (WidgetTester tester) async {
        print('\n📊 TESTE: Múltiplas oscilações de sinal\n');

        // Setup inicial
        await notifier.requestUserLocation();
        await notifier.fetchAvailableCourts(useUserLocation: true);
        await tester.pumpAndSettle();

        // Lista de oscilações
        final oscillations = [
          ('Sinal forte (A)', GPSSignalStatus.strong, false),
          ('Sinal fraco', GPSSignalStatus.weak, true),
          ('Sinal perdido', GPSSignalStatus.lost, true),
          ('Sinal fraco', GPSSignalStatus.weak, true),
          ('Sinal forte (B)', GPSSignalStatus.strong, false),
        ];

        for (final (description, status, hasError) in oscillations) {
          print('📍 $description');

          if (status == GPSSignalStatus.strong) {
            notifier.simulateGPSRecovery();
          } else {
            notifier.simulateGPSLoss();
          }

          await tester.pumpAndSettle();
          await Future.delayed(Duration(milliseconds: 200));

          expect(notifier.gpsStatus, status);

          if (hasError) {
            expect(notifier.errorMessage, isNotEmpty);
          }

          print('✅ $description detectado corretamente');
        }

        print('\n✅ Oscilações gerenciadas com sucesso!\n');
      },
    );

    testWidgets(
      'GPS Lost mantém dados em cache durante outage',
      (WidgetTester tester) async {
        print('\n📊 TESTE: Cache durante outage de GPS\n');

        // 1. Carrega dados com sucesso
        print('📍 [1] Carregando dados de quadras...');
        await notifier.fetchAvailableCourts(useUserLocation: true);
        await tester.pumpAndSettle();

        final courtsBeforeLoss = notifier.courts.length;
        expect(courtsBeforeLoss, greaterThan(0));
        print('✅ [1] ${courtsBeforeLoss} quadras carregadas');

        // 2. Simula perda de GPS
        print('📍 [2] Simulando perda de GPS...');
        notifier.simulateGPSLoss();
        await tester.pumpAndSettle();

        // 3. Verifica que dados ainda estão em memória
        print('📍 [3] Verificando dados em cache...');
        final courtsAfterLoss = notifier.courts.length;
        expect(courtsAfterLoss, equals(courtsBeforeLoss));
        print('✅ [3] ${courtsAfterLoss} quadras ainda disponíveis (cache)');

        // 4. Tenta filtrar (operações locais devem funcionar)
        print('📍 [4] Tentando filtrar por esporte...');
        if (notifier.courts.isNotEmpty) {
          final sport = notifier.courts.first.sport;
          notifier.filterBySport(sport);
          await tester.pumpAndSettle();
          expect(notifier.courts.isNotEmpty, true);
          print('✅ [4] Filtro funciona mesmo sem GPS');
        }

        // 5. Recupera GPS e refetch
        print('📍 [5] GPS recuperado, refetching...');
        notifier.simulateGPSRecovery();
        await notifier.fetchAvailableCourts(forceRefresh: true);
        await tester.pumpAndSettle();

        expect(notifier.state, LoadingState.success);
        print('✅ [5] Dados atualizados após recuperação');
      },
    );

    testWidgets(
      'Lifecycle: pausa GPS ao ir para background',
      (WidgetTester tester) async {
        print('\n📊 TESTE: Lifecycle do GPS\n');

        // 1. Inicia escuta de GPS
        print('📍 [1] Iniciando escuta contínua de GPS...');
        await notifier.startListeningToLocation();
        await tester.pumpAndSettle();

        expect(notifier.isListeningToGPS, true);
        print('✅ [1] Escuta ativa (gasta bateria)');

        // 2. Aguarda um pouco
        await Future.delayed(Duration(milliseconds: 500));

        // 3. Pausa GPS (como se app fosse para background)
        print('📍 [2] App vai para background - parando GPS...');
        await notifier.stopListeningToLocation();
        await tester.pumpAndSettle();

        expect(notifier.isListeningToGPS, false);
        print('✅ [2] Escuta parada (economiza bateria)');

        // 4. App volta (foreground)
        print('📍 [3] App volta ao foreground - retomando GPS...');
        await notifier.startListeningToLocation();
        await tester.pumpAndSettle();

        expect(notifier.isListeningToGPS, true);
        print('✅ [3] Escuta retomada');
      },
    );

    testWidgets(
      'Permissões: GPS desligado mostra fallback educativo',
      (WidgetTester tester) async {
        print('\n📊 TESTE: Fallback para Novo Mundo\n');

        // Simula GPS desligado
        print('📍 GPS desligado - obtendo fallback...');
        final result = await LocationService.getLocationWithFallback();

        expect(result.latitude, isNotNull);
        expect(result.longitude, isNotNull);

        // Fallback para Novo Mundo
        const defaultLat = -15.7942;
        const defaultLng = -48.0676;

        if (result.status != LocationStatus.success) {
          expect(
            result.latitude,
            moreOrLessEquals(defaultLat, epsilon: 0.001),
          );
          expect(
            result.longitude,
            moreOrLessEquals(defaultLng, epsilon: 0.001),
          );
          print('✅ Fallback ativado (Novo Mundo, Goiânia)');
        }
      },
    );
  });
}

// Mock para gerar dados fake
class MockApiService {
  // Implementação em service_locator.dart
}
