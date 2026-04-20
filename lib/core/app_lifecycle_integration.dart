import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/lifecycle_manager.dart';
import '../presentation/providers/court_list_notifier.dart';
import '../data/services/media_permission_service.dart';
import '../presentation/widgets/location_permission_sheets.dart';
import '../presentation/widgets/shimmer_skeletons.dart';

/// Widget que gerencia o ciclo de vida do app e dos sensores
/// Coloque no topo da sua árvore de widgets para controlar GPS globally
class AppLifecycleHandler extends StatefulWidget {
  final Widget child;

  const AppLifecycleHandler({
    Key? key,
    required this.child,
  }) : super(key: key);

  @override
  State<AppLifecycleHandler> createState() => _AppLifecycleHandlerState();
}

class _AppLifecycleHandlerState extends State<AppLifecycleHandler>
    with AppLifecycleAware<AppLifecycleHandler> {
  late AppLifecycleManager _lifecycleManager;

  @override
  void initState() {
    super.initState();
    _lifecycleManager = AppLifecycleManager();
    _lifecycleManager.addListener(_onLifecycleChange);
  }

  @override
  void dispose() {
    _lifecycleManager.removeListener(_onLifecycleChange);
    super.dispose();
  }

  /// Chamado quando o app é resumido (traz pra foreground)
  @override
  void onAppResumed() {
    print('🟢 App resumed - retomando sensores...');
    
    // Retoma GPS se estava escutando
    if (mounted && context.mounted) {
      context.read<CourtListNotifier>().startListeningToLocation();
    }
  }

  /// Chamado quando o app é pausado (vai para background)
  @override
  void onAppPaused() {
    print('⏸️ App paused - pausando sensores para economizar bateria...');
    
    // Para GPS para economizar bateria
    if (mounted && context.mounted) {
      context.read<CourtListNotifier>().stopListeningToLocation();
    }
  }

  /// Chamado quando o app é desanexado (encerrado)
  @override
  void onAppDetached() {
    print('🔴 App detached - limpando recursos...');
    
    // Limpa recursos
    if (mounted && context.mounted) {
      context.read<CourtListNotifier>().dispose();
    }
  }

  void _onLifecycleChange(AppLifecycleStateEnum state) {
    print('App lifecycle: $state');
    switch (state) {
      case AppLifecycleStateEnum.resumed:
        onAppResumed();
        break;
      case AppLifecycleStateEnum.paused:
        onAppPaused();
        break;
      case AppLifecycleStateEnum.detached:
        onAppDetached();
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}

/// Widget que consome CourtListNotifier e gerencia UI baseada em GPS status
class CourtListWithLocationHandling extends StatefulWidget {
  final bool autoStartGPS;

  const CourtListWithLocationHandling({
    Key? key,
    this.autoStartGPS = true,
  }) : super(key: key);

  @override
  State<CourtListWithLocationHandling> createState() =>
      _CourtListWithLocationHandlingState();
}

class _CourtListWithLocationHandlingState
    extends State<CourtListWithLocationHandling> {
  @override
  void initState() {
    super.initState();

    // Inicializa dados e sensores
    Future.microtask(() async {
      if (!mounted) return;
      final notifier = context.read<CourtListNotifier>();

      // Carrega quadras com localização
      final locationResult =
          await notifier.requestUserLocation();

      // Se GPS está desligado, mostra BottomSheet educativo
      if (locationResult.status == LocationStatus.serviceDisabled) {
        if (mounted) {
          _showGPSDisabledSheet();
        }
      } else if (locationResult.status ==
          LocationStatus.permissionDeniedForever) {
        if (mounted) {
          _showPermissionPermanentlyDeniedSheet();
        }
      } else if (locationResult.status == LocationStatus.permissionDenied) {
        if (mounted) {
          _showPermissionDeniedSheet();
        }
      }

      // Carrega quadras
      await notifier.fetchAvailableCourts(useUserLocation: true);

      // Inicia escuta contínua (parado no initState vai para background)
      if (widget.autoStartGPS && mounted) {
        await notifier.startListeningToLocation();
      }
    });
  }

  @override
  void dispose() {
    // Pausa GPS ao sair da página
    if (mounted && context.mounted) {
      context.read<CourtListNotifier>().stopListeningToLocation();
    }
    super.dispose();
  }

  void _showGPSDisabledSheet() {
    GPSDisabledBottomSheet.show(
      context,
      onLocationSettingsTapped: () async {
        if (!mounted) return;
        final notifier = context.read<CourtListNotifier>();
        await notifier.requestUserLocation();
        await notifier.fetchAvailableCourts(useUserLocation: true);
      },
    );
  }

  void _showPermissionDeniedSheet() {
    LocationPermissionDeniedBottomSheet.show(
      context,
      onRetry: () async {
        if (!mounted) return;
        final notifier = context.read<CourtListNotifier>();
        await notifier.requestUserLocation();
        await notifier.fetchAvailableCourts(useUserLocation: true);
      },
    );
  }

  void _showPermissionPermanentlyDeniedSheet() {
    LocationPermissionPermanentlyDeniedBottomSheet.show(
      context,
      onOpenSettings: () async {
        if (!mounted) return;
        final notifier = context.read<CourtListNotifier>();
        await notifier.requestUserLocation();
        await notifier.fetchAvailableCourts(useUserLocation: true);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CourtListNotifier>(
      builder: (context, notifier, child) {
        return Stack(
          children: [
            // Lista de quadras
            notifier.isLoading
                ? const SkeletonList(
                    itemCount: 8,
                    cacheExtent: 900,
                    itemBuilder: (_, __) => CourtCardShimmer(),
                  )
                : ListView.builder(
                    cacheExtent: 900,
                    itemCount: notifier.courts.length,
                    itemBuilder: (_, i) => CourtCard(
                      court: notifier.courts[i],
                    ),
                  ),

            // Indicador de status de GPS (fixo no topo)
            Positioned(
              top: 12,
              left: 12,
              child: _buildGPSStatusIndicator(notifier),
            ),
          ],
        );
      },
    );
  }

  Widget _buildGPSStatusIndicator(CourtListNotifier notifier) {
    Color statusColor;
    IconData statusIcon;
    String statusText;

    switch (notifier.gpsStatus) {
      case GPSSignalStatus.strong:
        statusColor = Colors.green;
        statusIcon = Icons.location_on;
        statusText = 'GPS Ativo';
        break;
      case GPSSignalStatus.weak:
        statusColor = Colors.orange;
        statusIcon = Icons.location_searching;
        statusText = 'Sinal Fraco';
        break;
      case GPSSignalStatus.lost:
        statusColor = Colors.red;
        statusIcon = Icons.location_off;
        statusText = 'Sinal Perdido';
        break;
      case GPSSignalStatus.disabled:
        statusColor = Colors.grey;
        statusIcon = Icons.location_disabled;
        statusText = 'GPS Desligado';
        break;
      case GPSSignalStatus.permissionDenied:
        statusColor = Colors.red;
        statusIcon = Icons.lock;
        statusText = 'Sem Permissão';
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: statusColor.withOpacity(0.9),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Icon(statusIcon, color: Colors.white, size: 16),
          const SizedBox(width: 8),
          Text(
            statusText,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

/// Card simples para exibir uma quadra (exemplo)
class CourtCard extends StatelessWidget {
  final Court;

  const CourtCard({
    Key? key,
    required this.Court,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(8),
      child: ListTile(
        title: Text(Court.name),
        subtitle: Text(Court.location),
        trailing: Text('${Court.availableSlots}/${Court.totalSlots}'),
      ),
    );
  }
}

/// Exemplo de uso no main.dart
/// 
/// void main() async {
///   await setupServiceLocator();
///   runApp(const MatchingEsportivoApp());
/// }
/// 
/// class MatchingEsportivoApp extends StatelessWidget {
///   @override
///   Widget build(BuildContext context) {
///     return MultiProvider(
///       providers: [
///         ChangeNotifierProvider(
///           create: (_) => CourtListNotifier(...),
///         ),
///       ],
///       child: MaterialApp(
///         home: AppLifecycleHandler(  // ← Wrapper para gerenciar lifecycle
///           child: MyHomePage(),
///         ),
///       ),
///     );
///   }
/// }

// Imports necessários (já existem)
import '../data/models/court.dart';
import '../data/services/location_service.dart';
