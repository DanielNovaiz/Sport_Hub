import 'package:permission_handler/permission_handler.dart';
import 'package:flutter/material.dart';

/// Status de permissão de mídia
enum MediaPermissionStatus {
  granted,              // Permissão concedida
  denied,               // Negada (pode solicitar novamente)
  deniedForever,        // Negada permanentemente
  restricted,           // Restringida (iOS)
  provisional,          // Provisional (iOS 14+)
  limited,              // Limited photos/videos (iOS 14+)
}

/// Converte PermissionStatus do permission_handler para MediaPermissionStatus
MediaPermissionStatus _convertStatus(PermissionStatus status) {
  switch (status) {
    case PermissionStatus.granted:
      return MediaPermissionStatus.granted;
    case PermissionStatus.denied:
      return MediaPermissionStatus.denied;
    case PermissionStatus.deniedForever:
      return MediaPermissionStatus.deniedForever;
    case PermissionStatus.restricted:
      return MediaPermissionStatus.restricted;
    case PermissionStatus.provisional:
      return MediaPermissionStatus.provisional;
    case PermissionStatus.limited:
      return MediaPermissionStatus.limited;
  }
}

/// Resultado detalhado da solicitação de permissão de mídia
class MediaPermissionResult {
  final MediaPermissionStatus status;
  final String? errorMessage;
  final bool isGranted;

  MediaPermissionResult({
    required this.status,
    this.errorMessage,
    required this.isGranted,
  });

  @override
  String toString() => 'MediaPermissionResult(status: $status, granted: $isGranted)';
}

/// Serviço robusto de permissões de mídia (Galeria, Câmera, Áudio)
/// Implementa as diretrizes da Play Store (Google) e App Store (Apple)
class MediaPermissionService {
  /// Solicita permissão para acessar a galeria de fotos
  static Future<MediaPermissionResult> requestGalleryPermission({
    String? rationale,
  }) async {
    try {
      final status = await Permission.photos.request();

      return MediaPermissionResult(
        status: _convertStatus(status),
        isGranted: status.isGranted,
        errorMessage: _getErrorMessage(status, 'Galeria'),
      );
    } catch (e) {
      return MediaPermissionResult(
        status: MediaPermissionStatus.denied,
        isGranted: false,
        errorMessage: 'Erro ao solicitar permissão: $e',
      );
    }
  }

  /// Solicita permissão para usar a câmera
  static Future<MediaPermissionResult> requestCameraPermission({
    String? rationale,
  }) async {
    try {
      final status = await Permission.camera.request();

      return MediaPermissionResult(
        status: _convertStatus(status),
        isGranted: status.isGranted,
        errorMessage: _getErrorMessage(status, 'Câmera'),
      );
    } catch (e) {
      return MediaPermissionResult(
        status: MediaPermissionStatus.denied,
        isGranted: false,
        errorMessage: 'Erro ao solicitar permissão: $e',
      );
    }
  }

  /// Solicita permissão para usar o microfone
  static Future<MediaPermissionResult> requestMicrophonePermission({
    String? rationale,
  }) async {
    try {
      final status = await Permission.microphone.request();

      return MediaPermissionResult(
        status: _convertStatus(status),
        isGranted: status.isGranted,
        errorMessage: _getErrorMessage(status, 'Microfone'),
      );
    } catch (e) {
      return MediaPermissionResult(
        status: MediaPermissionStatus.denied,
        isGranted: false,
        errorMessage: 'Erro ao solicitar permissão: $e',
      );
    }
  }

  /// Solicita múltiplas permissões simultaneamente
  static Future<Map<String, MediaPermissionResult>> requestMultiple({
    bool camera = false,
    bool gallery = false,
    bool microphone = false,
  }) async {
    final permissions = <Permission>[];
    if (camera) permissions.add(Permission.camera);
    if (gallery) permissions.add(Permission.photos);
    if (microphone) permissions.add(Permission.microphone);

    if (permissions.isEmpty) {
      return {};
    }

    try {
      final statuses = await permissions.request();

      return {
        if (camera)
          'camera': MediaPermissionResult(
            status: _convertStatus(statuses[Permission.camera]!),
            isGranted: statuses[Permission.camera]!.isGranted,
            errorMessage: _getErrorMessage(statuses[Permission.camera]!, 'Câmera'),
          ),
        if (gallery)
          'gallery': MediaPermissionResult(
            status: _convertStatus(statuses[Permission.photos]!),
            isGranted: statuses[Permission.photos]!.isGranted,
            errorMessage: _getErrorMessage(statuses[Permission.photos]!, 'Galeria'),
          ),
        if (microphone)
          'microphone': MediaPermissionResult(
            status: _convertStatus(statuses[Permission.microphone]!),
            isGranted: statuses[Permission.microphone]!.isGranted,
            errorMessage: _getErrorMessage(statuses[Permission.microphone]!, 'Microfone'),
          ),
      };
    } catch (e) {
      return {
        if (camera)
          'camera': MediaPermissionResult(
            status: MediaPermissionStatus.denied,
            isGranted: false,
            errorMessage: 'Erro ao solicitar permissão: $e',
          ),
        if (gallery)
          'gallery': MediaPermissionResult(
            status: MediaPermissionStatus.denied,
            isGranted: false,
            errorMessage: 'Erro ao solicitar permissão: $e',
          ),
        if (microphone)
          'microphone': MediaPermissionResult(
            status: MediaPermissionStatus.denied,
            isGranted: false,
            errorMessage: 'Erro ao solicitar permissão: $e',
          ),
      };
    }
  }

  /// Verifica permissão sem solicitar
  static Future<MediaPermissionStatus> checkGalleryPermission() async {
    final status = await Permission.photos.status;
    return _convertStatus(status);
  }

  /// Verifica permissão sem solicitar
  static Future<MediaPermissionStatus> checkCameraPermission() async {
    final status = await Permission.camera.status;
    return _convertStatus(status);
  }

  /// Abre as configurações do app no dispositivo
  static Future<void> openAppSettings() async {
    openAppSettings();
  }

  /// Gera mensagem de erro apropriada baseada no status
  static String? _getErrorMessage(PermissionStatus status, String feature) {
    switch (status) {
      case PermissionStatus.denied:
        return '$feature: Permissão negada. Você pode permitir depois.';
      case PermissionStatus.deniedForever:
        return '$feature: Permissão negada permanentemente. Abra as Configurações.';
      case PermissionStatus.restricted:
        return '$feature: Restringido pelo administrador do dispositivo.';
      case PermissionStatus.limited:
        return '$feature: Acesso limitado a algumas fotos/vídeos.';
      case PermissionStatus.provisional:
        return '$feature: Acesso provisional (iOS 12+).';
      default:
        return null;
    }
  }
}
