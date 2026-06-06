import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:matching_esportivo_mobile/screens/post_match_summary_screen.dart';

void main() {
  testWidgets('shows post-match xp summary and feedback lines', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: PostMatchSummaryScreen(
          sportType: 'Futebol',
          response: {
            'data': {
              'xp_gains': {
                'finishing': 15,
                'vision': 5,
              },
            },
          },
        ),
      ),
    );

    await tester.pump(const Duration(milliseconds: 1300));

    expect(find.text('Resumo pós-partida'), findsOneWidget);
    expect(find.text('+15 XP em Finalização'), findsOneWidget);
    expect(find.text('+5 XP em Visão'), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });
}
