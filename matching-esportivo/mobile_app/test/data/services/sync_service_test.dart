import 'package:flutter_test/flutter_test.dart';
import 'package:matching_esportivo_mobile/data/models/match.dart';
import 'package:matching_esportivo_mobile/data/services/sync_service.dart';

void main() {
  late SyncService syncService;

  setUp(() {
    syncService = SyncService();
  });

  group('SyncService', () {
    test('resolveConflict mantém local quando mais recente', () {
      // Arrange
      final local = Match(
        id: '1',
        courtId: 'court1',
        userId: 'user1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime.now(),
        status: MatchStatus.scheduled,
        updatedAt: DateTime(2024, 1, 2),
      );

      final remote = Match(
        id: '1',
        courtId: 'court1',
        userId: 'user1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime.now(),
        status: MatchStatus.scheduled,
        updatedAt: DateTime(2024, 1, 1),
      );

      // Act
      final result = syncService.resolveConflict<Match>(
        local: local,
        remote: remote,
        getTimestamp: (entry) => entry.updatedAt ?? DateTime(1970),
      );

      // Assert
      expect(result, local);
    });

    test('resolveConflict aceita remote quando mais recente', () {
      // Arrange
      final local = Match(
        id: '1',
        courtId: 'court1',
        userId: 'user1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime.now(),
        status: MatchStatus.scheduled,
        updatedAt: DateTime(2024, 1, 1),
      );

      final remote = Match(
        id: '1',
        courtId: 'court1',
        userId: 'user1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime.now(),
        status: MatchStatus.scheduled,
        updatedAt: DateTime(2024, 1, 2),
      );

      // Act
      final result = syncService.resolveConflict<Match>(
        local: local,
        remote: remote,
        getTimestamp: (entry) => entry.updatedAt ?? DateTime(1970),
      );

      // Assert
      expect(result, remote);
    });

    test('resolveConflict mantém local quando timestamps iguais', () {
      // Arrange
      final timestamp = DateTime(2024, 1, 1);
      final local = Match(
        id: '1',
        courtId: 'court1',
        userId: 'user1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime.now(),
        status: MatchStatus.scheduled,
        updatedAt: timestamp,
      );

      final remote = Match(
        id: '1',
        courtId: 'court1',
        userId: 'user1',
        courtName: 'Quadra 1',
        scheduledAt: DateTime.now(),
        status: MatchStatus.scheduled,
        updatedAt: timestamp,
      );

      // Act
      final result = syncService.resolveConflict<Match>(
        local: local,
        remote: remote,
        getTimestamp: (entry) => entry.updatedAt ?? DateTime(1970),
      );

      // Assert
      expect(result, local);
    });

    test('syncMatchEntries sincroniza múltiplas entradas', () async {
      // Arrange
      final localEntries = [
        Match(
          id: '1',
          courtId: 'court1',
          userId: 'user1',
          courtName: 'Quadra 1',
          scheduledAt: DateTime.now(),
          status: MatchStatus.scheduled,
          updatedAt: DateTime(2024, 1, 2),
        ),
      ];

      final remoteEntries = [
        Match(
          id: '1',
          courtId: 'court1',
          userId: 'user1',
          courtName: 'Quadra 1',
          scheduledAt: DateTime.now(),
          status: MatchStatus.scheduled,
          updatedAt: DateTime(2024, 1, 1),
        ),
      ];

      final savedEntries = <Match>[];

      // Act
      await syncService.syncMatchEntries(
        localEntries,
        remoteEntries,
        (entry) => savedEntries.add(entry),
      );

      // Assert
      expect(savedEntries.length, 1);
      expect(savedEntries.first, localEntries.first);
    });
  });
}
