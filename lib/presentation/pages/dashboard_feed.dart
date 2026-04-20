import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:provider/provider.dart';
import '../../core/app_colors.dart';
import '../../core/app_image_cache_manager.dart';
import '../providers/court_list_notifier.dart';
import '../widgets/shimmer_skeletons.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  @override
  void initState() {
    super.initState();
    // Carrega as quadras disponíveis quando a página é criada
    Future.microtask(() {
      context.read<CourtListNotifier>().fetchAvailableCourts();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface.withOpacity(0.6),
        elevation: 0,
        title: const Text(
          'MATCHING ESPORTIVO',
          style: TextStyle(
            color: AppColors.primaryNeon,
            fontWeight: FontWeight.bold,
            letterSpacing: -1,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined, color: AppColors.primaryNeon),
            onPressed: () {},
          ),
          // Botão de refresh
          Consumer<CourtListNotifier>(
            builder: (context, notifier, child) {
              return IconButton(
                icon: const Icon(Icons.refresh, color: AppColors.primaryNeon),
                onPressed: notifier.isLoading
                    ? null
                    : () => notifier.fetchAvailableCourts(forceRefresh: true),
              );
            },
          ),
        ],
      ),
      body: Consumer<CourtListNotifier>(
        builder: (context, notifier, child) {
          // Caso 1: Carregando dados
          if (notifier.isLoading) {
            return const SkeletonList(
              itemCount: 8,
              cacheExtent: 920,
              padding: EdgeInsets.all(24),
              itemBuilder: (_, __) => CourtCardShimmer(),
            );
          }

          // Caso 2: Erro ao carregar
          if (notifier.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error, color: Colors.red, size: 48),
                  const SizedBox(height: 16),
                  Text(
                    'Erro: ${notifier.errorMessage}',
                    style: const TextStyle(color: Colors.red),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () =>
                        notifier.fetchAvailableCourts(forceRefresh: true),
                    child: const Text('Tentar novamente'),
                  ),
                ],
              ),
            );
          }

          // Caso 3: Dados carregados com sucesso
          final courts = notifier.courts;

          if (courts.isEmpty) {
            return const Center(
              child: Text(
                'Nenhuma quadra disponível no momento',
                style: TextStyle(color: AppColors.onSurfaceVariant),
              ),
            );
          }

          return ListView.builder(
            cacheExtent: 920,
            padding: const EdgeInsets.all(24),
            itemCount: courts.length + 1,
            itemBuilder: (context, index) {
              if (index == 0) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'LIVE TELEMETRY',
                      style: TextStyle(
                        color: AppColors.onSurfaceVariant,
                        fontSize: 12,
                        letterSpacing: 2,
                      ),
                    ),
                    const Text(
                      'DASHBOARD FEED',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    // Indicador de cache
                    Row(
                      children: [
                        Icon(
                          notifier.isCacheValid ? Icons.cloud_done : Icons.cloud_off,
                          color: notifier.isCacheValid ? Colors.green : Colors.orange,
                          size: 14,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          notifier.isCacheValid ? 'Cache válido' : 'Cache expirado',
                          style: TextStyle(
                            fontSize: 11,
                            color: notifier.isCacheValid ? Colors.green : Colors.orange,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                  ],
                );
              }

              final court = courts[index - 1];
              return _buildCourtCard(
                courtId: court.id,
                title: court.name,
                location: court.location,
                level: '${(court.availableSlots * 20).toInt()}',
                vagas: '${court.availableSlots}/${court.totalSlots} Vagas',
                price: 'R\$ ${court.price.toStringAsFixed(2)}',
                sport: court.sport,
                icon: _getSportIcon(court.sport),
              );
            },
          );
        },
      ),
    );
  }

  /// Retorna o ícone apropriado para cada esporte
  IconData _getSportIcon(String sport) {
    switch (sport.toLowerCase()) {
      case 'futebol':
        return Icons.sports_soccer;
      case 'basquete':
      case 'basquete 3x3':
        return Icons.sports_basketball;
      case 'vôlei':
      case 'volei':
        return Icons.sports_volleyball;
      case 'tênis':
      case 'tenis':
        return Icons.sports_tennis;
      default:
        return Icons.sports_soccer;
    }
  }

  Widget _buildCourtCard({
    required String courtId,
    required String title,
    required String location,
    required String level,
    required String vagas,
    required String price,
    required String sport,
    required IconData icon,
  }) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: AppColors.surfaceContainer,
            borderRadius: BorderRadius.circular(4),
            border: const Border(
              left: BorderSide(color: AppColors.primaryNeon, width: 2),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.between,
                children: [
                  Row(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: CachedNetworkImage(
                          imageUrl: _courtImageUrl(courtId),
                          width: 48,
                          height: 48,
                          fit: BoxFit.cover,
                          cacheManager: AppImageCacheManager.instance,
                          fadeInDuration: const Duration(milliseconds: 120),
                          placeholder: (context, url) => Container(
                            width: 48,
                            height: 48,
                            color: AppColors.surfaceContainerHigh,
                          ),
                          errorWidget: (context, url, error) => Container(
                            width: 48,
                            height: 48,
                            color: AppColors.surfaceContainerHigh,
                            child: Icon(
                              icon,
                              color: AppColors.primaryNeon,
                              size: 24,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Icon(icon, color: AppColors.primaryNeon, size: 20),
                    ],
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        level,
                        style: const TextStyle(
                          color: AppColors.primaryNeon,
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Text(
                        'CAPACITY RATE',
                        style: TextStyle(
                          color: AppColors.onSurfaceVariant,
                          fontSize: 8,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                location,
                style: const TextStyle(
                  color: AppColors.onSurfaceVariant,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    vagas,
                    style: const TextStyle(
                      color: Colors.green,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    price,
                    style: const TextStyle(
                      color: AppColors.primaryNeon,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
                child: const Text('CONFIRMAR PRESENÇA'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  String _courtImageUrl(String courtId) {
    return 'https://picsum.photos/seed/dashboard_court_$courtId/320/220';
  }
}