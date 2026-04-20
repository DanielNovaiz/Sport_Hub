# 🧠 Megaprompt 1: O Cérebro de Estado - Guia Prático

## Overview da Implementação

Implementamos um sistema profissional de **state management com persistência automática**. Agora o app não perde dados ao ser minimizado e sincroniza estado entre telas automaticamente.

## Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│                        main.dart                             │
│            (setupServiceLocator + MultiProvider)            │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌───────────────────┐          ┌──────────────────┐
│ PlayerStatsNotif  │          │ CourtListNotif   │
│ (ChangeNotifier)  │          │ (ChangeNotifier) │
└────────┬──────────┘          └────────┬─────────┘
         │                              │
         ├──────────────┬───────────────┤
         │              │               │
         ▼              ▼               ▼
    Api Service   LocalStorage   Service Locator
         │              │               │
         └──────────────┴───────────────┘
                        │
                ┌───────┴────────┐
                │                │
                ▼                ▼
           Dio API        SharedPreferences
```

---

## 1️⃣ Componentes Principais

### A. Service Locator (get_it)
**Arquivo:** [lib/service_locator.dart](lib/service_locator.dart)

```dart
// Registra TODAS as dependências globais
// Chamado uma única vez no main()
await setupServiceLocator();

// Acessa qualquer dependência de qualquer lugar
final apiService = getIt.get<ApiService>();
final storage = getIt.get<LocalStorageService>();
```

**Benefício:** Trocar para MockApiService nos testes é trivial:
```dart
useMockApiService(MockApiService());
```

### B. API Service (Contrato Abstrato)
**Arquivo:** [lib/data/services/api_service.dart](lib/data/services/api_service.dart)

Interface limpa que define o contrato da API:
```dart
abstract class ApiService {
  Future<PlayerStats> getPlayerStats(String playerId);
  Future<CourtsResponse> getAvailableCourts({...});
  // ... mais métodos
}
```

**Implementação:** [lib/data/services/dio_api_service.dart](lib/data/services/dio_api_service.dart)

### C. Local Storage Service
**Arquivo:** [lib/data/services/local_storage_service.dart](lib/data/services/local_storage_service.dart)

Persiste dados localmente com shared_preferences:
```dart
// Salva
await storage.savePlayerStats(stats);

// Recupera
final cached = await storage.getPlayerStats();

// Verifica expiração
bool isExpired = storage.isCacheExpired(expireAfterMinutes: 30);
```

---

## 2️⃣ State Notifiers (O Cérebro de Estado)

### A. PlayerStatsNotifier
**Arquivo:** [lib/presentation/providers/player_stats_notifier.dart](lib/presentation/providers/player_stats_notifier.dart)

**Responsabilidades:**
- ✅ Sincroniza estatísticas entre telas
- ✅ Persiste automaticamente no cache
- ✅ Gerencia loading states
- ✅ Implementa "optimistic updates"

**Como usar em um Widget:**
```dart
class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<PlayerStatsNotifier>(
      builder: (context, notifier, child) {
        // Acessa o estado
        if (notifier.isLoading) return LoadingWidget();
        if (notifier.hasError) return ErrorWidget(notifier.errorMessage);

        // Usa os dados
        return ListView(
          children: notifier.stats.map((stat) => 
            PlayerCard(stat: stat)
          ).toList(),
        );
      },
    );
  }
}
```

**Carregando dados (manual trigger):**
```dart
// Na página/widget
@override
void initState() {
  super.initState();
  Future.microtask(() {
    context.read<PlayerStatsNotifier>().fetchAllPlayerStats();
  });
}
```

**Atualizando dados (sincronização automática):**
```dart
// Na BoxScoreScreen - atualiza um jogador
await notifier.updatePlayerStats(playerId, {
  'goals': 5,
  'assists': 2,
  'rating': 4.8,
});

// ✨ MAGIC: PlayerCard em HomeScreen atualiza automaticamente!
// Não precisa refresh manual, não precisa de callback
```

### B. CourtListNotifier
**Arquivo:** [lib/presentation/providers/court_list_notifier.dart](lib/presentation/providers/court_list_notifier.dart)

**Responsabilidades:**
- ✅ Mantém lista de quadras
- ✅ Geolocalização automática
- ✅ Filtros (esporte, preço, disponibilidade)
- ✅ Cache com expiração

**Como usar:**
```dart
// Carrega quadras (com geolocalização automática)
await notifier.fetchAvailableCourts(
  useUserLocation: true,
  sport: 'Futebol',
);

