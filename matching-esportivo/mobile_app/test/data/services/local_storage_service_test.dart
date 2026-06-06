import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:matching_esportivo_mobile/data/services/local_storage_service.dart';

void main() {
  late LocalStorageService service;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    service = LocalStorageService(prefs);
  });

  group('LocalStorageService', () {
    test('saveString e loadString funcionam', () async {
      await service.saveString('test_key', 'test_value');
      final result = await service.loadString('test_key');
      expect(result, 'test_value');
    });

    test('loadString retorna null para chave inexistente', () async {
      final result = await service.loadString('non_existent_key');
      expect(result, isNull);
    });

    test('delete remove chave', () async {
      await service.saveString('test_key', 'test_value');
      await service.delete('test_key');
      final result = await service.loadString('test_key');
      expect(result, isNull);
    });

    test('saveJson e loadJson funcionam', () async {
      final json = {'name': 'Test', 'age': 25, 'email': 'test@test.com'};
      await service.saveJson('user', json);
      final result = await service.loadJson('user');
      expect(result, json);
    });

    test('loadJson retorna null para chave inexistente', () async {
      final result = await service.loadJson('non_existent_key');
      expect(result, isNull);
    });

    test('saveInt e loadInt funcionam', () async {
      await service.saveInt('count', 42);
      final result = await service.loadInt('count');
      expect(result, 42);
    });

    test('saveBool e loadBool funcionam', () async {
      await service.saveBool('is_logged_in', true);
      final result = await service.loadBool('is_logged_in');
      expect(result, true);
    });

    test('clear remove todas as chaves', () async {
      await service.saveString('key1', 'value1');
      await service.saveString('key2', 'value2');
      await service.clear();
      expect(await service.loadString('key1'), isNull);
      expect(await service.loadString('key2'), isNull);
    });

    test('hasKey retorna true para chave existente', () async {
      await service.saveString('test_key', 'test_value');
      final result = await service.hasKey('test_key');
      expect(result, true);
    });

    test('hasKey retorna false para chave inexistente', () async {
      final result = await service.hasKey('non_existent_key');
      expect(result, false);
    });
  });
}
