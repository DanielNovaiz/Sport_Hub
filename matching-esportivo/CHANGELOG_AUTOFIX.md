# CHANGELOG_AUTOFIX

## 2026-04-15 — Hardening Arquitetural, Segurança e Resiliência

### 1) Consolidação de Arquitetura & Sub-Modelos
- Criado `app/services/overall_engine.py` como motor **unificado e assíncrono** de overall (`calculate_overall_async`) cobrindo:
  - Futebol (`futsal`, `society`, `field`),
  - Basquete (`3x3`),
  - Vôlei (`beach`, `quadra`),
  - Modo `flex` (fallback poliatleta).
- `xp_service.py` e `user_service.py` foram conectados ao motor assíncrono para remover dispersão de regras na seleção de cálculo por esporte.

### 2) Engine de Progressão & Integridade
- Regra de progressão fixada para **60 XP = 1 atributo** (`_resolve_xp_per_level`), removendo variação por faixa de overall.
- `apply_match_progression` reforçado com lock transacional:
  - lock de `PlayerStats` via `SELECT ... FOR UPDATE`;
  - lock de `UserXP` no repositório (`with_for_update()`), reduzindo risco de race conditions em concorrência.
- Mantida a drenagem automática para `UserPrestige` quando atributo está em 99 (`sync_user_prestige_entries`).

### 3) Segurança & Anti-Fraude
- `MatchPerformanceRateLimitMiddleware` ajustado para **20 minutos**.
- Implementado JWT owner-check no middleware:
  - valida `Authorization: Bearer <token>`;
  - decodifica `sub`;
  - exige `sub == payload.user_id` para permitir submissão.
- Criado `app/core/security.py` com:
  - `decode_jwt_subject_from_header`;
  - sanitização centralizada (`sanitize_text`, `sanitize_text_dict`).
- Endurecimento Pydantic em schemas de entrada com `extra="forbid"`, `strict=True` e sanitização por `field_validator`:
  - `BoxScoreCreate`, `UserCreate`, `UserUpdate`, `UserInterestCreate`, `PlayerStatsUpdate`, `ClubCreate`, `ClubJoinRequest`, `ClubMembershipReviewRequest`.

### 4) Self-Healing
- Criado `app/services/self_healing_service.py`.
- Na inicialização (`main.py` lifespan), executa varredura de `PlayerStats` para detectar overalls impossíveis (`NaN`, `inf`, `<0`, `>99`) e recalcular via histórico recente de `MatchPerformance` + overall engine.
- Adicionado handler global de exceções 500 em `main.py`:
  - log estruturado de stacktrace;
  - emissão em telemetria (`StructuredTelemetryRepository`);
  - resposta amigável sem detalhes de infraestrutura.

### 5) Índices de Performance
- `app/core/database.py` recebeu novos índices para alta velocidade:
  - `match_performance(user_id, created_at DESC)`
  - `match_performance(event_id, user_id)`
  - `user_xp(user_id, attribute_name, level DESC)`
  - `user_achievement(user_id, created_at DESC)`

### 6) Testes QA Extremo
- Novo arquivo `tests/test_security_and_stress.py` com:
  - cobertura de modos do overall engine,
  - validação de bypass JWT (missing/mismatch/sucesso),
  - rejeição de injeção negativa em atributos,
  - sanitização anti-XSS,
  - teste de estresse de 1.000 iterações para integridade Prestige,
  - check de performance de processamento de box score (<100ms no cenário unitário).
- Atualizados testes existentes:
  - `tests/test_match_performance_rate_limit.py` (janela 20 min),
  - `tests/test_xp_achievements_boxscore.py` (divisor fixo em 60),
  - `tests/test_user_api_stats.py` (import lazy de sessão).

### 7) Ajustes de Robustez para Testes
- `app/api/__init__.py` convertido para lazy-loading de routers para evitar side effects de boot de DB durante import.
- `app/api/users.py` passou a usar `get_session` de `app.core` (lazy wrapper) em vez de import direto de `app.core.database`.

### Notas de decisão
- Não foi feita renomeação destrutiva de colunas de domínio (`goals`, `points`) para evitar quebra retrocompatível sem migração completa de banco e clients; a modelagem atual permanece semanticamente válida por modalidade.
- Otimizações vetoriais com NumPy não foram introduzidas neste ciclo para evitar dependência extra e custo de serialização/boxing no hot path atual; o ganho imediato foi obtido com lock transacional, simplificação de regra de XP e redução de acoplamento.
