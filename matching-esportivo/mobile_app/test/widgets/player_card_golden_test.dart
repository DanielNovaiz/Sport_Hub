import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:matching_esportivo_mobile/models/achievement_badge.dart';
import 'package:matching_esportivo_mobile/models/player_stats.dart';
import 'package:matching_esportivo_mobile/models/user_rank.dart';
import 'package:matching_esportivo_mobile/widgets/player_card.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final now = DateTime.utc(2026, 4, 17);

  PlayerStats footballStats() {
    return PlayerStats(
      id: 'stats-football-elite',
      userId: 'user-football-elite',
      position: 'atacante',
      pace: 92,
      shooting: 96,
      passing: 91,
      defense: 80,
      physical: 89,
      technique: 95,
      shootLong: 90,
      shootMid: 94,
      shootShort: 97,
      finishing: 98,
      velocity: 93,
      jump: 87,
      agility: 94,
      energy: 90,
      strength: 86,
      balance: 88,
      ballControl: 95,
      vision: 92,
      dribble: 96,
      steal: 72,
      block: 65,
      perimDef: 74,
      postDef: 70,
      rebound: 78,
      rebPredict: 80,
      combativeness: 84,
      overall: 95,
      playstyleArchetype: 'Elite Finisher',
      createdAt: now,
      updatedAt: now,
    );
  }

  PlayerStats basketballStats() {
    return PlayerStats(
      id: 'stats-basketball-elite',
      userId: 'user-basketball-elite',
      position: 'armador',
      pace: 93,
      shooting: 94,
      passing: 97,
      defense: 88,
      physical: 90,
      technique: 96,
      shootLong: 95,
      shootMid: 92,
      shootShort: 91,
      finishing: 93,
      velocity: 94,
      jump: 89,
      agility: 96,
      energy: 92,
      strength: 84,
      balance: 90,
      ballControl: 97,
      vision: 96,
      dribble: 98,
      steal: 90,
      block: 82,
      perimDef: 91,
      postDef: 84,
      rebound: 88,
      rebPredict: 89,
      combativeness: 92,
      overall: 96,
      playstyleArchetype: 'Two-way Playmaker',
      createdAt: now,
      updatedAt: now,
    );
  }

  UserRank eliteRank(String userId, {required String division}) {
    return UserRank(
      id: 'rank-$userId',
      userId: userId,
      mmr: 2150,
      division: division,
      league: 'I',
      wins: 42,
      losses: 8,
      winRate: 84,
      achievements: const [
        AchievementBadge(
          code: 'legend_streak',
          title: 'Lenda da Temporada',
          description: 'Sequência de vitórias com performance elite.',
          icon: 'military_tech_rounded',
          rarity: 'common',
          progress: 10,
          target: 10,
        ),
      ],
      createdAt: DateTime.utc(2026, 1, 1),
      updatedAt: DateTime.utc(2026, 4, 17),
    );
  }

  Widget host(Widget child) {
    return MaterialApp(
      home: Scaffold(
        backgroundColor: const Color(0xFF0F1118),
        body: Center(
          child: SizedBox(width: 360, child: child),
        ),
      ),
    );
  }

  testWidgets('PlayerCard golden - futebol elite', (tester) async {
    await tester.binding.setSurfaceSize(const Size(420, 840));
    await tester.pumpWidget(
      host(
        PlayerCard(
          stats: footballStats(),
          rank: eliteRank('user-football-elite', division: 'diamond'),
          sportType: 'FOOTBALL',
          xpProgress: 0.93,
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 50));

    await expectLater(
      find.byType(PlayerCard),
      matchesGoldenFile('goldens/player_card.png'),
    );

    await tester.binding.setSurfaceSize(null);
  });

  testWidgets('PlayerCard golden - basquete elite', (tester) async {
    await tester.binding.setSurfaceSize(const Size(420, 840));
    await tester.pumpWidget(
      host(
        PlayerCard(
          stats: basketballStats(),
          rank: eliteRank('user-basketball-elite', division: 'immortal'),
          sportType: 'BASKETBALL',
          xpProgress: 0.97,
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 50));

    await expectLater(
      find.byType(PlayerCard),
      matchesGoldenFile('goldens/player_card_basketball.png'),
    );

    await tester.binding.setSurfaceSize(null);
  });
}
