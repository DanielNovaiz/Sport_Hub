import 'package:flutter_test/flutter_test.dart';
import 'package:matching_esportivo_mobile/data/models/auth_response.dart';

void main() {
  group('AuthResponse', () {
    test('cria AuthResponse com valores padrão', () {
      const authResponse = AuthResponse(
        accessToken: 'token123',
        refreshToken: 'refresh123',
        user: User(
          id: '1',
          email: 'test@test.com',
          name: 'Test User',
        ),
      );

      expect(authResponse.accessToken, 'token123');
      expect(authResponse.refreshToken, 'refresh123');
      expect(authResponse.user.id, '1');
      expect(authResponse.user.email, 'test@test.com');
      expect(authResponse.user.name, 'Test User');
    });

    test('User com avatarUrl opcional', () {
      const user = User(
        id: '1',
        email: 'test@test.com',
        name: 'Test User',
        avatarUrl: 'https://example.com/avatar.jpg',
      );

      expect(user.avatarUrl, 'https://example.com/avatar.jpg');
    });

    test('copyWith funciona corretamente', () {
      const user = User(
        id: '1',
        email: 'test@test.com',
        name: 'Test User',
      );

      final updatedUser = user.copyWith(name: 'Updated Name');

      expect(updatedUser.name, 'Updated Name');
      expect(updatedUser.email, 'test@test.com');
    });

    test('fromJson cria AuthResponse válido', () {
      final json = {
        'access_token': 'token123',
        'refresh_token': 'refresh123',
        'user': {
          'id': '1',
          'email': 'test@test.com',
          'name': 'Test User',
        },
      };

      final authResponse = AuthResponse.fromJson(json);

      expect(authResponse.accessToken, 'token123');
      expect(authResponse.refreshToken, 'refresh123');
      expect(authResponse.user.id, '1');
    });

    test('toJson serializa AuthResponse corretamente', () {
      const authResponse = AuthResponse(
        accessToken: 'token123',
        refreshToken: 'refresh123',
        user: User(
          id: '1',
          email: 'test@test.com',
          name: 'Test User',
        ),
      );

      final json = authResponse.toJson();

      expect(json['access_token'], 'token123');
      expect(json['refresh_token'], 'refresh123');
      expect(json['user']['id'], '1');
    });
  });
}
