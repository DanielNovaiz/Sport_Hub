# ⚡ Quick Start - Hardware Setup (5 minutos)

---

## 1️⃣ Já está integrado? ✅

`lib/main.dart` já tem:
```dart
import 'core/app_lifecycle_integration.dart';

home: AppLifecycleHandler(child: ClubIdentityPage()),
```

GPS para em background automaticamente.

---

## 2️⃣ Usar GPS em uma Tela

```dart
class MyCourtPage extends StatefulWidget {
  @override
  State<MyCourtPage> createState() => _MyCourtPageState();
}

class _MyCourtPageState extends State<MyCourtPage> {
  @override
  void initState() {
    super.initState();
    _setupLocation();
  }

  Future<void> _setupLocation() async {
    final notifier = context.read<CourtListNotifier>();
    
    // 1. Pedir localização
    final result = await notifier.requestUserLocation();
    
    // 2. Mostrar sheet se necessário
    if (result.status == LocationStatus.serviceDisabled) {
      GPSDisabledBottomSheet.show(context);
    }
    
    // 3. Carregar quadras
    await notifier.fetchAvailableCourts(useUserLocation: true);
    
    // 4. Iniciar escuta contínua
    await notifier.startListeningToLocation();
  }

  @override
  void dispose() {
    // Para GPS ao sair da página (economiza bateria)
    context.read<CourtListNotifier>().stopListeningToLocation();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<CourtListNotifier>(
      builder: (_, notifier, __) {
        return Scaffold(
          body: Column(
            children: [
              // GPS Status
              Container(
                padding: EdgeInsets.all(12),
                color: _getColor(notifier.gpsStatus),
                child: Text(_getText(notifier.gpsStatus)),
              ),
              // Lista de quadras
              Expanded(
                child: ListView.builder(
                  itemCount: notifier.courts.length,
                  itemBuilder: (_, i) => _buildCourtCard(notifier.courts[i]),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Color _getColor(GPSSignalStatus status) {
    switch (status) {
      case GPSSignalStatus.strong: return Colors.green;
      case GPSSignalStatus.weak: return Colors.orange;
      case GPSSignalStatus.lost: return Colors.red;
      default: return Colors.grey;
    }
  }

  String _getText(GPSSignalStatus status) {
    switch (status) {
      case GPSSignalStatus.strong: return '📍 GPS Ativo';
      case GPSSignalStatus.weak: return '📍 Sinal Fraco';
      case GPSSignalStatus.lost: return '❌ Sinal Perdido';
      case GPSSignalStatus.disabled: return '⚙️ GPS Desligado';
      case GPSSignalStatus.permissionDenied: return '🔒 Sem Permissão';
    }
  }
}
```

---

## 3️⃣ Rodar Testes

```bash
flutter test tests/test_gps_stress.dart
```

Esperado: ✅ 5 testes passando

---

## 4️⃣ API Rápida

### LocationService
```dart
// Obter localização (com fallback)
final result = await LocationService.getLocationWithFallback();
print(result.latitude);   // -15.7942
print(result.longitude);  // -48.0676
print(result.status);     // LocationStatus.success

// Escuta contínua
LocationService.getPositionStream().listen((pos) {
  print('Atualizado: ${pos.latitude}');
});

// Abrir settings
LocationService.openLocationSettings();
```

### MediaPermissionService
```dart
// Câmera
final result = await MediaPermissionService.requestCameraPermission();
if (result.isGranted) { /* abrir câmera */ }

// Galeria
final result = await MediaPermissionService.requestGalleryPermission();
if (result.isGranted) { /* abrir galeria */ }
```

### CourtListNotifier
```dart
final notifier = context.read<CourtListNotifier>();

// Localização
await notifier.requestUserLocation();
await notifier.startListeningToLocation();
await notifier.stopListeningToLocation();

// Status
notifier.gpsStatus          // GPSSignalStatus enum
notifier.userLatitude       // double?
notifier.userLongitude      // double?
notifier.isListeningToGPS   // bool
```

---

## 5️⃣ Documentação Completa

| Necessidade | Arquivo |
|-------------|---------|
| Entender tudo | [HARDWARE_SETUP_GUIDE.md](HARDWARE_SETUP_GUIDE.md) |
| Testar em device | [DEVICE_TESTING_GUIDE.md](DEVICE_TESTING_GUIDE.md) |
| Configurar Android | [ANDROID_CONFIG.md](ANDROID_CONFIG.md) |
| Ver índice | [INDEX_HARDWARE_SETUP.md](INDEX_HARDWARE_SETUP.md) |
| PM/Arquiteto | [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) |

---

## 🎯 Status

✅ GPS com fallback  
✅ Bateria otimizada (pausa em background)  
✅ Permissões robusto  
✅ 5 testes passando  
✅ 100% pronto para produção  

**Pronto para usar! 🚀**
