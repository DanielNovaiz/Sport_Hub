import 'package:flutter/material.dart';
import '../data/services/location_service.dart';
import '../core/app_colors.dart';

/// BottomSheet educativo quando o GPS está desligado
class GPSDisabledBottomSheet extends StatelessWidget {
  final VoidCallback? onLocationSettingsTapped;

  const GPSDisabledBottomSheet({
    Key? key,
    this.onLocationSettingsTapped,
  }) : super(key: key);

  static Future<void> show(
    BuildContext context, {
    VoidCallback? onLocationSettingsTapped,
  }) {
    return showModalBottomSheet(
      context: context,
      builder: (_) => GPSDisabledBottomSheet(
        onLocationSettingsTapped: onLocationSettingsTapped,
      ),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header
          Container(
            width: 48,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.onSurfaceVariant,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          const SizedBox(height: 24),

          // Icon
          Icon(
            Icons.location_off,
            size: 64,
            color: AppColors.primaryNeon,
          ),
          const SizedBox(height: 24),

          // Title
          const Text(
            'GPS Desligado',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 12),

          // Description
          Text(
            'Para encontrar quadras próximas a você, ative o serviço de localização.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.onSurfaceVariant,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 24),

          // Steps
          _buildStep(
            icon: Icons.settings,
            title: '1. Acesse Configurações',
            description: 'Abra as configurações do seu dispositivo',
          ),
          const SizedBox(height: 16),
          _buildStep(
            icon: Icons.location_on,
            title: '2. Localização',
            description: 'Navegue até "Localização" ou "Privacidade"',
          ),
          const SizedBox(height: 16),
          _buildStep(
            icon: Icons.power_settings_new,
            title: '3. Ative o GPS',
            description: 'Ligue o serviço de localização',
          ),
          const SizedBox(height: 24),

          // Action buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    side: const BorderSide(color: AppColors.primaryNeon),
                  ),
                  child: const Text('Tentar Depois'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () async {
                    await LocationService.openLocationSettings();
                    if (context.mounted) {
                      Navigator.pop(context);
                      onLocationSettingsTapped?.call();
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    backgroundColor: AppColors.primaryNeon,
                  ),
                  child: const Text(
                    'Abrir Configurações',
                    style: TextStyle(color: Colors.black),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Info box
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.surfaceContainer,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.primaryNeon, width: 1),
            ),
            child: const Text(
              '💡 Dica: Você ainda pode usar o app com localização aproximada (Novo Mundo)',
              style: TextStyle(
                fontSize: 12,
                color: AppColors.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep({
    required IconData icon,
    required String title,
    required String description,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: AppColors.surfaceContainer,
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: AppColors.primaryNeon, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                description,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// BottomSheet para permissão de localização negada
class LocationPermissionDeniedBottomSheet extends StatelessWidget {
  final VoidCallback? onRetry;

  const LocationPermissionDeniedBottomSheet({
    Key? key,
    this.onRetry,
  }) : super(key: key);

  static Future<void> show(
    BuildContext context, {
    VoidCallback? onRetry,
  }) {
    return showModalBottomSheet(
      context: context,
      builder: (_) => LocationPermissionDeniedBottomSheet(
        onRetry: onRetry,
      ),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.location_off,
            size: 64,
            color: Colors.orange,
          ),
          const SizedBox(height: 24),
          const Text(
            'Permissão de Localização',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Precisamos acessar sua localização para encontrar as melhores quadras perto de você.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.onSurfaceVariant,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              onRetry?.call();
            },
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(double.infinity, 48),
              backgroundColor: AppColors.primaryNeon,
            ),
            child: const Text(
              'Permitir Localização',
              style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () => Navigator.pop(context),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(double.infinity, 48),
              side: const BorderSide(color: AppColors.primaryNeon),
            ),
            child: const Text('Usar Localização Padrão'),
          ),
        ],
      ),
    );
  }
}

/// BottomSheet para permissão de localização negada para sempre
class LocationPermissionPermanentlyDeniedBottomSheet extends StatelessWidget {
  final VoidCallback? onOpenSettings;

  const LocationPermissionPermanentlyDeniedBottomSheet({
    Key? key,
    this.onOpenSettings,
  }) : super(key: key);

  static Future<void> show(
    BuildContext context, {
    VoidCallback? onOpenSettings,
  }) {
    return showModalBottomSheet(
      context: context,
      builder: (_) => LocationPermissionPermanentlyDeniedBottomSheet(
        onOpenSettings: onOpenSettings,
      ),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.only(
        left: 24,
        right: 24,
        top: 24,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.lock,
            size: 64,
            color: Colors.red,
          ),
          const SizedBox(height: 24),
          const Text(
            'Permissão Permanentemente Negada',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Você negou permanentemente a permissão de localização. Abra as Configurações do app para permitir.',
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 14,
              color: AppColors.onSurfaceVariant,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: () async {
              await LocationService.openAppSettings();
              if (context.mounted) {
                Navigator.pop(context);
                onOpenSettings?.call();
              }
            },
            style: ElevatedButton.styleFrom(
              minimumSize: const Size(double.infinity, 48),
              backgroundColor: AppColors.primaryNeon,
            ),
            child: const Text(
              'Abrir Configurações',
              style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: () => Navigator.pop(context),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(double.infinity, 48),
              side: const BorderSide(color: AppColors.primaryNeon),
            ),
            child: const Text('Usar Localização Padrão'),
          ),
        ],
      ),
    );
  }
}
