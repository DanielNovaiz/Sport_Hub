param(
  [string]$Flavor = "prod",
  [string]$DevBaseUrl = "https://api-dev.matching-esportivo.local/v1",
  [string]$ProdBaseUrl = "https://api.matching-esportivo.com/v1",
  [string]$DebugInfoDir = "build\app\outputs\symbols"
)

$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
  param([string]$Step)
  if ($LASTEXITCODE -ne 0) {
    throw "Falha no passo: $Step (exit code: $LASTEXITCODE)"
  }
}

Write-Host "==> Flutter clean"
flutter clean
Assert-LastExitCode -Step "Flutter clean"

Write-Host "==> Flutter pub get"
flutter pub get
Assert-LastExitCode -Step "Flutter pub get"

Write-Host "==> Flutter analyze"
flutter analyze
Assert-LastExitCode -Step "Flutter analyze"

Write-Host "==> Build APK release (obfuscate + split-debug-info)"
flutter build apk --release `
  --obfuscate `
  --split-debug-info="$DebugInfoDir" `
  --dart-define=APP_FLAVOR=$Flavor `
  --dart-define=API_BASE_URL_DEV=$DevBaseUrl `
  --dart-define=API_BASE_URL_PROD=$ProdBaseUrl `
  --dart-define=ENABLE_DEBUG_NETWORK_LOGS=false `
  --dart-define=ENABLE_SSL_PINNING=true
Assert-LastExitCode -Step "Build APK release"

Write-Host "Build concluído com sucesso."