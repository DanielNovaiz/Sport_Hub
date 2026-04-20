import 'package:flutter_test/flutter_test.dart';

import 'package:matching_esportivo_mobile/models/club_summary.dart';
import 'package:matching_esportivo_mobile/models/feed_event.dart';

void main() {
  group('FeedEvent contract resilience', () {
    test('parses snake_case payload', () {
      final event = FeedEvent.fromJson({
        'id': 'evt-1',
        'creator_id': 'u-1',
        'club_id': 'club-1',
        'title': 'Basquete 3x3',
        'sport_type': 'basquete',
        'scheduled_time': '2026-04-17T19:30:00Z',
        'status': 'open',
        'max_participants': 12,
        'distance_km': 4.2,
        'club_priority': true,
        'confirmed_participants': 7,
        'remaining_spots': 5,
      });

      expect(event.id, 'evt-1');
      expect(event.creatorId, 'u-1');
      expect(event.clubId, 'club-1');
      expect(event.sportType, 'basquete');
      expect(event.distanceKm, 4.2);
      expect(event.clubPriority, isTrue);
      expect(event.confirmedParticipants, 7);
      expect(event.remainingSpots, 5);
    });

    test('parses camelCase payload', () {
      final event = FeedEvent.fromJson({
        'id': 'evt-2',
        'creatorId': 'u-2',
        'clubId': 'club-2',
        'title': 'Futebol society',
        'sportType': 'futebol',
        'scheduledTime': '2026-04-18T21:00:00Z',
        'status': 'open',
        'maxParticipants': 10,
        'distanceKm': 2.8,
        'clubPriority': false,
        'confirmedParticipants': 3,
        'remainingSpots': 7,
      });

      expect(event.id, 'evt-2');
      expect(event.creatorId, 'u-2');
      expect(event.clubId, 'club-2');
      expect(event.sportType, 'futebol');
      expect(event.distanceKm, 2.8);
      expect(event.clubPriority, isFalse);
      expect(event.confirmedParticipants, 3);
      expect(event.remainingSpots, 7);
    });

    test('parses variable row shape [event, distance, priority, confirmed]', () {
      final event = FeedEvent.fromDynamic([
        {
          'id': 'evt-3',
          'creator_id': 'u-3',
          'title': 'Feed row fallback',
          'sport_type': 'basquete',
          'scheduled_time': '2026-04-18T17:00:00Z',
          'max_participants': 10,
          'status': 'open',
        },
        6.1,
        true,
        8,
      ]);

      expect(event.id, 'evt-3');
      expect(event.distanceKm, 6.1);
      expect(event.clubPriority, isTrue);
      expect(event.confirmedParticipants, 8);
      expect(event.remainingSpots, 2);
    });
  });

  group('ClubSummary contract resilience', () {
    test('parses snake_case payload including active_members', () {
      final club = ClubSummary.fromJson({
        'id': 'club-1',
        'name': 'Arena Sunset',
        'description': 'Treino competitivo',
        'owner_id': 'owner-1',
        'sport_type': 'futevolei',
        'privacy_type': 'private',
        'created_at': '2026-04-17T10:00:00Z',
        'active_members': 34,
      });

      expect(club.id, 'club-1');
      expect(club.ownerId, 'owner-1');
      expect(club.sportType, 'futevolei');
      expect(club.privacyType, 'private');
      expect(club.activeMembers, 34);
      expect(club.isPrivate, isTrue);
    });

    test('parses camelCase payload including activeMembers', () {
      final club = ClubSummary.fromJson({
        'id': 'club-2',
        'name': 'Clube Goiânia',
        'description': 'Partidas noturnas',
        'ownerId': 'owner-2',
        'sportType': 'basquete',
        'privacyType': 'public',
        'createdAt': '2026-04-17T11:00:00Z',
        'activeMembers': 12,
      });

      expect(club.id, 'club-2');
      expect(club.ownerId, 'owner-2');
      expect(club.sportType, 'basquete');
      expect(club.privacyType, 'public');
      expect(club.activeMembers, 12);
      expect(club.isPrivate, isFalse);
    });

    test('parses envelope payload {data: ...}', () {
      final club = ClubSummary.fromDynamic({
        'status': 'success',
        'data': {
          'id': 'club-3',
          'name': 'Envelope Club',
          'owner_id': 'owner-3',
          'sport_type': 'futebol',
          'privacy_type': 'public',
          'created_at': '2026-04-17T12:00:00Z',
          'active_members': 7,
        },
      });

      expect(club.id, 'club-3');
      expect(club.activeMembers, 7);
    });
  });
}
