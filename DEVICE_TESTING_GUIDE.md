# 📱 Device Testing Guide - GPS, Câmera, Permissões

**Data:** Abril 17, 2026  
**Objetivo:** Validar hardware setup em dispositivo real

---

## 🔧 Setup Inicial

### 1. Instalar Flutter DevTools

```bash
# Terminal
flutter pub global activate devtools
flutter devtools
```

Acessa: `http://localhost:9100`

### 2. Conectar Dispositivo Real

```bash
# Listar dispositivos conectados
flutter devices

# Esperado:
# Android Device (mobile) • R38M70ABCDE • android-arm64  • Android 14
# iPhone (mobile)         • iPhoneXS    • ios            • iOS 17
```

### 3. Build para Device

```bash
# Android
flutter run -d <device_id>

# iOS
flutter run -d <device_id>
```

---

## 🗺️ Teste 1: GPS em Sinal Forte

### Procedimento

1. Abra app em local com GPS forte (exterior, céu aberto)
2. Navegue para tela de quadras
3. Verifique se localização é obtida

### Validação

```
✅ GPS Status: Strong (verde)
✅ Latitude/Longitude: Coordenadas reais (~-15.79, -48.06 em Goiânia)
✅ Quadras carregadas: Filtradas por proximidade
✅ Cache synced: Verde (< 5 minutos)
```

### Debug

```bash
# Terminal do app
[GPS] Obtained position: lat=-15.7942, lng=-48.0676, accuracy=5.0m

# Log esperado
[INFO] CourtListNotifier: GPS status = strong
```

---

## 📵 Teste 2: GPS Desligado

### Procedimento

1. Abra app em interior (sem GPS)
2. Desactive GPS nas configurações de dispositivo
3. Navegue para tela de quadras
4. Verifique BottomSheet educativo

### Validação

```
✅ GPS Status: Disabled (cinza)
✅ BottomSheet mostra: "GPS Desligado, Tendendo usar Novo Mundo"
✅ Botões: "Tentar Depois", "Abrir Configurações"
✅ Fallback automático: -15.7942, -48.0676
✅ Quadras carregadas mesmo sem GPS real
```

### Debug

```bash
# Log esperado
[INFO] LocationService: GPS service is disabled
[INFO] LocationService: Using fallback coordinates
```

---

## 🔒 Teste 3: Permissão Negada

### Procedimento

1. Desinstale app
2. Instale novamente
3. Navegue para GPS
4. Negue permissão quando solicitado
5. Tente acessar GPS novamente

### Validação

```
✅ Primeira tentativa: Permission denied → BottomSheet "Permitir Localização"
✅ Segunda tentativa: Pode pedir novamente
✅ Fallback para Novo Mundo enquanto nega
✅ Botão "Permitir Localização" refaz request
```

---

## 🔐 Teste 4: Permissão Negada Para Sempre

### Procedimento

1. Pedir localização (permissão negada)
2. Escolher "Não Mostrar Novamente" em Android
3. Tente acessar GPS novamente

### Validação

```
✅ BottomSheet diferente: "Permissão Negada Permanentemente"
✅ Botão: "Abrir Configurações do App"
✅ Clique abre: Settings > App > Permissions > Location
✅ Fallback continua funcionando
```

---

## 📱 Teste 5: Lifecycle (Background/Foreground)

### Procedimento

1. Abra app na tela de quadras
2. Veja GPS escutando (status verde, updating)
3. Pressione botão Home (app vai para background)
4. Espere 10 segundos
5. Volte para app
6. Verifique se GPS retomou

### Validação

```
✅ Em foreground: GPS ouvindo (isListeningToGPS = true)
✅ Em background: GPS parado (isListeningToGPS = false)
✅ Ao retornar: GPS retoma (isListeningToGPS = true)
✅ Bateria: não drena enquanto em background
```

### Debug - Battery Drain

```bash
# Android
adb shell dumpsys batterymanager

# Esperado quando em background:
# GPS: OFF (0%)
# quando em foreground: ON (<5%)
```

---

## 📊 Teste 6: Oscilação de Sinal

### Procedimento

1. Abra app em local com sinal fraco (próximo a janela, mas interior)
2. Observe status do GPS (pode alternar entre strong/weak/lost)
3. Saia para local com sinal forte
4. Verifique recuperação

### Validação

```
✅ Sinal fraco: Status muda para weak (amarelo)
✅ UI atualiza em tempo real
✅ Quadras refiltradas com novas coordenadas
✅ Sinal recuperado: Status volta para strong (verde)
```

---

## 📷 Teste 7: Câmera - Primeira Request

### Procedimento

1. Navegue para tela de upload de foto (se existe)
2. Clique em "Tirar Foto"
3. Aceite permissão quando solicitado

### Validação

```
✅ Dialog: "Permitir acesso à câmera?"
✅ Câmera abre sem delay
✅ Foto tirada com sucesso
✅ Upload funciona
```

---

## 📸 Teste 8: Câmera - Permissão Negada

### Procedimento

1. Navegue para upload de foto
2. Clique em "Tirar Foto"
3. Negue permissão
4. Tente novamente

### Validação

```
✅ Primeira tentativa: Nega → sem câmera
✅ Segunda tentativa: Pode pedir novamente
✅ Mensagem educativa: "Precisamos de acesso para tirar fotos"
```

