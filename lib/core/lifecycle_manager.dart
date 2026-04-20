import 'package:flutter/material.dart';
import 'package:app_lifecycle/app_lifecycle.dart';

/// Estados do ciclo de vida da aplicação
enum AppLifecycleStateEnum {
  resumed,   // App em foreground e visível
  paused,    // App em background ou parcialmente obscurecido
  detached,  // App desanexado
}

/// Callback para mudanças no ciclo de vida
typedef AppLifecycleCallback = void Function(AppLifecycleStateEnum state);

/// Gerencia o ciclo de vida da aplicação
/// Usado para parar de escutar sensores quando app vai para background
class AppLifecycleManager extends WidgetsBindingObserver {
  static final AppLifecycleManager _instance = AppLifecycleManager._internal();

  factory AppLifecycleManager() {
    return _instance;
  }

  AppLifecycleManager._internal() {
    WidgetsBinding.instance.addObserver(this);
  }

  // Callbacks registrados
  final List<AppLifecycleCallback> _callbacks = [];
  AppLifecycleStateEnum _currentState = AppLifecycleStateEnum.paused;

  AppLifecycleStateEnum get currentState => _currentState;

  bool get isResumed => _currentState == AppLifecycleStateEnum.resumed;
  bool get isPaused => _currentState == AppLifecycleStateEnum.paused;

  /// Registra um callback para mudanças no ciclo de vida
  void addListener(AppLifecycleCallback callback) {
    if (!_callbacks.contains(callback)) {
      _callbacks.add(callback);
    }
  }

  /// Remove um callback
  void removeListener(AppLifecycleCallback callback) {
    _callbacks.remove(callback);
  }

  /// Notifica todos os listeners
  void _notifyListeners() {
    for (final callback in _callbacks) {
      callback(_currentState);
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final newState = _mapState(state);
    if (_currentState != newState) {
      _currentState = newState;
      print('AppLifecycle changed to: $newState');
      _notifyListeners();
    }
  }

  AppLifecycleStateEnum _mapState(AppLifecycleState state) {
    switch (state) {
      case AppLifecycleState.resumed:
        return AppLifecycleStateEnum.resumed;
      case AppLifecycleState.paused:
        return AppLifecycleStateEnum.paused;
      case AppLifecycleState.detached:
        return AppLifecycleStateEnum.detached;
      case AppLifecycleState.inactive:
        return AppLifecycleStateEnum.paused;
      case AppLifecycleState.hidden:
        return AppLifecycleStateEnum.paused;
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _callbacks.clear();
    super.dispose();
  }
}

/// Mixin para widgets que precisam reagir ao ciclo de vida do app
/// Use em State<T> para automaticamente registrar/remover listeners
mixin AppLifecycleAware<T extends StatefulWidget> on State<T> {
  late AppLifecycleManager _lifecycleManager;

  @override
  void initState() {
    super.initState();
    _lifecycleManager = AppLifecycleManager();
    _lifecycleManager.addListener(_onLifecycleChange);
  }

  @override
  void dispose() {
    _lifecycleManager.removeListener(_onLifecycleChange);
    super.dispose();
  }

  /// Chamado quando o ciclo de vida da app muda
  /// Override em subclasses para reagir
  void onAppResumed() {}
  void onAppPaused() {}
  void onAppDetached() {}

  void _onLifecycleChange(AppLifecycleStateEnum state) {
    switch (state) {
      case AppLifecycleStateEnum.resumed:
        onAppResumed();
        break;
      case AppLifecycleStateEnum.paused:
        onAppPaused();
        break;
      case AppLifecycleStateEnum.detached:
        onAppDetached();
        break;
    }
  }
}

/// Controlador de sensores que respeita o ciclo de vida do app
abstract class SensorLifecycleController {
  /// Inicia a escuta do sensor
  Future<void> start();

  /// Para a escuta do sensor (chamado automaticamente no background)
  Future<void> stop();

  /// Verifica se o sensor está ativo
  bool get isActive;
}

/// Implementação base com suporte automático a ciclo de vida
abstract class BaseSensorLifecycleController implements SensorLifecycleController {
  late AppLifecycleManager _lifecycleManager;
  bool _isActive = false;

  @override
  bool get isActive => _isActive;

  BaseSensorLifecycleController() {
    _lifecycleManager = AppLifecycleManager();
    _lifecycleManager.addListener(_onLifecycleChange);
  }

  Future<void> _onLifecycleChange(AppLifecycleStateEnum state) async {
    switch (state) {
      case AppLifecycleStateEnum.resumed:
        // App voltou ao foreground - retoma sensores
        if (!_isActive) {
          await start();
        }
        break;
      case AppLifecycleStateEnum.paused:
        // App foi para background - pausa sensores (economiza bateria)
        if (_isActive) {
          await stop();
        }
        break;
      case AppLifecycleStateEnum.detached:
        // App está sendo destruído
        if (_isActive) {
          await stop();
        }
        break;
    }
  }

  void dispose() {
    _lifecycleManager.removeListener(_onLifecycleChange);
  }
}
