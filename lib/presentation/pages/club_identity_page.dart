import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../core/app_colors.dart';
import '../../core/app_image_cache_manager.dart';

class ClubIdentityPage extends StatelessWidget {
  const ClubIdentityPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface.withOpacity(0.6),
        elevation: 0,
        leading: Padding(
          padding: const EdgeInsets.only(left: 16),
          child: Center(
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.outlineVariant),
              ),
              clipBehavior: Clip.antiAlias,
              child: CachedNetworkImage(
                imageUrl:
                    'https://lh3.googleusercontent.com/aida-public/AB6AXuDGET-5C__95ybXiXGrr4GokRgUx0j8svhRI9pvrZKKEuCfxkF6SYtUPTK0ddCZgCLyirLs1scF6MaAtrnaZ2WIr2OJgvQMg4k_ptFRAsFDZYIHDgSQkM2yMTWSTggdSETyF0MnmyrK9MvqxGpI4oH57N3PY7_ON3F7Ff0y4BLdG6ns5uT_-nL3hffIRFSq_GI-saVe-7OcaciK3PjV6_fW_Iyyw9X7bdV-2XTqlH-5MzV-ML3uPN1NrH7D9PQAU_h0wVgVM7MNOOk',
                cacheManager: AppImageCacheManager.instance,
                fit: BoxFit.cover,
                placeholder: (context, url) => Container(
                  color: AppColors.surfaceContainer,
                ),
                errorWidget: (context, url, error) => const Icon(
                  Icons.shield,
                  color: AppColors.primaryNeon,
                ),
              ),
            ),
          ),
        ),
        title: const Text(
          'MATCHING ESPORTIVO',
          style: TextStyle(
            color: AppColors.primaryNeon,
            fontWeight: FontWeight.bold,
            letterSpacing: -1,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined, color: AppColors.primaryNeon),
            onPressed: () {},
          ),
        ],
      ),
      body: ListView.builder(
        cacheExtent: 960,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        itemCount: 8,
        itemBuilder: (context, index) {
          switch (index) {
            case 0:
              return const Text(
                'CLUB IDENTITY',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 36,
                  fontWeight: FontWeight.bold,
                  letterSpacing: -1,
                ),
              );
            case 1:
              return const Padding(
                padding: EdgeInsets.only(top: 8, bottom: 40),
                child: Text(
                  'Gerencie seu prestígio e explore novos centros de treinamento.',
                  style: TextStyle(
                    color: AppColors.onSurfaceVariant,
                    fontSize: 14,
                  ),
                ),
              );
            case 2:
              return _buildSectionHeader(
                'CLUBES QUE SOU MEMBRO',
                '3 ATIVOS',
                AppColors.primaryNeon,
              );
            case 3:
              return Padding(
                padding: const EdgeInsets.only(top: 24, bottom: 16),
                child: _buildClubCard(
                  title: 'APEX PERFORMANCE LAB',
                  subtitle:
                      'Centro de treinamento focado em biomecânica e recuperação elite.',
                  role: 'ADMIN',
                  members: '124',
                  location: 'Goiânia, BR',
                  icon: Icons.security,
                  isAdmin: true,
                ),
              );
            case 4:
              return _buildClubCard(
                title: 'VANGUARD SQUASH CLUB',
                subtitle:
                    'Comunidade exclusiva para atletas de raquete de alto rendimento.',
                role: 'MEMBRO',
                members: '82',
                location: 'São Paulo, BR',
                icon: Icons.fitness_center,
                isAdmin: false,
              );
            case 5:
              return const SizedBox(height: 48);
            case 6:
              return Padding(
                padding: const EdgeInsets.only(bottom: 24),
                child: _buildSectionHeader(
                  'CLUBES DESCOBERTOS',
                  'NOVO',
                  Colors.cyanAccent,
                ),
              );
            default:
              return _buildDiscoveryCard();
          }
        },
      ),
    );
  }

  Widget _buildSectionHeader(String title, String status, Color accentColor) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(width: 4, height: 24, decoration: BoxDecoration(color: accentColor, borderRadius: BorderRadius.circular(2))),
            const SizedBox(width: 12),
            Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 1.2)),
          ],
        ),
        Text(status, style: TextStyle(color: accentColor, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
      ],
    );
  }

  Widget _buildClubCard({required String title, required String subtitle, required String role, required String members, required String location, required IconData icon, required bool isAdmin}) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        borderRadius: BorderRadius.circular(4),
        border: const Border(bottom: BorderSide(color: Colors.transparent, width: 2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                width: 50, height: 50,
                decoration: BoxDecoration(color: AppColors.surfaceContainerHigh, borderRadius: BorderRadius.circular(8), border: Border.all(color: AppColors.outlineVariant)),
                child: Icon(icon, color: isAdmin ? AppColors.primaryNeon : AppColors.onSurfaceVariant),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: isAdmin ? Colors.green.withOpacity(0.1) : Colors.transparent,
                  border: Border.all(color: isAdmin ? AppColors.primaryNeon.withOpacity(0.2) : AppColors.onSurfaceVariant.withOpacity(0.2)),
                ),
                child: Text(role, style: TextStyle(color: isAdmin ? AppColors.primaryNeon : AppColors.onSurfaceVariant, fontSize: 10, fontWeight: FontWeight.black, letterSpacing: 2)),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(subtitle, style: const TextStyle(color: AppColors.onSurfaceVariant, fontSize: 13)),
          const SizedBox(height: 20),
          Row(
            children: [
              Icon(Icons.groups, size: 14, color: AppColors.onSurfaceVariant),
              const SizedBox(width: 4),
              Text('$members Membros', style: const TextStyle(color: AppColors.onSurfaceVariant, fontSize: 11)),
              const SizedBox(width: 16),
              Icon(Icons.location_on, size: 14, color: AppColors.onSurfaceVariant),
              const SizedBox(width: 4),
              Text(location, style: const TextStyle(color: AppColors.onSurfaceVariant, fontSize: 11)),
            ],
          )
        ],
      ),
    );
  }

  Widget _buildDiscoveryCard() {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(color: AppColors.surfaceContainerLow, borderRadius: BorderRadius.circular(4)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            height: 150,
            width: double.infinity,
            decoration: const BoxDecoration(
              color: AppColors.surfaceContainer,
            ),
            clipBehavior: Clip.antiAlias,
            child: CachedNetworkImage(
              imageUrl:
                  'https://lh3.googleusercontent.com/aida-public/AB6AXuAYRo6qYiAdNS543VOo9V5bdbPPcwmjycO5Z96aCAev23zA1_uuES1da_VVKWXBfIP3GvB1SZ-ej365Mc0XvZ9LfOuPRgW33w7TjdvFYualR3ze2aMbKR92qlJ6DdrXVPkiudCSQMSrIV7r3CX73m9RmYivW78gpvasKBdf_x_bj5MwNLEuQg4AfGzz2kgWT4LZmn57_U8SOUDpo6uPH2KBXnizolwIu_0B7FfkHenC4NFSvSC8yBLg_pSSwDm4pI9bxK7Ejxzx_WU',
              cacheManager: AppImageCacheManager.instance,
              fit: BoxFit.cover,
              color: Colors.black.withOpacity(0.5),
              colorBlendMode: BlendMode.darken,
              placeholder: (context, url) => Container(
                color: AppColors.surfaceContainerHigh,
              ),
              errorWidget: (context, url, error) => const Icon(
                Icons.image_not_supported,
                color: AppColors.onSurfaceVariant,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('TITAN CROSSFIT HUB', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(height: 8),
                const Text('Nova unidade especializada em levantamento olímpico e telemetria.', style: TextStyle(color: AppColors.onSurfaceVariant, fontSize: 14)),
                const SizedBox(height: 24),
                ElevatedButton(
                  onPressed: () {},
                  child: const Center(child: Text('SOLICITAR INGRESSO')),
                )
              ],
            ),
          )
        ],
      ),
    );
  }
}