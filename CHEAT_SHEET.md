# ⚡ CHEAT SHEET: State Management Matching Esportivo

## 🎯 Quick Reference

### Setup (Uma vez no main())
```dart
void main() async {
  await setupServiceLocator();  // Inicializa TUDO
  runApp(const MatchingEsportivoApp());
}
```

### Consumir Estado em Widget
```dart
Consumer<PlayerStatsNotifier>(
  builder: (context, notifier, _) {
    if (notifier.isLoading) return Loading();
    if (notifier.hasError) return Error();
    return ListView(children: notifier.stats.map(...).toList());
  },
);
```

### Carregar Dados (initState)
```dart
@override
void initState() {
  super.initState();
  Future.microtask(() {
    context.read<PlayerStatsNotifier>().fetchAllPlayerStats();
  });
}
```

### Atualizar Dados
```dart
await context.read<PlayerStatsNotifier>().updatePlayerStats(
  '123',
  {'goals': 5, 'assists': 2},
);
```

### Acessar Service em Qualquer Lugar
```dart
final apiService = getIt.get<ApiService>();
final storage = getIt.get<LocalStorageService>();
```

---

## 📋 PlayerStatsNotifier API

| Método | Descrição |
|--------|-----------|
| `fetchAllPlayerStats()` | Carrega todos os jogadores |
| `fetchPlayerStats(id)` | Carrega um jogador |
| `updatePlayerStats(id, updates)` | Atualiza com sync automático |
| `findByName(name)` | Busca por nome |
| `findByPosition(pos)` | Busca por posição |
| `clearAll()` | Limpa tudo |
| `refreshUI()` | Força atualização sem mudança |

| Propriedade | Tipo | Descrição |
|------------|------|-----------|
| `stats` | `List<PlayerStats>` | Lista de jogadores |
| `state` | `LoadingState` | idle/loading/success/error |
| `isLoading` | `bool` | True se carregando |
| `hasError` | `bool` | True se erro |
| `errorMessage` | `String` | Mensagem do erro |
| `isCacheValid` | `bool` | Cache < 30 min |
| `minutesSinceLastFetch` | `int` | Minutos desde fetch |

---

## 📍 CourtListNotifier API

| Método | Descrição |
|--------|-----------|
| `fetchAvailableCourts()` | Carrega quadras |
| `fetchCourtDetails(id)` | Detalhes de uma quadra |
| `filterBySport(sport)` | Filtra por esporte |
| `filterByAvailability(n)` | Filtra por n vagas min |
| `filterByPrice(max)` | Filtra por preço máximo |
| `clearFilters()` | Remove filtros |
| `findById(id)` | Busca quadra |
| `updateCourtSlots(id, n)` | Atualiza vagas |
| `requestUserLocation()` | Pede geolocalização |

---

## 🧪 Mock para Testes

```dart
void main() {
  setUpAll(() async {
    await setupServiceLocator();
    useMockApiService(MockApiService());  // ← Ativa mock
  });

  testWidgets('Test', (tester) async {
    // MockApiService é automaticamente usado
  });
}
```

---

## 💾 LocalStorageService API

```dart
// Player Stats
await storage.savePlayerStats(stats);
final stats = await storage.getPlayerStats();

// Courts
await storage.saveCourts(courts);
final courts = await storage.getCourts();

// User Profile
await storage.saveUserProfile({'name': 'John'});
final profile = await storage.getUserProfile();

// Match State (Hydration)
await storage.saveMatchState({'team1': 'A', 'team2': 'B'});
final state = await storage.getMatchState();

// Utilities
bool expired = storage.isCacheExpired();
int minutes = storage.getMinutesSinceLastSync();
await storage.clearAll();
```

---

## 🔄 Padrão de Notifier com Cache

```dart
// Automático na inicialização
PlayerStatsNotifier(apiService, localStorage) {
  _initialize();  // ← Carrega cache
}

// Fetch com cache validation
Future<void> fetchAllPlayerStats({bool forceRefresh = false}) async {
  if (isCacheValid && !forceRefresh) return;  // Skip if cache OK
  
  _state = LoadingState.loading;
  notifyListeners();
  
  try {
    final response = await _apiService.getAllPlayerStats();
    _stats = response.stats;
    await _localStorage.savePlayerStats(_stats);  // Save cache
    _state = LoadingState.success;
  } catch (e) {
    _state = LoadingState.error;
  }
  
  notifyListeners();
}
```

---

## 🎪 Estados Comuns

### Loading
```dart
if (notifier.isLoading) {
  return Center(
    child: CircularProgressIndicator(
      color: AppColors.primaryNeon,
    ),
  );
}
```

### Error
```dart
if (notifier.hasError) {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text('Erro: ${notifier.errorMessage}'),
        ElevatedButton(
          onPressed: () => notifier.fetchAllPlayerStats(forceRefresh: true),
          child: Text('Tentar novamente'),
        ),
      ],
    ),
  );
}
```

### Empty
```dart
if (notifier.stats.isEmpty) {
  return Center(child: Text('Nenhum dado'));
}
```

### Success
```dart
return ListView.builder(
  itemCount: notifier.stats.length,
  itemBuilder: (_, i) => StatCard(stat: notifier.stats[i]),
);
```

