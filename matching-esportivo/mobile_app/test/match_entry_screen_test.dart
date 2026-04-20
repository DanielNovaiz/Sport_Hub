import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:matching_esportivo_mobile/screens/match_entry_screen.dart';

void main() {
  const saveButtonKey = ValueKey('save-match-button');

  Widget buildApp(Widget child) {
    return MaterialApp(home: child);
  }

  testWidgets('renders football fields in a grid', (tester) async {
    await tester.pumpWidget(
      buildApp(
        const MatchEntryScreen(selectedSport: SelectedSport.football),
      ),
    );

    expect(find.text('Gols'), findsOneWidget);
    expect(find.text('Assist'), findsOneWidget);
    expect(find.text('Desarmes'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(3));
  });

  testWidgets('renders basketball fields in a grid', (tester) async {
    await tester.pumpWidget(
      buildApp(
        const MatchEntryScreen(selectedSport: SelectedSport.basketball),
      ),
    );

    expect(find.text('Pontos'), findsOneWidget);
    expect(find.text('Rebounds'), findsOneWidget);
    expect(find.text('Steals'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(3));
  });

  testWidgets('validates positive integers', (tester) async {
    Map<String, int>? submitted;

    await tester.pumpWidget(
      buildApp(
        MatchEntryScreen(
          selectedSport: SelectedSport.football,
          onSubmit: (values) async {
            submitted = values;
          },
        ),
      ),
    );

    await tester.enterText(find.byType(TextFormField).first, '0');
    await tester.ensureVisible(find.byKey(saveButtonKey));
    await tester.tap(find.byKey(saveButtonKey));
    await tester.pumpAndSettle();

    expect(find.text('Informe um número inteiro positivo.'), findsNWidgets(3));
    expect(submitted, isNull);

    await tester.pumpWidget(
      buildApp(
        MatchEntryScreen(
          selectedSport: SelectedSport.football,
          onSubmit: (values) async {
            submitted = values;
          },
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextFormField).first, '2');
    await tester.enterText(find.byType(TextFormField).at(1), '1');
    await tester.enterText(find.byType(TextFormField).at(2), '3');
    await tester.ensureVisible(find.byKey(saveButtonKey));
    await tester.tap(find.byKey(saveButtonKey));
    await tester.pumpAndSettle();

    expect(submitted, isNotNull);
    expect(submitted!['goals'], 2);
    expect(submitted!['assists'], 1);
    expect(submitted!['tackles'], 3);
  });
}
