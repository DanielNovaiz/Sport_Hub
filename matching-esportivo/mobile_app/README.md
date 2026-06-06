# Matching Esportivo Mobile

Aplicativo Flutter/Dart do projeto Matching Esportivo.

## Stack

- Flutter 3.22+
- Provider para estado global
- GetIt para injeção de dependências
- Dio para HTTP
- SharedPreferences e storage local para cache

## Estrutura principal

- `lib/main.dart` - bootstrap do app, rotas e providers globais
- `lib/service_locator.dart` - registro das dependências
- `lib/core/` - tema, ambiente, autenticação, cache e serviços comuns
- `lib/data/` - modelos e integrações com API/local storage
- `lib/presentation/` - telas, providers e widgets

## Execução

1. Instale as dependências com `flutter pub get`.
2. Rode a aplicação com `flutter run`.
3. Execute os testes com `flutter test`.

## Observação

O app usa o backend FastAPI do diretório `matching-esportivo/` como origem de dados.
