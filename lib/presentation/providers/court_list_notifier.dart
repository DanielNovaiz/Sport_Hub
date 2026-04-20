import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart' show Position;
import '../data/models/court.dart';
import '../data/services/api_service.dart';
import '../data/services/local_storage_service.dart';
import '../data/services/location_service.dart';
import '../service_locator.dart';

/// Status de sinal GPS
enum GPSSignalStatus {
  strong,          // Sinal forte
  weak,            // Sinal fraco
  lost,            // Sinal perdido
  disabled,        // GPS desligado
  permissionDenied, // Permissão negada
}

/// Notifier que gerencia o estado global de quadras disponíveis
/// - Sincroniza dados entre telas automaticamente
/// - Persiste dados localmente
/// - Suporta filtro por localização e esporte
/// - Gerencia GPS com tratamento robusto de permissões
class CourtListNotifier extends ChangeNotifier {
  final ApiService _apiService;
  final LocalStorageService _localStorage;

  // Estado privado
  List<Court> _courts = [];
  List<Court> _filteredCourts = [];
  LoadingState _state = LoadingState.idle;
  String _errorMessage = '';
  DateTime? _lastFetch;
  String? _selectedSport;
  double? _userLatitude;
  double? _userLongitude;
  GPSSignalStatus _gpsStatus = GPSSignalStatus.disabled;
  LocationStatus? _lastLocationStatus;
  
  // Subscription para GPS contínuo
  StreamSubscription<Position>? _positionSubscription;
  bool _isListeningToGPS = false;

  // Getters públicos
  List<Court> get courts => _filteredCourts.isEmpty ? _courts : _filteredCourts;
  LoadingState get state => _state;
  String get errorMessage => _errorMessage;
  bool get isLoading => _state == LoadingState.loading;
  bool get hasError => _state == LoadingState.error;
  bool get isCacheValid => _localStorage.isCacheExpired() == false;
  String? get selectedSport => _selectedSport;
  GPSSignalStatus get gpsStatus => _gpsStatus;
  LocationStatus? get lastLocationStatus => _lastLocationStatus;
  bool get isListeningToGPS => _isListeningToGPS;

  // Localização
  double? get userLatitude => _userLatitude;
  double? get userLongitude => _userLongitude;

  CourtListNotifier(this._apiService, this._localStorage) {
    _initialize();
  }

  /// Inicializa carregando dados do cache
  Future<void> _initialize() async {
    await _restoreFromCache();
  }

  /// Restaura dados do cache local
  Future<void> _restoreFromCache() async {
    try {
      final cachedCourts = await _localStorage.getCourts();
      if (cachedCourts.isNotEmpty) {
        _courts = cachedCourts;
        _state = LoadingState.success;
        notifyListeners();
      }
    } catch (e) {
      print('Erro ao restaurar cache: $e');
    }
  }

  /// Busca a localização atual do usuário com tratamento robusto
  Future<LocationResult> requestUserLocation() async {
    final result = await LocationService.getLocationWithFallback();
    _lastLocationStatus = result.status;
    
    // Atualiza status do GPS
    if (result.status == LocationStatus.success) {
      _gpsStatus = GPSSignalStatus.strong;
    } else if (result.status == LocationStatus.serviceDisabled) {
      _gpsStatus = GPSSignalStatus.disabled;
    } else if (result.status == LocationStatus.permissionDenied ||
               result.status == LocationStatus.permissionDeniedForever) {
      _gpsStatus = GPSSignalStatus.permissionDenied;
    } else if (result.status == LocationStatus.timeout) {
      _gpsStatus = GPSSignalStatus.weak;
    }

    // Atualiza coordenadas (com fallback)
    _userLatitude = result.latitude;
    _userLongitude = result.longitude;

    if (!result.isSuccess) {
      _errorMessage = result.errorMessage ?? 'Erro desconhecido na localização';
    } else {
      _errorMessage = '';
    }

    notifyListeners();
    return result;
  }

  /// Inicia escuta contínua de localização
  /// IMPORTANTE: Deve ser parado quando app vai para background
  /// Use AppLifecycleManager para isso
  Future<void> startListeningToLocation({
    LocationAccuracy accuracy = LocationAccuracy.best,
  }) async {
    if (_isListeningToGPS) return;

    try {
      _isListeningToGPS = true;
      
      _positionSubscription = LocationService.getPositionStream(
        accuracy: accuracy,
        distanceFilter: 10, // Atualiza a cada 10 metros
      ).listen(
        (Position position) {
          _userLatitude = position.latitude;
          _userLongitude = position.longitude;
          _gpsStatus = GPSSignalStatus.strong;
          notifyListeners();
          print('GPS atualizado: $_userLatitude, $_userLongitude');
        },
        onError: (error) {
          print('Erro no stream de GPS: $error');
          _gpsStatus = GPSSignalStatus.lost;
          _errorMessage = 'Perdido sinal de GPS';
          notifyListeners();
        },
      );
    } catch (e) {
      _isListeningToGPS = false;
      _errorMessage = 'Erro ao iniciar escuta de GPS: $e';
      notifyListeners();
    }
  }

