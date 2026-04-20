import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('app smoke widget test', (WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text('Matching Esportivo'),
          ),
        ),
      ),
    );

    expect(find.text('Matching Esportivo'), findsOneWidget);
  });
}