// Filtra por esporte
notifier.filterBySport('Basquete');

// Busca quadra específica
final court = notifier.findById('court_123');

// Atualiza vagas
await notifier.updateCourtSlots('court_123', 2);
```

---

## 3️⃣ Integração no App

### main.dart
**Arquivo:** [lib/main.dart](lib/main.dart)

```dart
void main() async {
  // ✅ Setup obrigatório: inicializa SharedPreferences, Dio, Services
  await setupServiceLocator();
  runApp(const MatchingEsportivoApp());
}

class MatchingEsportivoApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Injeta PlayerStatsNotifier globalmente
        ChangeNotifierProvider(
          create: (_) => PlayerStatsNotifier(
            getIt.get(),  // ApiService
            getIt.get(),  // LocalStorageService
          ),
        ),
        // Injeta CourtListNotifier globalmente
        ChangeNotifierProvider(
          create: (_) => CourtListNotifier(
            getIt.get(),  // ApiService
            getIt.get(),  // LocalStorageService
          ),
        ),
      ],
      child: MaterialApp(home: MyApp()),
    );
  }
}
```

---

## 4️⃣ Fluxos Concretos de Uso

### Fluxo 1: Sincronização Automática
```
┌─────────────────┐
│ BoxScoreScreen  │ ← Usuário atualiza score
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ PlayerStatsNotifier.updatePlayerStats() │
│ - Atualiza UI localmente (otimismo)    │
│ - Sincroniza com servidor (Dio/API)    │
│ - Salva no cache (SharedPreferences)    │
└────────┬────────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│ PlayerCard em HomeScreen │ ← Atualiza automaticamente
│ (Consumer<...>)          │   (notifyListeners())
└──────────────────────────┘
```

### Fluxo 2: Restauração de Estado ao Retomar App
```
┌─────────────────┐
│ User kills app  │ ← Android mata processo
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Dados persistidos em SharedPrefs    │
│ - MatchEntryScreen state            │
│ - Last courts loaded                │
│ - User profile cache                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ App retoma (main() → setupService)  │
│ - Carrega LocalStorageService       │
│ - Restaura dados do cache           │
└────────┬────────────────────────────┘
         │
         ▼
┌────────────────────────────┐
│ User vê dados antigos      │
│ Notifier faz refetch       │
│ Se houver mudanças, UI atua
└────────────────────────────┘
```

### Fluxo 3: Teste com MockApiService
```dart
// No setup de testes
void main() {
  setUpAll(() async {
    await setupServiceLocator();
    useMockApiService(MockApiService());
  });

  testWidgets('PlayerCard atualiza ao mudar stats', (tester) async {
    // MockApiService retorna dados fake mas com delay realista
    await tester.pumpWidget(TestApp());
    
    // Verifica carregamento
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpAndSettle();
    
    // Verifica dados mock
    expect(find.text('Test Player'), findsOneWidget);
  });
}
```

---

## 5️⃣ Recursos Avançados

### A. Persistência de MatchEntryScreen (Hydration)
```dart
// Ao sair da tela, salva estado
@override
void dispose() {
  final storage = getIt.get<LocalStorageService>();
  storage.saveMatchState({
    'team1': team1,
    'team2': team2,
    'score': currentScore,
    'timestamp': DateTime.now(),
  });
  super.dispose();
}

// Ao entrar novamente, restaura
@override
void initState() {
  super.initState();
  final storage = getIt.get<LocalStorageService>();
  final savedState = storage.getMatchState();
  if (savedState != null) {
    // Restaura estado anterior
    team1 = savedState['team1'];
    // ...
  }
}
```

### B. Cache Validation
```dart
// Verificar se cache é válido (padrão: 30 minutos)
if (notifier.isCacheValid) {
  // Usa cache, não faz requisição
  print('Cache válido por ${30 - notifier.minutesSinceLastFetch} min');
} else {
  // Cache expirou, refetch
  await notifier.fetchAvailableCourts(forceRefresh: true);
}
```

### C. Filtros em Tempo Real
```dart
// Usuário seleciona esporte
notifier.filterBySport('Futebol');

// Consumer atualiza automaticamente
Consumer<CourtListNotifier>(
  builder: (_, notifier, __) {
    return ListView(
      children: notifier.courts.map(...).toList(),
      // Mostra apenas quadras de futebol
    );
  },
);
```

### D. Otimismo (Optimistic Updates)
```dart
// Ao atualizar, UI muda IMEDIATAMENTE
// Servidor processa em background
// Se falhar, refetch automático

