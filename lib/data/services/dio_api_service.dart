import 'dart:io';

import 'package:dio/dio.dart';
import 'package:dio/io.dart';
import 'package:flutter/foundation.dart';

import '../../core/app_environment.dart';
import '../../core/app_exception.dart';
import '../models/court.dart';
import '../models/player_stats.dart';
import 'api_service.dart';
import 'auth_token_provider.dart';

class DioApiService implements ApiService {
  final Dio _dio;
  final AuthTokenProvider _tokenProvider;

  DioApiService(
    this._dio,
    this._tokenProvider,
  ) {
    _dio.options.baseUrl = AppEnvironment.apiBaseUrl;
    _dio.options.connectTimeout = const Duration(seconds: 10);
    _dio.options.receiveTimeout = const Duration(seconds: 10);

    _configureSecurity();
    _setupInterceptors();
  }

  void _configureSecurity() {
    if (kIsWeb) return;

    // Base preparada para SSL pinning por certificado SHA256/public key pin.
    // Ativar com --dart-define=ENABLE_SSL_PINNING=true
    if (!AppEnvironment.enableSslPinning) return;

    final adapter = IOHttpClientAdapter(
      createHttpClient: () {
        final client = HttpClient();

        // NOTE: placeholder para pinning real.
        // Em produção, implemente validação de fingerprint/certificado aqui.
        client.badCertificateCallback = (cert, host, port) {
          // Rejeita certificados inválidos por padrão.
          return false;
        };

        return client;
      },
    );

    _dio.httpClientAdapter = adapter;
  }

  void _setupInterceptors() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          options.headers['Content-Type'] = 'application/json';
          options.headers['Accept'] = 'application/json';

          final token = await _tokenProvider.getAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }

          if (kDebugMode && AppEnvironment.enableDebugNetworkLogs) {
            debugPrint(
              '[DIO][REQ] ${options.method} ${options.baseUrl}${options.path} '
              'headers=${options.headers} query=${options.queryParameters} '
              'body=${options.data}',
            );
          }

          handler.next(options);
        },
        onResponse: (response, handler) {
          if (kDebugMode && AppEnvironment.enableDebugNetworkLogs) {
            debugPrint(
              '[DIO][RES] ${response.statusCode} ${response.requestOptions.method} '
              '${response.requestOptions.baseUrl}${response.requestOptions.path} '
              'data=${response.data}',
            );
          }

          handler.next(response);
        },
        onError: (error, handler) {
          if (kDebugMode && AppEnvironment.enableDebugNetworkLogs) {
            debugPrint(
              '[DIO][ERR] ${error.requestOptions.method} '
              '${error.requestOptions.baseUrl}${error.requestOptions.path} '
              'message=${error.message} status=${error.response?.statusCode}',
            );
          }

          handler.next(error);
        },
      ),
    );
  }

  @override
  Future<PlayerStats> getPlayerStats(String playerId) async {
    try {
      final response = await _dio.get('/players/$playerId/stats');
      final json = _validatedJsonMap(
        response.data,
        requiredKeys: const ['id', 'name', 'position'],
      );
      return PlayerStats.fromJson(json);
    } on DioException catch (e, s) {
      throw ApiException(
        'Não foi possível buscar as estatísticas do jogador.',
        debugMessage: e.message,
        stackTrace: s,
        cause: e,
      );
    }
  }

  @override
  Future<PlayerStatsResponse> getAllPlayerStats() async {
    try {
      final response = await _dio.get('/players/stats');
      final json = _validatedJsonMap(
        response.data,
        requiredKeys: const ['stats', 'fetchedAt'],
      );
      if (json['stats'] is! List) {
        throw ApiException(
          'Resposta inválida do servidor.',
          debugMessage: 'Campo "stats" não é lista.',
        );
      }
      return PlayerStatsResponse.fromJson(json);
    } on DioException catch (e, s) {
      throw ApiException(
        'Não foi possível buscar as estatísticas dos jogadores.',
        debugMessage: e.message,
        stackTrace: s,
        cause: e,
      );
    }
  }

  @override
  Future<PlayerStats> updatePlayerStats(
    String playerId,
    Map<String, dynamic> updates,
  ) async {
    try {
      final response = await _dio.patch(
        '/players/$playerId/stats',
        data: updates,
      );
      final json = _validatedJsonMap(
        response.data,
        requiredKeys: const ['id', 'name', 'position'],
      );
      return PlayerStats.fromJson(json);
    } on DioException catch (e, s) {
      throw ApiException(
        'Não foi possível atualizar as estatísticas do jogador.',
        debugMessage: e.message,
        stackTrace: s,
        cause: e,
      );
    }
  }

  @override
  Future<CourtsResponse> getAvailableCourts({
    double? latitude,
    double? longitude,
    String? sport,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        if (latitude != null) 'latitude': latitude,
        if (longitude != null) 'longitude': longitude,
        if (sport != null) 'sport': sport,
      };

      final response = await _dio.get(
        '/courts/available',
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      final json = _validatedJsonMap(
        response.data,
        requiredKeys: const ['courts', 'fetchedAt'],
      );
      if (json['courts'] is! List) {
        throw ApiException(
          'Resposta inválida do servidor.',
          debugMessage: 'Campo "courts" não é lista.',
        );
      }
      return CourtsResponse.fromJson(json);
    } on DioException catch (e, s) {
      throw ApiException(
        'Não foi possível buscar as quadras disponíveis.',
        debugMessage: e.message,
        stackTrace: s,
        cause: e,
      );
    }
  }

  @override
  Future<Court> getCourtDetails(String courtId) async {
    try {
      final response = await _dio.get('/courts/$courtId');
      final json = _validatedJsonMap(
        response.data,
        requiredKeys: const ['id', 'name', 'location', 'sport'],
      );
      return Court.fromJson(json);
    } on DioException catch (e, s) {
      throw ApiException(
        'Não foi possível buscar os detalhes da quadra.',
        debugMessage: e.message,
        stackTrace: s,
        cause: e,
      );
    }
  }

  @override
  Future<Court> updateCourtSlots(String courtId, int availableSlots) async {
    try {
      final response = await _dio.patch(
        '/courts/$courtId/slots',
        data: {'availableSlots': availableSlots},
      );
      final json = _validatedJsonMap(
        response.data,
        requiredKeys: const ['id', 'availableSlots', 'totalSlots'],
      );
      return Court.fromJson(json);
    } on DioException catch (e, s) {
      throw ApiException(
        'Não foi possível atualizar as vagas da quadra.',
        debugMessage: e.message,
        stackTrace: s,
        cause: e,
      );
    }
  }

  Map<String, dynamic> _validatedJsonMap(
    Object? data, {
    required List<String> requiredKeys,
  }) {
    if (data is! Map<String, dynamic>) {
      throw ApiException(
        'Resposta inválida do servidor.',
        debugMessage: 'Payload não é um JSON objeto.',
      );
    }

    for (final key in requiredKeys) {
      if (!data.containsKey(key) || data[key] == null) {
        throw ApiException(
          'Resposta inválida do servidor.',
          debugMessage: 'Payload corrompido: chave ausente "$key".',
        );
      }
    }

    return data;
  }
}
