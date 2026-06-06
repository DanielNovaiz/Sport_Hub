import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:matching_esportivo_mobile/models/player_stats.dart';
import 'package:matching_esportivo_mobile/widgets/player_card.dart';

void main() {
  test('statValueColor uses green/yellow/red thresholds', () {
    expect(statValueColor(85), const Color(0xFF4ADE80));
    expect(statValueColor(72), const Color(0xFFFACC15));
    expect(statValueColor(59), const Color(0xFFEF4444));
  });

  testWidgets('PlayerCard radar uses five user attributes', (tester) async {
    final stats = PlayerStats(
      id: 'stats-1',
      userId: 'user-1',
      position: 'meia',
      pace: 81,
      shooting: 77,
      passing: 84,
      defense: 58,
      physical: 65,
      technique: 70,
      shootLong: 50,
      shootMid: 50,
      shootShort: 50,
      finishing: 50,
      velocity: 50,
      jump: 50,
      agility: 50,
      energy: 50,
      strength: 50,
      balance: 50,
      ballControl: 50,
      vision: 50,
      dribble: 50,
      steal: 50,
      block: 50,
      perimDef: 50,
      postDef: 50,
      rebound: 50,
      rebPredict: 50,
      combativeness: 50,
      overall: 75,
      playstyleArchetype: 'Playmaker',
      createdAt: DateTime(2026),
      updatedAt: DateTime(2026),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PlayerCard(
            stats: stats,
            rank: null,
            sportType: 'FOOTBALL',
            xpProgress: 0.5,
          ),
        ),
      ),
    );

    expect(find.text('Passe'), findsOneWidget);
    expect(find.text('Chute'), findsOneWidget);
    expect(find.text('Defesa'), findsOneWidget);
    expect(find.text('Físico'), findsOneWidget);
    expect(find.text('Ritmo'), findsOneWidget);
  });
}
