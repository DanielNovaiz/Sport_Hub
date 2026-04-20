import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:provider/provider.dart';
import '../../presentation/providers/player_stats_notifier.dart';
import '../../core/app_colors.dart';
import '../../core/app_image_cache_manager.dart';
import 'shimmer_skeletons.dart';

/// Exemplo de widget que consome estado do PlayerStatsNotifier
/// Demonstra como usar o notifier em um widget consumer
class PlayerStatsWidget extends StatelessWidget {
  final String? playerId;

  const PlayerStatsWidget({Key? key, this.playerId}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerStatsNotifier>(
      builder: (context, notifier, child) {
        // Caso 1: Carregando dados
        if (notifier.isLoading) {
          return const SkeletonList(
            itemCount: 8,
            cacheExtent: 840,
            itemBuilder: (_, __) => PlayerCardShimmer(),
          );
        }

        // Caso 2: Erro ao carregar
        if (notifier.hasError) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Erro: ${notifier.errorMessage}',
                  style: const TextStyle(color: Colors.red),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: () =>
                      notifier.fetchAllPlayerStats(forceRefresh: true),
                  child: const Text('Tentar novamente'),
                ),
              ],
            ),
          );
        }

        // Caso 3: Dados carregados com sucesso
        final stats = notifier.stats;
        if (stats.isEmpty) {
          return const Center(
            child: Text('Nenhuma estatística encontrada'),
          );
        }

        return ListView.builder(
          cacheExtent: 840,
          itemCount: stats.length,
          itemBuilder: (context, index) {
            final stat = stats[index];
            return Card(
              margin: const EdgeInsets.all(8),
              color: AppColors.surface,
              child: ListTile(
                leading: ClipOval(
                  child: CachedNetworkImage(
                    imageUrl: _playerImageUrl(stat.id),
                    width: 48,
                    height: 48,
                    fit: BoxFit.cover,
                    cacheManager: AppImageCacheManager.instance,
                    fadeInDuration: const Duration(milliseconds: 120),
                    placeholder: (context, url) => Container(
                      width: 48,
                      height: 48,
                      color: AppColors.surfaceContainer,
                    ),
                    errorWidget: (context, url, error) => const CircleAvatar(
                      backgroundColor: AppColors.surfaceContainer,
                      child: Icon(Icons.person, color: AppColors.primaryNeon),
                    ),
                  ),
                ),
                title: Text(
                  stat.name,
                  style: const TextStyle(
                    color: AppColors.primaryNeon,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Posição: ${stat.position}',
                      style: const TextStyle(color: AppColors.onSurfaceVariant),
                    ),
                    Text(
                      'Rating: ${stat.rating}/5.0',
                      style: const TextStyle(color: AppColors.onSurfaceVariant),
                    ),
                  ],
                ),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('⚽ ${stat.goals}', style: const TextStyle(color: AppColors.primaryNeon)),
                    Text('🎯 ${stat.assists}', style: const TextStyle(color: AppColors.primaryNeon)),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  String _playerImageUrl(String playerId) {
    return 'https://picsum.photos/seed/player_$playerId/200/200';
  }
}

/// Exemplo de como atualizar dados em uma tela
/// e ver a atualização automática em outras telas
class UpdatePlayerStatsExample extends StatefulWidget {
  const UpdatePlayerStatsExample({Key? key}) : super(key: key);

  @override
  State<UpdatePlayerStatsExample> createState() =>
      _UpdatePlayerStatsExampleState();
}

class _UpdatePlayerStatsExampleState extends State<UpdatePlayerStatsExample> {
  late TextEditingController _goalsController;
  late TextEditingController _assistsController;

  @override
  void initState() {
    super.initState();
    _goalsController = TextEditingController();
    _assistsController = TextEditingController();
  }

  @override
  void dispose() {
    _goalsController.dispose();
    _assistsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerStatsNotifier>(
      builder: (context, notifier, child) {
        if (notifier.stats.isEmpty) {
          return const Center(child: Text('Carregue os dados primeiro'));
        }

        final firstPlayer = notifier.stats.first;

        return SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Text(
                'Atualizar: ${firstPlayer.name}',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primaryNeon,
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _goalsController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Gols',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _assistsController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Assistências',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () async {
                  final goals = int.tryParse(_goalsController.text);
                  final assists = int.tryParse(_assistsController.text);

                  if (goals == null || assists == null) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Valores inválidos')),
                    );
                    return;
                  }

                  // Atualiza o notifier
                  // Isso vai automaticamente sincronizar em TODAS as telas
                  // que consomem este notifier
                  await notifier.updatePlayerStats(
                    firstPlayer.id,
                    {
                      'goals': goals,
                      'assists': assists,
                    },
                  );

                  if (!mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Stats atualizadas!')),
                  );
                },
                child: const Text('Atualizar Stats'),
              ),
            ],
          ),
        );
      },
    );
  }
}
