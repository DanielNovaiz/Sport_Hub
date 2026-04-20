# 🤖 Android Configuration - GPS, Camera, Storage

Este guia cobre as configurações necessárias no Android para GPS, câmera e armazenamento.

---

## 📱 AndroidManifest.xml

**Localização:** `android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.matching.esportivo">

    <!-- ==================== LOCALIZAÇÃO ==================== -->
    <!-- Permissão de localização precisa (GPS) -->
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    
    <!-- Permissão de localização aproximada (rede) -->
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

    <!-- ==================== CÂMERA ==================== -->
    <!-- Para tirar fotos de perfil ou quadras -->
    <uses-permission android:name="android.permission.CAMERA" />

    <!-- ==================== ARMAZENAMENTO ==================== -->
    <!-- Ler fotos/vídeos da galeria (Android 13+) -->
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    
    <!-- Para compatibilidade com Android < 13 -->
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <!-- ==================== CONECTIVIDADE ==================== -->
    <!-- Para verificar se tem internet -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- ==================== APPLICATION ==================== -->
    <application
        android:label="Matching Esportivo"
        android:icon="@mipmap/ic_launcher">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode">

            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Configure any Android-specific meta tags here as needed -->
    </application>
</manifest>
```

---

## 🔧 build.gradle

**Localização:** `android/app/build.gradle`

```gradle
// ... rest of file

android {
    compileSdkVersion 34  // ← Importante para Android 14 (API 34)

    defaultConfig {
        applicationId "com.matching.esportivo"
        minSdkVersion 21    // ← Android 5.0
        targetSdkVersion 34 // ← Android 14
        versionCode 1
        versionName "1.0.0"
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}

dependencies {
    // Adicione se não estiver presente
    // Google Play Services para Location
    implementation 'com.google.android.gms:play-services-location:21.0.1'
}
```

---

## 📍 Configuração de Localização Precisa (GPS)

Para obter melhor precisão com GPS:

### AndroidManifest.xml (adicional)

```xml
<!-- Para usar GPS de alta precisão -->
<uses-feature
    android:name="android.hardware.location.gps"
    android:required="false" />
```

### Runtime Permissions (já gerenciado por permission_handler)

A biblioteca `permission_handler` automaticamente pede as permissões em runtime no Android 6.0+.

---

## 📹 Câmera - Policies da Play Store

Para evitar rejeição na Play Store:

### 1. Política de Permissão (no app)

```dart
// Explique por que precisa de câmera
void _requestCameraWithExplanation(BuildContext context) async {
  // Mostrar diálogo explicativo ANTES de pedir
  showDialog(
    context: context,
    builder: (_) => AlertDialog(
      title: Text('Acesso à Câmera'),
      content: Text(
        'Precisamos de acesso à câmera para você tirar fotos de seu perfil e das quadras.',
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Negar'),
        ),
        TextButton(
          onPressed: () async {
            Navigator.pop(context);
            final result = await MediaPermissionService.requestCameraPermission();
            if (result.isGranted) {
              // Abrir câmera
            }
          },
          child: Text('Permitir'),
        ),
      ],
    ),
  );
}
```

### 2. Privacy Policy (obrigatório)

Sua app deve incluir:
- URL para Política de Privacidade
- Explicação sobre coleta de GPS
- Explicação sobre fotos

---

## 📸 Galeria/Storage - Comportamento por Versão

| Android | Comportamento | Permissão |
|---------|---------------|-----------|
| < 10 | Acesso a todos os arquivos | `READ_EXTERNAL_STORAGE` |
| 10-12 | Scoped Storage + allowlist | `READ_EXTERNAL_STORAGE` |
| 13+ | Media-specific permissions | `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO` |
| 14+ | Partial Media Access | `READ_MEDIA_IMAGES` (limited) |

A biblioteca `permission_handler` abstrai isso automaticamente.

---

## 🌍 GPS - Troubleshooting

### GPS não funciona no emulador

```bash
# No emulador, use mock location
# 1. Abra o emulador
# 2. Vá em: Settings > Location > Use mock locations
# 3. Use app como "Mock Location App"
```

### Ou configure no código:

```dart
// Para testes, forçar localização mock
if (kDebugMode) {
  // Mock location em modo debug
  _userLatitude = -15.7942;
  _userLongitude = -48.0676;
}
```

---

## 🔐 Segurança - SSL Pinning (futuro)

Para proteger requisições GPS/API:

```dart
// Em dio_api_service.dart (futura implementação)
_dio.httpClientAdapter = IOHttpClientAdapter(
  createHttpClient: () {
    final client = HttpClient();
    // Implementar certificate pinning aqui
    return client;
  },
);
```

---

## 📦 Dependencies

Adicione ao `pubspec.yaml`:

```yaml
dependencies:
  geolocator: ^13.0.2           # GPS
  permission_handler: ^11.4.4   # Permissões
  app_lifecycle: ^2.0.0         # Lifecycle
```

---

## ✅ Checklist de Deploy

Antes de enviar para Play Store:

- [ ] AndroidManifest.xml com todas as permissões
- [ ] Politica de Privacidade linkada no app
- [ ] Explicação clara no app sobre por que pede GPS
- [ ] Explicação clara no app sobre por que pede câmera
- [ ] Testado em dispositivo real com GPS ligado
- [ ] Testado em dispositivo real com GPS desligado
- [ ] Testado com permissões negadas
- [ ] Testado em background (bateria)
- [ ] Consentimento claro para "Location Always" (se necessário)
- [ ] Fallback para Novo Mundo (para offline)

---

## 📚 Referências

- [Android Permissions](https://developer.android.com/guide/topics/permissions)
- [GPS no Flutter](https://pub.dev/packages/geolocator)
- [Play Store Policy - Location](https://support.google.com/googleplay/android-developer/answer/9888170)
- [Play Store Policy - Camera](https://support.google.com/googleplay/android-developer/answer/9888170)
- [Scoped Storage](https://developer.android.com/about/versions/11/privacy/storage)

---

**Última atualização:** Abril 2026  
**Android SDK:** 34 (Android 14)  
**Min SDK:** 21 (Android 5.0)
