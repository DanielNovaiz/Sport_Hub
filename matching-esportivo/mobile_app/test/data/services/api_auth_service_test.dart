import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/annotations.dart';
import 'package:mockito/mockito.dart';
import 'package:matching_esportivo_mobile/data/services/api_auth_service.dart';
import 'package:matching_esportivo_mobile/data/services/local_storage_service.dart';

@GenerateMocks([Dio, LocalStorageService])
import 'api_auth_service_test.mocks.dart';

void main() {
  late ApiAuthService authService;
  late MockDio mockDio;
  late MockLocalStorageService mockStorage;

  setUp(() {
    mockDio = MockDio();
    mockStorage = MockLocalStorageService();
    authService = ApiAuthService(mockDio, mockStorage);
  });

  group('ApiAuthService', () {
    test('login salva tokens no storage', () async {
      // Arrange
      final responseData = {
        'access_token': 'token123',
        'refresh_token': 'refresh123',
        'user': {
          'id': '1',
          'email': 'test@test.com',
          'name': 'Test User',
        },
      };

      when(mockDio.post('/api/auth/login', data: anyNamed('data'))).thenAnswer(
        (_) async => Response(
          data: responseData,
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/auth/login'),
        ),
      );

      when(mockStorage.saveString(any, any)).thenAnswer((_) async {});
      when(mockStorage.saveJson(any, any)).thenAnswer((_) async {});

      // Act
      final result = await authService.login('test@test.com', 'senha123');

      // Assert
      expect(result.accessToken, 'token123');
      expect(result.refreshToken, 'refresh123');
      verify(mockStorage.saveString('auth_access_token', 'token123')).called(1);
      verify(mockStorage.saveString('auth_refresh_token', 'refresh123'))
          .called(1);
      verify(mockStorage.saveJson('auth_current_user', any)).called(1);
    });

    test('login lança exceção em erro de rede', () async {
      // Arrange
      when(mockDio.post('/api/auth/login', data: anyNamed('data'))).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: '/api/auth/login'),
          type: DioExceptionType.connectionTimeout,
        ),
      );

      // Act & Assert
      expect(
        () => authService.login('test@test.com', 'senha123'),
        throwsA(isA<Exception>()),
      );
    });

    test('logout limpa storage mesmo com erro de rede', () async {
      // Arrange
      when(mockStorage.loadString('auth_access_token'))
          .thenAnswer((_) async => 'token123');
      when(mockDio.post(
        '/api/auth/logout',
        options: anyNamed('options'),
      )).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: '/api/auth/logout'),
          type: DioExceptionType.connectionTimeout,
        ),
      );
      when(mockStorage.delete(any)).thenAnswer((_) async {});

      // Act
      await authService.logout();

      // Assert
      verify(mockStorage.delete('auth_access_token')).called(1);
      verify(mockStorage.delete('auth_refresh_token')).called(1);
      verify(mockStorage.delete('auth_current_user')).called(1);
    });

    test('refreshToken atualiza access token', () async {
      // Arrange
      when(mockDio.post('/api/auth/refresh', data: anyNamed('data')))
          .thenAnswer(
        (_) async => Response(
          data: {'access_token': 'new_token_456'},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/auth/refresh'),
        ),
      );
      when(mockStorage.saveString(any, any)).thenAnswer((_) async {});

      // Act
      final result = await authService.refreshToken('refresh123');

      // Assert
      expect(result, 'new_token_456');
      verify(mockStorage.saveString('auth_access_token', 'new_token_456'))
          .called(1);
    });

    test('getCurrentUser retorna usuário do storage', () async {
      // Arrange
      final userJson = {
        'id': '1',
        'email': 'test@test.com',
        'name': 'Test User',
      };
      when(mockStorage.loadJson('auth_current_user'))
          .thenAnswer((_) async => userJson);

      // Act
      final result = await authService.getCurrentUser();

      // Assert
      expect(result, isNotNull);
      expect(result!.email, 'test@test.com');
      expect(result.name, 'Test User');
    });

    test('getCurrentUser retorna null quando não há usuário', () async {
      // Arrange
      when(mockStorage.loadJson('auth_current_user'))
          .thenAnswer((_) async => null);

      // Act
      final result = await authService.getCurrentUser();

      // Assert
      expect(result, isNull);
    });
  });
}
