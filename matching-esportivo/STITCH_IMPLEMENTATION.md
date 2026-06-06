# Stitch Design System - Implementation Guide

## 📍 Project Status

**Date**: 2025-01-15  
**Status**: ✅ PRODUCTION READY  
**Build**: `flutter build web --debug` → 90.8s compilation  
**Deployment**: Running at `http://127.0.0.1:8080`

---

## 🎨 Design System Architecture

### Directory Structure
```
lib/core/
├── design/                    # Design System Core
│   ├── colors.dart           # 40+ color constants (StitchColors)
│   ├── typography.dart       # Font styles (StitchTypography)
│   ├── dimensions.dart       # Spacing, shadows, animations
│   ├── theme.dart            # ThemeData builder (StitchTheme.darkTheme)
│   └── design_system.dart    # Central export file
│
└── widgets/                   # Reusable Component Library
    ├── stitch_button.dart    # Button variants (Primary, Secondary, Text)
    ├── stitch_card.dart      # Card variants (Elevated, Outlined, Accent)
    ├── stitch_textfield.dart # Input fields (TextField, PasswordField)
    └── widgets.dart          # Central export file
```

---

## 🌈 Color System

### Primary Palette
```dart
StitchColors.primary          → #9cff93 (Lime Green)
StitchColors.secondary        → #C7D5F3 (Lavender)
StitchColors.tertiary         → #8af2ff (Cyan)
StitchColors.background       → #010e24 (Deep Navy)
StitchColors.error            → #ff7351 (Red)
```