---

## 🖼️ Teste 9: Galeria/Storage

### Procedimento

1. Navegue para upload de galeria
2. Clique em "Escolher Foto"
3. Aceite permissão
4. Selecione foto

### Validação

```
✅ Permission dialog aparece (Android 13+: READ_MEDIA_IMAGES)
✅ Galeria abre depois de aceitar
✅ Foto escolhida é carregada
✅ Upload funciona
```

---

## ⚡ Teste 10: Múltiplas Permissões

### Procedimento

1. Primeiro uso do app
2. Sistema pede: Localização + Câmera + Galeria (simultaneamente)
3. Aceite todas

### Validação

```
✅ Dialog único com múltiplas permissões
✅ Todas são solicitadas
✅ Todas funcionam depois
```

---

## 🔄 Teste 11: App Restart com Cache

### Procedimento

1. Abra app
2. Carregue quadras (GPS obtém localização)
3. Feche app (kill process)
4. Abra novamente

### Validação

```
✅ Quadras aparecem rapidamente (cache)
✅ GPS status mostra cache válido (< 30 min)
✅ Ícone de cache: Verde (fresco) → Amarelo (> 20 min) → Vermelho (> 30 min)
✅ Refetch automático ao atingir 30 minutos
```

---

## 🧪 Teste 12: Estresse - Múltiplos Toggles

### Procedimento

1. Ligue/desligue GPS 5 vezes rapídamente
2. Observe comportamento

### Validação

```
✅ App não crashes
✅ Status atualiza corretamente
✅ Cache mantém dados
✅ Fallback ativado quando perdido
✅ Recuperação automática quando ligado
```

---

## 📊 Checklist de Validação

| Teste | Aspecto | Status | Notas |
|-------|---------|--------|-------|
| 1 | GPS Strong | ⬜ | |
| 2 | GPS Disabled | ⬜ | |
| 3 | Permission Denied | ⬜ | |
| 4 | Permission Denied Forever | ⬜ | |
| 5 | Lifecycle Background | ⬜ | |
| 6 | Signal Oscillation | ⬜ | |
| 7 | Camera First Request | ⬜ | |
| 8 | Camera Permission Denied | ⬜ | |
| 9 | Gallery/Storage | ⬜ | |
| 10 | Multiple Permissions | ⬜ | |
| 11 | App Restart + Cache | ⬜ | |
| 12 | Stress - Multiple Toggles | ⬜ | |

---

## 🐛 Debugging - Ferramentas

### Android Studio

```bash
# Abrir logcat
flutter logs

# Filtrar apenas app
flutter logs | grep "matching_esportivo"
```

### Simulação de GPS no Emulador

```bash
# Abrir emulador
emulator -avd <device_name>

# Via Android Studio:
# Tools > Device Manager > Extended Controls > Location
# Insira: Latitude -15.7942, Longitude -48.0676

# Ou via terminal:
telnet localhost 5554
geo fix -48.0676 -15.7942 100
```

### iOS Simulator

```bash
# Abrir Simulator
open -a Simulator

# Simulação via Xcode:
# Xcode > Schemes > Edit Schemes > Run > Pre-actions
# Adicionar script para mock location
```

---

## 📋 Relatório Template

```markdown
# Teste de Hardware - Matching Esportivo
Data: ___________
Dispositivo: ___________
OS: ___________
Build: ___________

## Resultados

### GPS
- [x] Sinal Forte: ✅ PASS / ❌ FAIL
- [x] GPS Desligado: ✅ PASS / ❌ FAIL
- [x] Permissão Negada: ✅ PASS / ❌ FAIL
- [x] Permissão Negada Forever: ✅ PASS / ❌ FAIL
- [x] Lifecycle: ✅ PASS / ❌ FAIL
- [x] Oscilação Sinal: ✅ PASS / ❌ FAIL

### Câmera
- [x] Primeira Request: ✅ PASS / ❌ FAIL
- [x] Permissão Negada: ✅ PASS / ❌ FAIL

### Galeria
- [x] Storage Request: ✅ PASS / ❌ FAIL

### Permissões Múltiplas
- [x] Multi Request: ✅ PASS / ❌ FAIL

### Cache & Restart
- [x] App Restart: ✅ PASS / ❌ FAIL

### Estresse
- [x] Multiple Toggles: ✅ PASS / ❌ FAIL

## Issues Encontrados
- (nenhum)

## Performance
- Bateria: ___% (after 1 hour)
- GPS Lag: ___ms average
- Cache Hit: ___%

## Notas
```

---

## 🎯 Resultado Esperado

Se todos os testes passarem:

```
✅ GPS Funciona em todas as condições
✅ Permissões pedidas corretamente
✅ Fallback para Novo Mundo quando necessário
✅ Bateria economizada em background
✅ App não crashes em nenhum cenário
✅ Cache funciona entre sessions
✅ BottomSheets educativos aparecem no momento certo

🟢 PRONTO PARA APP STORE / PLAY STORE
```

---

## 🚀 Próximas Fases

Após validar em dispositivo real:

1. **Play Store:** Enviar com todos os tests passando
2. **iOS App Store:** Adicionar NSLocationWhenInUseUsageDescription
3. **Beta:** Convidar 10 users para beta testing
4. **Megaprompt 3:** UX Fluida (animações, transições)

---

**Happy testing! 🎉**
