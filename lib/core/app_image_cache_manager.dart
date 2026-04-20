import 'package:flutter_cache_manager/flutter_cache_manager.dart';

/// Cache manager global para imagens de atletas e quadras.
///
/// Estratégia:
/// - validade: 7 dias
/// - volume máximo: 250 objetos
class AppImageCacheManager {
  static const key = 'matching_esportivo_image_cache_v1';

  static final CacheManager instance = CacheManager(
    Config(
      key,
      stalePeriod: const Duration(days: 7),
      maxNrOfCacheObjects: 250,
    ),
  );
}