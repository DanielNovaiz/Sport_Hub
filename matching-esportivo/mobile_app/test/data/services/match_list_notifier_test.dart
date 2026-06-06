import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:matching_esportivo_mobile/data/models/match.dart';
import 'package:matching_esportivo_mobile/data/services/api_service.dart';
import 'package:matching_esportivo_mobile/data/services/local_storage_service.dart';
import 'package:matching_esportivo_mobile/presentation/providers/match_list_notifier.dart';

@GenerateMocks([ApiService, LocalStorageService])
import 'match_list_notifier_test.mocks.dart';

void main() {
  late MatchListNotifier notifier;
  late MockApiService mockApiService;
  late MockLocalStorageService mockStorageService;

  setUp(() {
    mockApiService = MockApiService();
    mockStorageService = MockLocalStorageService();
    notifier = MatchListNotifier(mockApiService, mockStorageService);
  });

  group('MatchListNotifier', () {
    test('fetchMatches carrega matches da API', () async {
      // Arrange
      final matchesData = [
        {
          'id': 'match1',
          'court_id': 'court1',
          'user_id': 'user1',
          'court_name': 'Quadra 1',
          'scheduled_at': '2026-04-28T14:00:00Z',
          'status': 'scheduled',
          'created_at': '2026-04-27T10:00:00Z',
          'updated_at': '2026-04-27T10:00:00Z',
          'version': 1,
        },
      ];

      when(mockApiService.get('/matches/me')).thenAnswer((_) async => {
            'matches': matchesData,
          });

      when(mockStorageService.saveJson(any, any)).thenAnswer((_) async => {});

      // Act
      await notifier.fetchMatches();

      // Assert
      expect(notifier.matches.length, 1);
      expect(notifier.matches.first.id, 'match1');
      expect(notifier.isLoading, false);
      verify(mockApiService.get('/matches/me')).called(1);
      verify(mockStorageService.saveJson('user_matches_cache', any)).called(1);
    });

    test('fetchMatches usa cache em caso de erro', () async {
      // Arrange
      final cachedData = {
        'matches': [
          {
            'id': 'cached1',
            'court_id': 'court1',
            'user_id': 'user1',
            'court_name': 'Quadra Cache',
            'scheduled_at': '2026-04-28T14:00:00Z',
            'status': 'scheduled',
            'created_at': '2026-04-27T10:00:00Z',
            'updated_at': '2026-04-27T10:00:00Z',
            'version': 1,
          },
        ],
        'fetchedAt': DateTime.now().toIso8601String(),
      };

      when(mockApiService.get('/matches/me')).thenThrow(Exception('API Error'));
      when(mockStorageService.loadJson('user_matches_cache'))
          .thenAnswer((_) async => cachedData);

      // Act
      await notifier.fetchMatches();

      // Assert
      expect(notifier.matches.length, 1);
      expect(notifier.matches.first.id, 'cached1');
      expect(notifier.errorMessage, 'Usando dados offline');
      verify(mockStorageService.loadJson('user_matches_cache')).called(1);
    });

    test('createMatch cria novo match com sucesso', () async {
      // Arrange
      final newMatchData = {
        'id': 'new1',
        'court_id': 'court1',
        'user_id': 'user1',
        'court_name': 'Quadra 1',
        'scheduled_at': '2026-04-28T14:00:00Z',
        'status': 'scheduled',
        'created_at': '2026-04-27T10:00:00Z',
        'updated_at': '2026-04-27T10:00:00Z',
        'version': 1,
      };

      when(mockApiService.post('/matches', data: anyNamed('data')))
          .thenAnswer((_) async => newMatchData);
      when(mockStorageService.saveJson(any, any)).thenAnswer((_) async => {});

      // Act
      final result = await notifier.createMatch(
        courtId: 'court1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime(2026, 4, 28, 14, 0),
      );

      // Assert
      expect(result, isNotNull);
      expect(result!.id, 'new1');
      expect(notifier.matches.length, 1);
      verify(mockApiService.post('/matches', data: anyNamed('data'))).called(1);
      verify(mockStorageService.saveJson('user_matches_cache', any)).called(1);
    });

    test('createMatch retorna null em caso de erro', () async {
      // Arrange
      when(mockApiService.post('/matches', data: anyNamed('data')))
          .thenThrow(Exception('API Error'));

      // Act
      final result = await notifier.createMatch(
        courtId: 'court1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime(2026, 4, 28, 14, 0),
      );

      // Assert
      expect(result, isNull);
      expect(notifier.errorMessage, 'Erro ao criar match');
    });

    test('cancelMatch cancela match com sucesso', () async {
      // Arrange
      

      // Adicionar match ao notifier via fetch
      final matchesData = [
        {
          'id': 'match1',
          'court_id': 'court1',
          'user_id': 'user1',
          'court_name': 'Quadra 1',
          'scheduled_at': '2026-04-28T14:00:00Z',
          'status': 'scheduled',
          'created_at': '2026-04-27T10:00:00Z',
          'updated_at': '2026-04-27T10:00:00Z',
          'version': 1,
        },
      ];

      when(mockApiService.get('/matches/me')).thenAnswer((_) async => {
            'matches': matchesData,
          });
      when(mockStorageService.saveJson(any, any)).thenAnswer((_) async => {});
      when(mockApiService.patch('/matches/match1', data: anyNamed('data')))
          .thenAnswer((_) async => {});

      await notifier.fetchMatches();

      // Act
      final result = await notifier.cancelMatch('match1');

      // Assert
      expect(result, true);
      expect(notifier.matches.first.status, MatchStatus.cancelled);
      verify(mockApiService.patch('/matches/match1', data: anyNamed('data')))
          .called(1);
    });

    test('cancelMatch retorna false em caso de erro', () async {
      // Arrange
      when(mockApiService.patch('/matches/match1', data: anyNamed('data')))
          .thenThrow(Exception('API Error'));

      // Act
      final result = await notifier.cancelMatch('match1');

      // Assert
      expect(result, false);
      expect(notifier.errorMessage, 'Erro ao cancelar match');
    });

    test('clearCache limpa cache local', () async {
      // Arrange
      when(mockStorageService.delete('user_matches_cache'))
          .thenAnswer((_) async => {});

      // Act
      await notifier.clearCache();

      // Assert
      verify(mockStorageService.delete('user_matches_cache')).called(1);
    });

    test('refresh limpa cache e busca matches novamente', () async {
      // Arrange
      final matchesData = [
        {
          'id': 'match1',
          'court_id': 'court1',
          'user_id': 'user1',
          'court_name': 'Quadra 1',
          'scheduled_at': '2026-04-28T14:00:00Z',
          'status': 'scheduled',
          'created_at': '2026-04-27T10:00:00Z',
          'updated_at': '2026-04-27T10:00:00Z',
          'version': 1,
        },
      ];

      when(mockStorageService.delete('user_matches_cache'))
          .thenAnswer((_) async => {});
      when(mockApiService.get('/matches/me')).thenAnswer((_) async => {
            'matches': matchesData,
          });
      when(mockStorageService.saveJson(any, any)).thenAnswer((_) async => {});

      // Act
      await notifier.refresh();

      // Assert
      verify(mockStorageService.delete('user_matches_cache')).called(1);
      verify(mockApiService.get('/matches/me')).called(1);
    });
  });
}