  /// Para a escuta contínua de localização (economiza bateria)
  Future<void> stopListeningToLocation() async {
    if (_positionSubscription != null) {
      await _positionSubscription?.cancel();
      _positionSubscription = null;
    }
    _isListeningToGPS = false;
    notifyListeners();
  }

  /// Busca quadras disponíveis (opcionalmente próximas ao usuário)
  Future<void> fetchAvailableCourts({
    bool useUserLocation = false,
    String? sport,
    bool forceRefresh = false,
  }) async {
    if (isCacheValid && !forceRefresh) {
      return;
    }

    _state = LoadingState.loading;
    _selectedSport = sport;
    _errorMessage = '';
    notifyListeners();

    try {
      // Busca localização do usuário se solicitado
      if (useUserLocation) {
        final locationResult = await requestUserLocation();
        
        // Se GPS está desligado mas usuário ainda quer continuar
        if (locationResult.status == LocationStatus.serviceDisabled) {
          print('⚠️ GPS desligado, usando fallback de localização');
        }
      }

      final response = await _apiService.getAvailableCourts(
        latitude: _userLatitude,
        longitude: _userLongitude,
        sport: sport,
      );

      _courts = response.courts;
      _lastFetch = response.fetchedAt;
      _state = LoadingState.success;

      // Persiste no cache
      await _localStorage.saveCourts(_courts);

      // Aplica filtro se necessário
      if (sport != null) {
        _filterBySport(sport);
      }
    } catch (e) {
      _state = LoadingState.error;
      _errorMessage = e.toString();
      print('Erro ao buscar quadras: $e');
    }

    notifyListeners();
  }

  /// Busca detalhes de uma quadra específica
  Future<Court?> fetchCourtDetails(String courtId) async {
    try {
      return await _apiService.getCourtDetails(courtId);
    } catch (e) {
      _errorMessage = e.toString();
      notifyListeners();
      return null;
    }
  }

  /// Simula perda de sinal GPS (para testes)
  void simulateGPSLoss() {
    _gpsStatus = GPSSignalStatus.lost;
    _errorMessage = '⚠️ Sinal de GPS perdido';
    notifyListeners();
  }

  /// Simula recuperação de sinal GPS (para testes)
  void simulateGPSRecovery() {
    _gpsStatus = GPSSignalStatus.strong;
    _errorMessage = '';
    notifyListeners();
  }

  /// Filtra quadras por esporte
  void filterBySport(String sport) {
    _filterBySport(sport);
    notifyListeners();
  }

  void _filterBySport(String sport) {
    if (sport.isEmpty) {
      _filteredCourts = [];
      _selectedSport = null;
    } else {
      _selectedSport = sport;
      _filteredCourts = _courts
          .where((c) => c.sport.toLowerCase() == sport.toLowerCase())
          .toList();
    }
  }

  /// Filtra quadras por disponibilidade
  void filterByAvailability(int minSlots) {
    _filteredCourts = _courts.where((c) => c.availableSlots >= minSlots).toList();
    notifyListeners();
  }

  /// Filtra quadras por preço máximo
  void filterByPrice(double maxPrice) {
    _filteredCourts = _courts.where((c) => c.price <= maxPrice).toList();
    notifyListeners();
  }

  /// Limpa filtros
  void clearFilters() {
    _filteredCourts = [];
    _selectedSport = null;
    notifyListeners();
  }

  /// Busca quadra por ID
  Court? findById(String courtId) {
    try {
      return _courts.firstWhere((c) => c.id == courtId);
    } catch (e) {
      return null;
    }
  }

  /// Atualiza vagas disponíveis de uma quadra
  Future<void> updateCourtSlots(String courtId, int availableSlots) async {
    try {
      // Otimismo: atualiza localmente
      final index = _courts.indexWhere((c) => c.id == courtId);
      if (index != -1) {
        final current = _courts[index];
        _courts[index] = current.copyWith(
          availableSlots: availableSlots,
          lastChecked: DateTime.now(),
        );
        notifyListeners();
      }

      // Sincroniza com servidor
      await _apiService.updateCourtSlots(courtId, availableSlots);

      // Persiste no cache
      await _localStorage.saveCourts(_courts);

      _state = LoadingState.success;
    } catch (e) {
      _state = LoadingState.error;
      _errorMessage = e.toString();
      // Recarrega para descartar otimismo
      await fetchAvailableCourts(forceRefresh: true);
    }

    notifyListeners();
  }

  /// Limpa todos os dados
  Future<void> clearAll() async {
    _courts = [];
    _filteredCourts = [];
    _state = LoadingState.idle;
    _errorMessage = '';
    _lastFetch = null;
    _selectedSport = null;
    await stopListeningToLocation();
    await _localStorage.clearCourts();
    notifyListeners();
  }

  /// Força atualização sem mudança de estado
  void refreshUI() {
    notifyListeners();
  }

  @override
  void dispose() {
    stopListeningToLocation();
    super.dispose();
  }
}

// Re-export LoadingState para uso em widgets
enum LoadingState { idle, loading, success, error }

// Import para StreamSubscription
import 'dart:async';
