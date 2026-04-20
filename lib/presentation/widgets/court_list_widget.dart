import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:provider/provider.dart';
import '../../presentation/providers/court_list_notifier.dart';
import '../../core/app_colors.dart';
import '../../core/app_image_cache_manager.dart';
import 'shimmer_skeletons.dart';

/// Exemplo de widget que consome estado do CourtListNotifier
/// Demonstra como usar o notifier com filtros e localização
class CourtListWidget extends StatefulWidget {
  final bool useLocation;

  const CourtListWidget({
    Key? key,
    this.useLocation = false,
  }) : super(key: key);

  @override
  State<CourtListWidget> createState() => _CourtListWidgetState();
}

class _CourtListWidgetState extends State<CourtListWidget> {
  @override
  void initState() {
    super.initState();
    // Carrega quadras quando o widget é criado
    Future.microtask(() {
      context.read<CourtListNotifier>().fetchAvailableCourts(
            useUserLocation: widget.useLocation,
          );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CourtListNotifier>(
      builder: (context, notifier, child) {
        // Caso 1: Carregando dados
        if (notifier.isLoading) {
          return const SkeletonList(
            itemCount: 8,
            cacheExtent: 840,
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
                  notifier.errorMessage,
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
            child: Text('Nenhuma quadra disponível'),
          );
        }

        return ListView.builder(
          cacheExtent: 840,
          itemCount: courts.length,
          itemBuilder: (context, index) {
            final court = courts[index];
            return Card(
              margin: const EdgeInsets.all(8),
              color: AppColors.surface,
              child: ListTile(
                leading: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: CachedNetworkImage(
                    imageUrl: _courtImageUrl(court.id),
                    width: 56,
                    height: 56,
                    fit: BoxFit.cover,
                    cacheManager: AppImageCacheManager.instance,
                    fadeInDuration: const Duration(milliseconds: 120),
                    placeholder: (context, url) => Container(
                      width: 56,
                      height: 56,
                      color: AppColors.surfaceContainer,
                    ),
                    errorWidget: (context, url, error) => Container(
                      width: 56,
                      height: 56,
                      color: AppColors.surfaceContainer,
                      child: const Icon(
                        Icons.sports,
                        color: AppColors.primaryNeon,
                      ),
                    ),
                  ),
                ),
                title: Text(
                  court.name,
                  style: const TextStyle(
                    color: AppColors.primaryNeon,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '📍 ${court.location}',
                      style: const TextStyle(color: AppColors.onSurfaceVariant),
                    ),
                    Text(
                      '🏀 ${court.sport}',
                      style: const TextStyle(color: AppColors.onSurfaceVariant),
                    ),
                    Text(
                      'R\$ ${court.price.toStringAsFixed(2)} • ${court.availableSlots}/${court.totalSlots} vagas',
                      style: const TextStyle(color: Colors.green),
                    ),
                  ],
                ),
                trailing: Icon(
                  court.availableSlots > 0
                      ? Icons.check_circle
                      : Icons.cancel,
                  color: court.availableSlots > 0 ? Colors.green : Colors.red,
                ),
              ),
            );
          },
        );
      },
    );
  }

  String _courtImageUrl(String courtId) {
    return 'https://picsum.photos/seed/court_$courtId/300/220';
  }
}

/// Filtro de quadras por esporte
class CourtFilterWidget extends StatelessWidget {
  final List<String> sports;

  const CourtFilterWidget({
    Key? key,
    this.sports = const ['Futebol', 'Basquete', 'Vôlei', 'Tênis'],
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<CourtListNotifier>(
      builder: (context, notifier, child) {
        return Padding(
          padding: const EdgeInsets.all(12),
          child: Wrap(
            spacing: 8,
            children: [
              // Botão "Todos"
              FilterChip(
                label: const Text('Todos'),
                selected: notifier.selectedSport == null,
                onSelected: (_) => notifier.clearFilters(),
              ),
              // Botões de esporte
              ...sports.map((sport) {
                return FilterChip(
                  label: Text(sport),
                  selected: notifier.selectedSport == sport,
                  onSelected: (_) => notifier.filterBySport(sport),
                );
              }),
            ],
          ),
        );
      },
    );
  }
}

/// Indicador de cache validity
class CacheSyncIndicator extends StatelessWidget {
  const CacheSyncIndicator({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<CourtListNotifier>(
      builder: (context, notifier, child) {
        final minutesSince = notifier.isCacheValid ? 0 : -1;

        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            children: [
              Icon(
                notifier.isCacheValid ? Icons.cloud_done : Icons.cloud_off,
                color: notifier.isCacheValid ? Colors.green : Colors.orange,
                size: 16,
              ),
              const SizedBox(width: 8),
              Text(
                notifier.isCacheValid
                    ? 'Cache válido'
                    : 'Cache expirado (30+ min)',
                style: TextStyle(
                  fontSize: 12,
                  color: notifier.isCacheValid ? Colors.green : Colors.orange,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
