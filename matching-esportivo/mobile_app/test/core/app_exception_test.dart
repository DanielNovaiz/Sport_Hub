import 'package:flutter_test/flutter_test.dart';
import 'package:matching_esportivo_mobile/core/app_exception.dart';

void main() {
  group('AppException', () {
    test('cria exception com mensagem customizada', () {
      final exception = AppException('Erro customizado');
      expect(exception.message, 'Erro customizado');
    });

    test('cria exception com debugMessage', () {
      final exception = AppException(
        'Erro ao usuário',
        debugMessage: 'Erro técnico detalhado',
      );
      expect(exception.message, 'Erro ao usuário');
      expect(exception.debugMessage, 'Erro técnico detalhado');
    });

    test('toString retorna mensagem formatada', () {
      final exception = AppException('Erro de teste');
      final str = exception.toString();
      expect(str, contains('Erro de teste'));
    });

    test('ApiException herda de AppException', () {
      final exception = ApiException('Erro de API');
      expect(exception, isA<AppException>());
      expect(exception.message, 'Erro de API');
    });

    test('ApiException com DioException details', () {
      final exception = ApiException(
        'Erro de conexão',
        debugMessage: 'Connection timeout',
      );
      expect(exception.message, 'Erro de conexão');
      expect(exception.debugMessage, 'Connection timeout');
    });
  });
}
