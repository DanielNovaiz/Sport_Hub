import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:provider/provider.dart';
import 'core/app_theme.dart';
import 'presentation/pages/dashboard_page.dart';
import 'presentation/pages/club_identity_page.dart';
import 'presentation/providers/player_stats_notifier.dart';
import 'presentation/providers/court_list_notifier.dart';
import 'service_locator.dart';
import 'core/app_lifecycle_integration.dart';
import 'core/app_colors.dart';
import 'core/app_image_cache_manager.dart';
import 'presentation/widgets/shimmer_skeletons.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ==================== SETUP ====================
  // Inicializa todas as dependências antes de rodar o app
  await setupServiceLocator();

  runApp(const MatchingEsportivoApp());
}

class MatchingEsportivoApp extends StatelessWidget {
  const MatchingEsportivoApp({super.key});

  @override
  Widget build(BuildContext context) {
    // ==================== PROVIDER SETUP ====================
    // Configura os notifiers globais que sincronizam estado entre telas
    return MultiProvider(
      providers: [
        // PlayerStatsNotifier - sincroniza estatísticas de jogadores
        ChangeNotifierProvider(
          create: (_) => PlayerStatsNotifier(
            getIt.get(),  // ApiService
            getIt.get(),  // LocalStorageService
          ),
        ),

        // CourtListNotifier - sincroniza lista de quadras disponíveis
        ChangeNotifierProvider(
          create: (_) => CourtListNotifier(
            getIt.get(),  // ApiService
            getIt.get(),  // LocalStorageService
          ),
        ),
      ],
      child: MaterialApp(
        title: 'Matching Esportivo',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.kineticTheme,
        // ==================== LIFECYCLE HANDLER ====================
        // Gerencia o ciclo de vida do app (pausar GPS em background, etc)
        home: AssetPreloadGate(
          child: AppLifecycleHandler(
            child: const ClubIdentityPage(),
          ),
        ),
      ),
    );
  }
}

class AssetPreloadGate extends StatefulWidget {
  final Widget child;

  const AssetPreloadGate({super.key, required this.child});

  @override
  State<AssetPreloadGate> createState() => _AssetPreloadGateState();
}

class _AssetPreloadGateState extends State<AssetPreloadGate> {
  late final Future<void> _preloadFuture;

  static const List<String> _essentialSportAssets = [
    'assets/icons/sports/soccer.png',
    'assets/icons/sports/basketball.png',
    'assets/icons/sports/volleyball.png',
    'assets/icons/sports/tennis.png',
    'assets/logos/app_logo.png',
  ];

  static const List<String> _essentialLogoUrls = [
    'https://lh3.googleusercontent.com/aida-public/AB6AXuDGET-5C__95ybXiXGrr4GokRgUx0j8svhRI9pvrZKKEuCfxkF6SYtUPTK0ddCZgCLyirLs1scF6MaAtrnaZ2WIr2OJgvQMg4k_ptFRAsFDZYIHDgSQkM2yMTWSTggdSETyF0MnmyrK9MvqxGpI4oH57N3PY7_ON3F7Ff0y4BLdG6ns5uT_-nL3hffIRFSq_GI-saVe-7OcaciK3PjV6_fW_Iyyw9X7bdV-2XTqlH-5MzV-ML3uPN1NrH7D9PQAU_h0wVgVM7MNOOk',
    'https://lh3.googleusercontent.com/aida-public/AB6AXuAYRo6qYiAdNS543VOo9V5bdbPPcwmjycO5Z96aCAev23zA1_uuES1da_VVKWXBfIP3GvB1SZ-ej365Mc0XvZ9LfOuPRgW33w7TjdvFYualR3ze2aMbKR92qlJ6DdrXVPkiudCSQMSrIV7r3CX73m9RmYivW78gpvasKBdf_x_bj5MwNLEuQg4AfGzz2kgWT4LZmn57_U8SOUDpo6uPH2KBXnizolwIu_0B7FfkHenC4NFSvSC8yBLg_pSSwDm4pI9bxK7Ejxzx_WU',
  ];

  @override
  void initState() {
    super.initState();
    _preloadFuture = _precacheEssentialAssets();
  }

  Future<void> _precacheEssentialAssets() async {
    // Precache de assets locais (se existirem no bundle)
    for (final assetPath in _essentialSportAssets) {
      final exists = await _assetExists(assetPath);
      if (!exists || !mounted) continue;
      await precacheImage(AssetImage(assetPath), context);
    }

    // Warm-up do cache para logos essenciais em rede (7 dias)
    for (final logoUrl in _essentialLogoUrls) {
      if (!mounted) break;
      await precacheImage(
        CachedNetworkImageProvider(
          logoUrl,
          cacheManager: AppImageCacheManager.instance,
        ),
        context,
      );
    }
  }

  Future<bool> _assetExists(String assetPath) async {
    try {
      await rootBundle.load(assetPath);
      return true;
    } catch (_) {
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _preloadFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Scaffold(
            backgroundColor: AppColors.surface,
            body: Padding(
              padding: EdgeInsets.all(16),
              child: SkeletonList(
                itemCount: 6,
                itemBuilder: (_, __) => CourtCardShimmer(),
              ),
            ),
          );
        }

        return widget.child;
      },
    );
  }
}