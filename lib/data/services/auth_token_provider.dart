import 'package:shared_preferences/shared_preferences.dart';

abstract class AuthTokenProvider {
  Future<String?> getAccessToken();
}

class SharedPrefsAuthTokenProvider implements AuthTokenProvider {
  static const String accessTokenKey = 'auth_access_token';

  final SharedPreferences _prefs;

  SharedPrefsAuthTokenProvider(this._prefs);

  @override
  Future<String?> getAccessToken() async {
    return _prefs.getString(accessTokenKey);
  }

  Future<void> saveAccessToken(String token) async {
    await _prefs.setString(accessTokenKey, token);
  }

  Future<void> clearAccessToken() async {
    await _prefs.remove(accessTokenKey);
  }
}
