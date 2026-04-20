enum AppFlavor { dev, prod }

class AppEnvironment {
  static const String _flavorRaw = String.fromEnvironment(
    'APP_FLAVOR',
    defaultValue: 'dev',
  );

  static const String _devBaseUrl = String.fromEnvironment(
    'API_BASE_URL_DEV',
    defaultValue: 'https://api-dev.matching-esportivo.local/v1',
  );

  static const String _prodBaseUrl = String.fromEnvironment(
    'API_BASE_URL_PROD',
    defaultValue: 'https://api.matching-esportivo.com/v1',
  );

  static const bool enableDebugNetworkLogs = bool.fromEnvironment(
    'ENABLE_DEBUG_NETWORK_LOGS',
    defaultValue: true,
  );

  static const bool enableSslPinning = bool.fromEnvironment(
    'ENABLE_SSL_PINNING',
    defaultValue: false,
  );

  static AppFlavor get flavor {
    if (_flavorRaw.toLowerCase() == 'prod') {
      return AppFlavor.prod;
    }
    return AppFlavor.dev;
  }

  static String get apiBaseUrl =>
      flavor == AppFlavor.prod ? _prodBaseUrl : _devBaseUrl;

  static bool get isProduction => flavor == AppFlavor.prod;
}
