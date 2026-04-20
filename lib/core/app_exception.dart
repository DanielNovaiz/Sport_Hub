import 'package:flutter/foundation.dart';

class AppException implements Exception {
  final String userMessage;
  final String? debugMessage;
  final StackTrace? stackTrace;
  final Object? cause;

  AppException(
    this.userMessage, {
    this.debugMessage,
    this.stackTrace,
    this.cause,
  }) {
    _log();
  }

  void _log() {
    final buffer = StringBuffer()
      ..writeln('[AppException] $userMessage');

    if (debugMessage != null && debugMessage!.isNotEmpty) {
      buffer.writeln('[debug] $debugMessage');
    }

    if (cause != null) {
      buffer.writeln('[cause] $cause');
    }

    if (stackTrace != null) {
      buffer.writeln('[stackTrace]');
      buffer.writeln(stackTrace.toString());
    }

    debugPrint(buffer.toString());
  }

  @override
  String toString() => userMessage;
}

class ApiException extends AppException {
  ApiException(
    super.userMessage, {
    super.debugMessage,
    super.stackTrace,
    super.cause,
  });
}