---

## 🔐 Padrão de Otimismo

```dart
Future<void> updateScore(String id, int newScore) async {
  // 1. Atualiza localmente (otimismo)
  final index = _stats.indexWhere((s) => s.id == id);
  if (index != -1) {
    _stats[index] = _stats[index].copyWith(goals: newScore);
    notifyListeners();  // UI atualiza IMEDIATAMENTE
  }

  try {
    // 2. Sincroniza com servidor
    await _apiService.updatePlayerStats(id, {'goals': newScore});
    
    // 3. Salva no cache
    await _localStorage.savePlayerStats(_stats);
    
    _state = LoadingState.success;
  } catch (e) {
    // 4. Erro? Refetch para descartar otimismo
    await fetchAllPlayerStats(forceRefresh: true);
  }

  notifyListeners();
}
```

---

## 📱 Exemplo Completo: Tela de Jogadores

```dart
class PlayersPage extends StatefulWidget {
  @override
  State<PlayersPage> createState() => _PlayersPageState();
}

class _PlayersPageState extends State<PlayersPage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<PlayerStatsNotifier>().fetchAllPlayerStats();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Jogadores'),
        actions: [
          Consumer<PlayerStatsNotifier>(
            builder: (_, notifier, __) => 
              notifier.isLoading
                ? SizedBox.square(dimension: 16, child: CircularProgressIndicator())
                : IconButton(
                    icon: Icon(Icons.refresh),
                    onPressed: () => notifier.fetchAllPlayerStats(forceRefresh: true),
                  ),
          ),
        ],
      ),
      body: Consumer<PlayerStatsNotifier>(
        builder: (_, notifier, __) {
          if (notifier.isLoading) return Center(child: CircularProgressIndicator());
          if (notifier.hasError) return ErrorWidget(notifier.errorMessage);
          if (notifier.stats.isEmpty) return Center(child: Text('Sem dados'));
          
          return ListView.builder(
            itemCount: notifier.stats.length,
            itemBuilder: (_, i) {
              final stat = notifier.stats[i];
              return ListTile(
                title: Text(stat.name),
                subtitle: Text('${stat.goals} gols'),
                trailing: Icon(Icons.edit),
                onTap: () async {
                  final result = await Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => EditPlayerPage(stat: stat),
                    ),
                  );
                  if (result != null) {
                    await notifier.updatePlayerStats(
                      stat.id,
                      result,
                    );
                  }
                },
              );
            },
          );
        },
      ),
    );
  }
}
```

---

## 🚨 Erros Comuns

### ❌ Esquecer setupServiceLocator()
```dart
// ERRADO
void main() {
  runApp(MyApp());  // ← ApiService não existe!
}

// CORRETO
void main() async {
  await setupServiceLocator();  // ← Setup ANTES
  runApp(MyApp());
}
```

### ❌ Usar read em builder
```dart
// ERRADO - builder rebuilda toda hora
builder: (context) {
  context.read<NotifierX>().fetch();  // Chamado a cada rebuild!
}

// CORRETO - microtask
@override
void initState() {
  super.initState();
  Future.microtask(() {
    context.read<NotifierX>().fetch();  // Chamado uma vez
  });
}
```

### ❌ Não esperar futures
```dart
// ERRADO
notifier.updatePlayerStats(id, updates);  // Fire and forget
// Usuário vê UI desatualizada

// CORRETO
await notifier.updatePlayerStats(id, updates);
// Espera antes de continuar
```

---

## 🎯 Checklist para Nova Tela

- [ ] Importar `Consumer`
- [ ] Importar notifier (`PlayerStatsNotifier` ou `CourtListNotifier`)
- [ ] Chamar fetch em `initState`
- [ ] Envolver UI com `Consumer<NotifierX>`
- [ ] Tratar `isLoading` state
- [ ] Tratar `hasError` state
- [ ] Tratar empty state
- [ ] Mapear dados com `notifier.stats.map()`
- [ ] Implementar refresh button

---

## 🔧 Configuração de Cache

```dart
// Padrão: 30 minutos
bool expired = storage.isCacheExpired();

// Customizado
bool expired = storage.isCacheExpired(expireAfterMinutes: 60);

// Minutos exatos
int minutes = storage.getMinutesSinceLastSync();

// Force refresh sempre
await notifier.fetchAllPlayerStats(forceRefresh: true);
```

---

## 📊 Estrutura de Dados

### PlayerStats
```dart
PlayerStats(
  id: '1',
  name: 'João Silva',
  position: 'Goleiro',
  assists: 2,
  goals: 0,
  matches: 10,
  rating: 4.5,
  lastUpdated: DateTime.now(),
)
```

### Court
```dart
Court(
  id: 'court_1',
  name: 'Quadra do Bueno',
  location: 'Setor Bueno, Goiânia',
  latitude: -15.7942,
  longitude: -48.0676,
  sport: 'Futebol',
  availableSlots: 2,
  totalSlots: 4,
  price: 150.0,
  lastChecked: DateTime.now(),
)
```

---

**Última atualização:** Abril 2026  
**Versão:** 1.0  
**Mantido por:** GitHub Copilot