await notifier.updateCourtSlots('court_123', 2);
// Vagas já mostram 2 na UI, mesmo antes de resposta do servidor

// Se servidor retorna erro:
// - Notifier faz refetch
// - UI volta aos valores corretos
// - Mostra erro para usuário
```

---

## 6️⃣ Modelo de Dados

### PlayerStats (Freezed)
```dart
@freezed
class PlayerStats with _$PlayerStats {
  const factory PlayerStats({
    required String id,
    required String name,
    required String position,
    required int assists,
    required int goals,
    required int matches,
    required double rating,
    required DateTime lastUpdated,
  }) = _PlayerStats;
}
```

### Court (Freezed)
```dart
@freezed
class Court with _$Court {
  const factory Court({
    required String id,
    required String name,
    required String location,
    required double latitude,
    required double longitude,
    required String sport,
    required int availableSlots,
    required int totalSlots,
    required double price,
    required DateTime lastChecked,
  }) = _Court;
}
```

---

## 7️⃣ Checklist de Implementação em Novas Telas

Ao criar uma nova tela que precisa de dados:

- [ ] **Inicializar dados no initState**
  ```dart
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<PlayerStatsNotifier>().fetchAllPlayerStats();
    });
  }
  ```

- [ ] **Consumir estado com Consumer**
  ```dart
  Consumer<PlayerStatsNotifier>(
    builder: (context, notifier, child) {
      if (notifier.isLoading) return LoadingWidget();
      return ListView(...);
    },
  );
  ```

- [ ] **Implementar ações de atualização**
  ```dart
  await notifier.updatePlayerStats(id, updates);
  ```

- [ ] **Mostrar estados de erro**
  ```dart
  if (notifier.hasError) {
    return ErrorWidget(notifier.errorMessage);
  }
  ```

- [ ] **Oferecer refresh manual**
  ```dart
  ElevatedButton(
    onPressed: () => notifier.fetchAllPlayerStats(forceRefresh: true),
    child: Text('Atualizar'),
  );
  ```

---

## 8️⃣ Troubleshooting

**P: Dados não atualizam entre telas**
R: Certifique-se que `notifyListeners()` é chamado após mudança de estado.
   O notifier já faz isso automaticamente.

**P: Cache não está sendo lido**
R: Verifique que `LocalStorageService._restoreFromCache()` é chamado no `initState` do notifier.

**P: Mock não funciona nos testes**
R: Certifique-se de chamar `useMockApiService()` após `setupServiceLocator()`.

**P: Dados desaparecem ao fechar o app**
R: Os dados devem estar salvos em SharedPreferences. Se não, verifique se `localStorage.save*()` é chamado.

---

## 9️⃣ Próximos Passos (Megaprompts 2-5)

- **Megaprompt 2:** UX Fluida (animações, transições, offline mode)
- **Megaprompt 3:** Segurança de Dados (criptografia, tokens)
- **Megaprompt 4:** Observabilidade (logging, analytics)
- **Megaprompt 5:** Performance Real (otimizações, profiling)

---

## 🔗 Estrutura de Pastas

```
lib/
├── main.dart                          # Setup + MultiProvider
├── service_locator.dart               # get_it configuration
├── core/                              # Design system
│   ├── app_colors.dart
│   └── app_theme.dart
├── data/
│   ├── models/
│   │   ├── player_stats.dart         # Freezed model
│   │   └── court.dart                # Freezed model
│   └── services/
│       ├── api_service.dart          # Abstract
│       ├── dio_api_service.dart      # Implementation
│       └── local_storage_service.dart # Persistence
├── presentation/
│   ├── pages/
│   │   └── dashboard_feed.dart       # Example consumer
│   ├── providers/
│   │   ├── player_stats_notifier.dart
│   │   └── court_list_notifier.dart
│   └── widgets/
│       ├── player_stats_widget.dart
│       └── court_list_widget.dart
```

---

## 📚 Documentação dos Arquivos

Cada arquivo tem comentários detalhados. Explore:
- [ApiService abstrata](lib/data/services/api_service.dart)
- [DioApiService com interceptors](lib/data/services/dio_api_service.dart)
- [PlayerStatsNotifier com cache](lib/presentation/providers/player_stats_notifier.dart)
- [CourtListNotifier com filtros](lib/presentation/providers/court_list_notifier.dart)

---

**Criado em:** Abril 2026
**Arquiteto:** GitHub Copilot
**Status:** ✅ Pronto para Megaprompt 2
