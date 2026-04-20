import 'package:geolocator/geolocator.dart';
import 'package:flutter/material.dart';

/// Representa o resultado do pedido de localização
enum LocationStatus {
  success,              // Localização obtida com sucesso
  serviceDisabled,      // Serviço de GPS desligado
  permissionDenied,     // Usuário negou permissão (pode permitir depois)
  permissionDeniedForever, // Usuário negou permanentemente (vai pra settings)
  timeout,              // Timeout na obtenção da localização
  unknownError,         // Erro desconhecido
}

/// Resultado detalhado da obtenção de localização
class LocationResult {
  final LocationStatus status;
  final double? latitude;
  final double? longitude;
  final String? errorMessage;
  final DateTime? timestamp;

  /// Indica se a localização foi obtida com sucesso
  bool get isSuccess => status == LocationStatus.success;

  /// Indica se é um erro recuperável (usuário pode tentar novamente)
  bool get isRecoverable => status == LocationStatus.serviceDisabled ||
      status == LocationStatus.permissionDenied ||
      status == LocationStatus.timeout;

  /// Indica se é um erro permanente (precisa ir para settings)
  bool get isPermanent => status == LocationStatus.permissionDeniedForever;

  LocationResult({
    required this.status,
    this.latitude,
    this.longitude,
    this.errorMessage,
    this.timestamp,
  });

  @override
  String toString() =>
      'LocationResult(status: $status, lat: $latitude, lng: $longitude, error: $errorMessage)';
}

/// Serviço robusto de localização GPS com tratamento completo de permissões e estados
class LocationService {
  static const String _defaultLatitude = '-15.7942'; // Novo Mundo, Goiânia
  static const String _defaultLongitude = '-48.0676';

  /// Trata toda a lógica de obtenção de localização com fallback
  /// Retorna resultado detalhado para o notifier decidir como proceder
  static Future<LocationResult> getLocationWithFallback({
    Duration timeout = const Duration(seconds: 10),
  }) async {
    try {
      // 1. Verifica se o serviço de GPS está ativado
      final serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return LocationResult(
          status: LocationStatus.serviceDisabled,
          errorMessage: 'Serviço de localização desativado',
          latitude: double.parse(_defaultLatitude),
          longitude: double.parse(_defaultLongitude),
        );
      }

      // 2. Verifica permissão atual
      LocationPermission permission = await Geolocator.checkPermission();

      // 3. Se negada, solicita
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();

        // Se usuário clicou "Not now"
        if (permission == LocationPermission.denied) {
          return LocationResult(
            status: LocationStatus.permissionDenied,
            errorMessage:
                'Permissão de localização negada. Você pode permitir depois.',
            latitude: double.parse(_defaultLatitude),
            longitude: double.parse(_defaultLongitude),
          );
        }
      }

      // 4. Se negada para sempre
      if (permission == LocationPermission.deniedForever) {
        return LocationResult(
          status: LocationStatus.permissionDeniedForever,
          errorMessage:
              'Permissão de localização negada permanentemente. Abra as Configurações.',
          latitude: double.parse(_defaultLatitude),
          longitude: double.parse(_defaultLongitude),
        );
      }

      // 5. Tenta obter a posição com timeout
      try {
        final position = await Geolocator.getCurrentPosition(
          timeLimit: timeout,
          locationSettings: const LocationSettings(
            accuracy: LocationAccuracy.best,
            distanceFilter: 10, // Atualiza a cada 10 metros
          ),
        );

        return LocationResult(
          status: LocationStatus.success,
          latitude: position.latitude,
          longitude: position.longitude,
          timestamp: DateTime.now(),
        );
      } on TimeoutException {
        // Se timeout, usa fallback
        return LocationResult(
          status: LocationStatus.timeout,
          errorMessage:
              'Timeout ao obter localização. Usando fallback (Novo Mundo).',
          latitude: double.parse(_defaultLatitude),
          longitude: double.parse(_defaultLongitude),
        );
      }
    } catch (e) {
      // Erro desconhecido
      return LocationResult(
        status: LocationStatus.unknownError,
        errorMessage: 'Erro ao obter localização: $e',
        latitude: double.parse(_defaultLatitude),
        longitude: double.parse(_defaultLongitude),
      );
    }
  }

  /// Stream de posição contínua para GPS em background
  /// Importante: DEVE ser cancelado quando app vai para background
  static Stream<Position> getPositionStream({
    LocationAccuracy accuracy = LocationAccuracy.best,
    int distanceFilter = 10, // Atualiza a cada 10 metros
  }) {
    return Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: accuracy,
        distanceFilter: distanceFilter,
      ),
    );
  }

  /// Para de escutar atualizações de posição (economiza bateria)
  static Future<void> stopListening() async {
    // O Geolocator não tem método explícito de stop
    // Cancelar a subscription é responsabilidade do consumer
  }

  /// Abre as configurações de localização do dispositivo
  static Future<void> openLocationSettings() async {
    await Geolocator.openLocationSettings();
  }

  /// Abre as configurações de App do dispositivo
  static Future<void> openAppSettings() async {
    await Geolocator.openAppSettings();
  }
}
