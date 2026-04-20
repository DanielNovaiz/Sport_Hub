import 'package:flutter/material.dart';
import 'app_colors.dart';

class AppTheme {
  static ThemeData get kineticTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.surface,
      
      // Aplicando a regra "Don't use pill buttons" - Cantos de 4px (0.25rem)
      cardTheme: CardTheme(
        color: AppColors.surfaceContainer,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
      ),

      // Botões Técnicos e Agressivos
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primaryNeon,
          foregroundColor: AppColors.surface,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
          textStyle: const TextStyle(fontWeight: FontWeight.bold, letterSpacing: -0.02),
        ),
      ),

      // Configuração de cores global
      colorScheme: const ColorScheme.dark(
        surface: AppColors.surface,
        primary: AppColors.primaryNeon,
        secondary: AppColors.primaryContainer,
        onSurface: AppColors.onSurface,
      ),
    );
  }
}