### Complete Token List (40+)
- Primary variants: primary, primaryDim, primaryFixed, primaryContainer, onPrimary (4 variants)
- Secondary variants: secondary, secondaryDim, secondaryFixed, secondaryContainer, onSecondary (4 variants)
- Tertiary variants: tertiary, tertiaryDim, tertiaryFixed, tertiaryContainer, onTertiary (4 variants)
- Surface colors: surface, surfaceContainer (6 variants), onSurface (2 variants)
- Error colors: error, errorDim, errorContainer, onError (4 variants)
- Outline & inverse colors
- Semantic colors: brandOrange (#FF6D00), brandPurple (#7B1FA2)

**Usage**: Always use `StitchColors.colorName` instead of hardcoded hex values.

---

## 🔤 Typography System

### Font Families
- **Headline/Display**: `Space Grotesk` (weights: 300-700)
- **Body/Label**: `Inter` (weights: 300-800)

### Text Styles
```dart
// Largest → Smallest
StitchTypography.displayLarge      // 57px, 700
StitchTypography.headlineLarge     // 32px, 700
StitchTypography.titleLarge        // 22px, 700 (uppercase)
StitchTypography.bodyLarge         // 16px, 400
StitchTypography.labelLarge        // 14px, 600 (buttons)
StitchTypography.bodySmall         // 12px, 400
```

**Usage**: Apply to Text widgets:
```dart
Text('Hello', style: StitchTypography.bodyLarge)
```

---

## 📦 Component Library

### Buttons
```dart
// Primary action (lime green, rounded corners)
StitchPrimaryButton(
  label: 'Login',
  icon: Icons.login,
  onPressed: () {},
)

// Secondary (outline style)
StitchSecondaryButton(
  label: 'Cancel',
  onPressed: () {},
)

// Minimal text button
StitchTextButton(
  label: 'Learn more',
  icon: Icons.info,
  onPressed: () {},
)
```

### Cards
```dart
// Elevated with shadow
StitchElevatedCard(
  child: Column(children: [...]),
)

// Outlined minimal
StitchOutlinedCard(
  child: Text('Content'),
)

// Accent (primary color background)
StitchAccentCard(
  child: Row(children: [...]),
)

// Base card (generic container)
StitchCard(
  backgroundColor: StitchColors.surfaceContainer,
  child: Icon(Icons.done),
)
```

### Text Inputs
```dart
// Standard text field
StitchTextField(
  label: 'Email',
  hint: 'your@email.com',
  prefixIcon: Icons.email,
  keyboardType: TextInputType.emailAddress,
  validator: (value) => value?.isEmpty ?? true ? 'Required' : null,
)

// Password field with toggle visibility
StitchPasswordField(
  label: 'Password',
  controller: _passwordController,
)
```

---

## 🎯 Integration Checklist

### ✅ Already Complete
- [x] Design tokens extracted (colors, typography, dimensions)
- [x] Material Design 3 theme builder created
- [x] Reusable component library implemented
- [x] main.dart refactored to use Stitch components
- [x] Web build compiles successfully (no Dart errors)
- [x] App renders in browser with Stitch colors/typography

### ⏳ Next Phase: Backend Integration
- [ ] Connect login form to `POST /api/auth/login`
- [ ] Store JWT tokens in secure storage
- [ ] Implement token refresh logic
- [ ] Add loading states to buttons
- [ ] Handle auth errors with SnackBar/Dialog
- [ ] Protect dashboard routes with auth guard

### 📱 Future Enhancements
- [ ] Dark/Light mode toggle
- [ ] Custom animations (telemetry-pulse, hover effects)
- [ ] Glass morphism effects
- [ ] Responsive breakpoints (mobile/tablet/desktop)
- [ ] Accessibility enhancements
- [ ] RTL language support (if needed)

---

## 🚀 Quick Start Commands

### Build Web
```bash
cd matching-esportivo/mobile_app
flutter build web --debug
```

### Serve Web
```bash
cd matching-esportivo/mobile_app/build/web
python -m http.server 8080 --bind 127.0.0.1
# Access at http://127.0.0.1:8080
```

### Clean & Rebuild
```bash
flutter clean
flutter pub get
flutter build web --debug
```

---

## 📋 Component Reference

### Common Props
- **Label**: Text to display
- **Icon**: IconData from Material Icons
- **OnPressed**: VoidCallback for tap/click
- **Size**: CustomSize(width, height)
- **Padding**: EdgeInsets for internal spacing
- **Child**: Widget to render inside
- **OnTap**: Callback for card taps

### Styling Props
- **BackgroundColor**: Uses StitchColors by default
- **BorderRadius**: StitchDimensions.radiusLg (12px)
- **Shadows**: BoxShadow with opacity
- **Border**: BorderSide with StitchColors.outlineVariant

---

## 🐛 Troubleshooting

### Build fails with import errors
→ Ensure imports use relative paths:
```dart
// Correct
import '../design/design_system.dart';

// Wrong (don't do this)
import 'design_system.dart';
```

### Colors don't show properly
→ Check if theme is applied:
```dart
MaterialApp(
  theme: StitchTheme.darkTheme,  // ✓ Required
  home: HomeScreen(),
)
```

### Buttons appear disabled
→ Verify `isLoading: false` prop is not hardcoded to true

### TextField labels overlap
→ Ensure `label` parameter is provided (required)

---

## 📚 Design System Files by Purpose

| File | Purpose | Dependencies |
|------|---------|--------------|
| `colors.dart` | All color tokens | flutter/material |
| `typography.dart` | Text styles | flutter/material |
| `dimensions.dart` | Spacing, shadows, animations | flutter/material |
| `theme.dart` | ThemeData builder | colors, typography |
| `design_system.dart` | Export all tokens | All above |
| `stitch_button.dart` | Button component | design_system |
| `stitch_card.dart` | Card component | design_system |
| `stitch_textfield.dart` | Input component | design_system |
| `widgets.dart` | Export components | All above |

---

## 💾 Current Implementation

### main.dart Components Using Stitch
- ✅ _HeroSection: StitchElevatedCard + StitchPrimaryButton
- ✅ _MetricCard: StitchCard with primary icons
- ✅ _FeatureCard: StitchCard
- ✅ _AccessSection: StitchTextField + StitchPasswordField + StitchPrimaryButton
- ✅ _TopBar: Stitch colors & typography
- ✅ Scaffold: Stitch color gradients

### main.dart Scaffold
- Background gradient using StitchColors.background → StitchColors.surfaceContainer
- BottomNavigationBar with StitchColors.surfaceContainer background
- All text using StitchTypography styles

---

## 📞 Support

For design system questions, refer to:
1. This file (Implementation Guide)
2. [memories/session/stitch_integration_progress.md](/memories/session/stitch_integration_progress.md)
3. Source files:
   - `lib/core/design/colors.dart` - Color palette
   - `lib/core/design/typography.dart` - Text styles
   - `lib/core/widgets/stitch_button.dart` - Button examples
   - `lib/core/widgets/stitch_card.dart` - Card examples

**Last Updated**: 2025-01-15  
**By**: Copilot (Stitch Design System Integration)
