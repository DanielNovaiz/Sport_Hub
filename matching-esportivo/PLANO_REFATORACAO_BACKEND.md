# PLANO DE REFATORAÇÃO — BACKEND MATCHING ESPORTIVO

> **Premissa:** o arquivo `INVENTARIO_BACKEND.md` citado como entrada **não existia no filesystem**
> (varredura recursiva vazia) — o inventário anterior saiu como texto de chat, não persistido. Para
> não travar, este plano foi **validado direto no código** (app/ e tests). Onde a verificação
> divergiu das hipóteses, o fato está marcado como **CORREÇÃO**. Posso, se desejado, persistir o
> `INVENTARIO_BACKEND.md` como linha de base. Convenção: `A → B` = "A importa B"; "arcos
> entrantes" = quantos módulos dependem do módulo; barris/`__init__` de reexporta não contam como
> dependente real.

---

## TAREFA 1 — Mapa de acoplamento real

### a) Hubs — quem mais outros dependem (arcos entrantes)

1. **`xp_service` — hub n.º 1 (CORREÇÃO: não são `ranked_service`/`user_service`).**
   É o maior texto, o mais conectado (~6 módulos internos) e o mais importado: `user_service`
   (T), `ranked_service` (T), `overall_engine` (L) + `test_3x3_performance`,
   `test_security_and_stress`, `test_xp_achievements_boxscore`.
2. **`user_service` — hub de NEGÓCIO (perfil/overall), não de dependências.** Importado por
   `api/users.py` e (lazy) por `xp_service.calculate_attribute_overall`, além de testes.
3. **`overall_engine`** — consumido por `user_service`, `xp_service`, `self_healing_service`
   (+1 teste); núcleo de cálculo. Também importa `xp_service` (L) — entra no ciclo (ver b).
4. **Secundários (1–3 arcos):** `season_manager`, `profile_cache_service`, `club_service`,
   `maintenance_service`, `notification_service`.
5. **`ranked_service` é hub de SAÍDA:** poucos dependentes (`api/ranked`, `api/ranking`, 2 testes),
   mas importa ~6 módulos internos e tem muita regra → alto risco de regressão na mudança.

**Síntese:** hub real = `xp_service`; `user_service` + `ranked_service` são orquestradores grandes;
os três concentram o risco e pedem cobertura de testes antes de qualquer mexida (Fase 1).

### b) Ciclos reais (inclui lazy/dentro de função; `T`=top-level, `L`=lazy)

- **Ciclo 2N — `overall_engine ↔ xp_service` (CONFIRMADO):** `xp_service →(T) overall_engine` (L20)
  e `overall_engine._calculate_sync →(L) xp_service` (L52) para os `calculate_*_overall`.
- **Ciclo 2N — `xp_service ↔ user_service` (NOVO, não suspeitado):** `user_service →(T) xp_service`
  (L25) e `xp_service.calculate_attribute_overall →(L) user_service.calculate_player_overall`
  (L646) — o alias "poliatleta" devolve a `user_service`.
- **Ciclo 3N (SCC fechado) `{xp_service, overall_engine, user_service}`:**
  `user_service→(T) overall_engine` + `user_service→(T) xp_service`;
  `overall_engine→(L) xp_service`; `xp_service→(L) user_service` + `xp_service→(T) overall_engine`.
  **É este o SCC a quebrar.**
- **Inversão de camada (não é ciclo, mas é aresta contrária):**
  `repositories/xp_repository.upsert_user_achievements →(L) services/achievement_service` (L90) —
  repositório dependendo de service (direção errada).
- **Ok (unidirecionais):** `ranked_service→(xp/club/season/profile_cache)`; `event_service→(T)
  notification_service`; `database→(T) models` (registro de tabelas); `main.py → services/repos`.
- **Aresta dinâmica oculta (NÃO capturada na 1.ª versão):** `xp_service` **não** importa
  `calculations.py` pelo grafo normal — carrega-o por
  `importlib.util.spec_from_file_location("app.services.calculations", …)` dentro de
  `calculate_football_overall` (`_CALCULATIONS_MODULE`, linhas 27/425-437). Ou seja, existe a aresta
  `xp_service → calculations` fora do sistema estático de imports, e a lógica de multiplicadores de
  sub-tipo (`apply_sub_type_multipliers` em `calculations.py`) **duplica parcialmente** o
  `apply_multiplier` de `xp_service` (linhas 668-684). Além disso, o docstring de
  `calculations.calculate_precise_overall` aponta para `calculate_precise_overall_with_sub_type`,
  nome que **não existe** no código (doc dessincronizada). **Consequência colateral:** vários testes
  (`test_calculations_sub_types`, `test_sports_engine`, `test_prestige_service`,
  `test_streak_manager`, `test_user_stats_service`) importam os services com `importlib.util`
  "fora do pacote" justamente por causa do SCC — a quebra P1 deve reescrevê-los para import normal.

**Síntese:** o lazy-import "anti-ciclo" foi usado em 4 pontos (`xp_service→user_service`,
`overall_engine→xp_service`, `xp_repository→achievement_service`, `core/__init__→core.database`).
Não se resolve só trocando lazy por top-level — é preciso mover o bloco para a camada certa.

### c) Inconsistências de padrão de import

1. **Sessão do banco com 2 caminhos:** `from app.core import get_session` (`api/users.py`,
   `test_user_api_stats.py`) vs `from app.core.database import get_session` (8 routers + testes).
2. **Barril `core` acumula papéis:** reexporta settings/enums/positions e ainda cria wrappers
   `get_session/init_db/close_db` que delegam a `database` → origem da ambiguidade do item 1.
3. **Dois loggers duplicados:** `app/core/logger.py` (usado em `main.py`) e
   `app/core/logging_config.py` são a mesma `JsonFormatter` + `configure_logging`.
4. **API importa privado de service:** `api/court.py` usa `_to_court_read` (underscore privado).
5. **Schemas importando Models:** `schemas/court.py→models/court` (`BookingStatusEnum`) e
   `schemas/ranked.py→models/ranked` (`LeagueDivisionEnum`); padrão dominante não faz isso.
6. **Testes usam privados como público:** `_normalize_city_key`, `_resolve_city_center`,
   `_resolve_xp_per_level` — travar renomes internos.
7. **Lazy-import anti-circular espalhado** (ver b).

---

## TAREFA 2 — Veredito sobre os arquivos órfãos

Contexto medido: nenhum módulo de `app/` nem `scripts/` importa os três; o único consumidor do
trio é `tests/test_auth_flow.py` (`from backend_auth_endpoints import router`).

### a) `backend_booking_endpoints.py` — ARQUIVAR/REMOVER (seguro agora)
- Exemplo ilustrativo standalone (prefixo `/matches`, mocks + Django comentado), dependente de
  `get_current_user_id` **inexistente** no projeto (endpoint não executaria).
- Nenhum router de `main.py` expõe `/matches`; o conceito "booking" foi reformulado no domínio
  `court`, e "match" virou alias `Match = Event`.
- Zero imports ativos. Remover ou mover para `docs/legado/` não altera nenhuma suíte.

### b) `sprint3_backend_endpoints.py` — ARQUIVAR/REMOVER (seguro agora)
- Mesmo perfil ilustrativo (notificações + mensagens; mocks; `get_current_user_id` inexistente).
- Funcionalidade absorvida/redesenhada em `api/chat.py`+`chat_service` e
  `api/notifications.py`+`notification_service` (design de sala-por-evento e `Notification`
  reduzido). Sem rota `/messages`/`/matches` no app.
- Zero imports ativos. Remover/arquivar não quebra nada.

### c) `backend_auth_endpoints.py` — NÃO remover ainda; re-apontar teste e então remover
- É um **shim** de 3 linhas (`from app.api.auth import router`) — não tem lógica própria.
- **Risco:** `tests/test_auth_flow.py` o importa; apagar quebra a suíte.
- **Duas sub-etapas (Fase 2):**
  1. Em `tests/test_auth_flow.py`, trocar para `from app.api.auth import router` (ou
     `from app import auth_router`) — derruba o último elo com a raiz;
  2. Rodar a suíte — verde — e então excluir `backend_auth_endpoints.py` (a doc interna já o
     marcava como "apenas compatibilidade").
- **Resumo:** booking e sprint3 saem **agora** sem risco; auth sai após 1 linha de teste.

---

## TAREFA 3 — Arquitetura-alvo (sem redesenhar do zero)

Objetivo: manter o escopo atual (API + motor XP/ranking/season + marketplace court + chat +
notificações), restaurando **direção limpa das arestas** e removendo duplicação e ciclos. Não é
mudança de stack nem de contrato HTTP.

### 3.1 Direção-alvo das camadas

```
app (main.py)  ->  api (thin: monta routers/endpoint; valida contrato)
api  ->  services (regras/orquestração)
services -> repositories -> models (DB)
services -> repositories -> dominios puros (sem DB)
schemas (pydantic; preferencial sem importar models)
core = infra (config, database, redis, security, logging)  -> nada importa services
```

### 3.2 Resolução por ponto arriscado/duplicado da TAREFA 1

**P1 — SCC `{xp_service, overall_engine, user_service}` (ciclos de cálculo/perfil)**
- Causa raiz: mistura de dois conceitos — **cálculo puro de overall** (modalidade/posição/sub-tipo)
  vs **progressão/XP/conquistas** (I/O). Os `calculate_*_overall` vivem hoje em `xp_service`, usados
  como "engine"; e `xp_service` ainda tem alias poliatleta que devolve para lógica de `user_service`.
- Alvo: extrair módulo puro `app/services/domain/overall_calculator.py`, migrando as funções hoje
  espalhadas (`calculate_basketball/football/volleyball/attribute_overall[_by_position]` + helpers de
  package) para ele. Esse módulo não importa nenhum service (só models p/ ler atributos). Depois,
  `overall_engine`, `user_service`, `xp_service`, `self_healing_service` apontam p/ o calculator com
  **uma única aresta** (sem lazy cross). Efeito: `xp_service` perde a volta p/ `user_service`;
  `user_service` deixa de importar cálculo de `xp_service`; o SCC vira DAG.
- **Refinamento V4 (não considerado antes):** há hoje **três** fontes de cálculo de overall — (i) os
  `calculate_*_overall` em `xp_service`, (ii) `calculations.py` carregado dinamicamente por
  `_load_calculations_module` (multiplicadores de sub-tipo) e (iii) o alias poliatleta → `user_service`.
  O novo `overall_calculator` deve **consolidar as três** (absorvendo `apply_sub_type_multipliers` de
  `calculations.py`), eliminar o `_load_calculations_module` e normalizar `calculations.py` (marcar
  aposentado/deprecated). Não fazer isso deixaria uma 4.ª/desincronizada fonte e "quebraria" a intenção.
- **Risco de teste:** os 5+ testes que hoje carregam services via `importlib.util` "fora do pacote"
  (para contornar o SCC) precisam ser reescritos para import normal na mesma fase — senão a suíte
  falseará verde sem exercer o grafo real.

**P2 — Repositório→service (`xp_repository` importa `achievement_service`)**
- Alvo: mover "raridade" e "bônus de raridade" (funções puras por contagem) p/ domínio puro
  (`app/services/domain/achievement_rules.py`). O repo importa domínio puro, jamais um `service`.
  `achievement_service` permanece para a regra de conceder/incrementar; "à esquerda" do repo, nada.

**P3 — Sessão do banco em 2 caminhos + barril `core` genérico**
- Alvo: padronizar `from app.core.database import get_session` em `api/users.py` e
  `test_user_api_stats.py`. Em `app/core/__init__.py`, **remover os wrappers**
  `get_session/init_db/close_db` (só serviam a `api/users` + 1 teste). Barril `core` passa a reexportar
  somente settings/enums (sem esconder database/redis).

**P4 — Dois loggers duplicados (`logger.py` ≈ `logging_config.py`)**
- Alvo: manter um módulo — o que preserva `extra` no JSON (`logger.py`, já usado em `main.py`) —;
  aposentar `logging_config.py` e corrigir o(s) consumo(s) remanescente(s). Um único
  `configure_logging`.

**P5 — API importando privado de service (`_to_court_read`)**
- Alvo: renomear p/ `to_court_read` (público) no service e atualizar o único uso em `api/court.py`;
  sem mudança na rota/HTTP.

**P6 — Schemas importando Models (só p/ enum)**
- Alvo (opcional/baixo risco): mover `BookingStatusEnum` e `LeagueDivisionEnum` p/ `app/core/enums.py`
  (ou p/ junto do schema) e remapear imports — os models passam a importar o enum de `core` quando
  precisarem. Schemas assim ficam sem aresta p/ models. Não requer migração de dados (só remap).

**P7 — Testes presos a privados (`_normalize_city_key`, `_resolve_city_center`, `_resolve_xp_per_level`)**
- Alvo: registrar como dívida a pagar na **Fase 7** (após o lar definitivo dos símbolos), trocando por
  API pública. Não bloquear a migração do cálculo com isso.

**P8 — Barris** — manter `models`, `schemas`, `repositories` (reexportam; reduzem acoplamento);
`api` lazy ok; **simplificar** `core` (P3); `services` não tem barril pesado e isso é desejável.

### 3.3 Regra-resumo da camada p/ o futuro (checklist de arquitetura)
- `models` e `core/database` : só libs + `app.core.config`. Nunca importam services.
- `schemas`: nunca importam `services`; só `app.core.security` e (residual a eliminar) enums/models.
- `repositories`: só `models`/`schemas`/domínios puros. Jamais um `service`.
- `services`: podem importar `repositories`, `models`, `schemas` e **outros services apenas em DAG**
  (nunca ciclo; lazy-import só como decisão explícita p/ teardown de import startup, não p/ aresta).
- `api`: importa `services` + `schemas`; não importa `repositories`.
- `core`: infra base. Se um símbolo em `core` precisar resolver runtime, evidenciar o motivo.

---

## TAREFA 4 — Linha do tempo de execução (ordem segura → arriscada)

Princípios: cada fase é curta, isolada e roda a suíte isoladamente; quem executa (outro modelo, mais
barato) tem "critério de aceite" objetivo por fase. Marcação de risco: 🟢 baixo · 🟡 médio · 🔴 alto.

### Fase 0 — Baseline & grade de verificação (🟢) [~0,5 h · sem código de runtime]
- Rodar a suíte atual + `python -c "import main"` p/ registrar o verde de partida.
- Criar (ou conferir) um teste leve de **ciclos de import** (ex.: subir um grafo de imports de
  `app/services` e falhar se houver ciclo/aresta repository→service). Isso vira o "guarda de
  regressão" de todas as fases seguintes.
- **Aceite:** suíte verde + teste de ciclo falhando nos 2 ciclos da TAREFA 1 (sinal de que ele mede o certo).

### Fase 1 — Higiene barata e isolada (🟢) [~1–2 h]
- **P4:** deduplicar loggers (manter `logger.py`, aposentar `logging_config.py`, corrigir consumo).
- **P3a:** uniformizar todos os `get_session` para `app.core.database` (usuário + teste) e remover os
  wrappers de `core/__init__`.
- Barril `core` passa a reexportar só settings/enums.
- **Aceite:** suíte verde; import lint sem quebra; nenhum `from app.core import get_session` restante.

### Fase 2 — Limpeza de arquivos órfãos (🟢) [~0,5–1 h · só raiz + teste]
- Confirmando TAREFA 2: arquivar/excluir `backend_booking_endpoints.py` e `sprint3_backend_endpoints.py`
  (opcionalmente mover p/ `docs/legado/`). Para `backend_auth_endpoints.py`: primeiro trocar o import
  em `tests/test_auth_flow.py` p/ `app.api.auth.router`, rodar suíte, então excluir o shim.
- **Aceite:** suíte verde com os 3 arquivos ausentes da raiz; `git log`/`grep` sem referência ativa.

### Fase 3 — Inversão repository→service (P2) (🟡) [~2–3 h]
- Extrair `app/services/domain/achievement_rules.py` (raridade + bônus de raridade, puro).
- `xp_repository` passa a depender do domínio puro; `achievement_service` apenas distribui p/ repo.
- **Aceite:** teste de ciclo agora só acusa o SCC de cálculo; suíte verde; `grep achievement_service`
  em `repositories/` vazio.

### Fase 4 — Quebra do SCC de cálculo (P1) (🔴 mais arriscado) [~4–6 h, em micro-passos]
Sequência minimal, cada passo verde antes do próximo:
1. Mover funções puras de overall (`calculate_*_overall[_by_position]`, helpers) p/
   `overall_calculator`, mantendo `xp_service` reexportando (alias) p/ não quebrar outros módulos/tests.
2. Apontar `overall_engine` para o calculator e remover o lazy `xp_service` ali; após, o teste de
   ciclo deixa de reportar o ciclo `overall_engine↔xp_service`.
3. Fazer `user_service` importar o calculator (não cálculo de `xp_service`).
4. Eliminar o alias "poliatleta" `calculate_attribute_overall` em `xp_service` (ou movê-lo): quem
   precisava (engine/flex) usa o calculator; remover a aresta `xp_service →(L) user_service`.
5. **Consolidar a 3.ª fonte:** absorver `apply_sub_type_multipliers` de `calculations.py` no
   calculator e remover o `_load_calculations_module` (dinâmico) de `xp_service`; aposentar
   `calculations.py`. **Reescrever** os testes que usam `importlib.util` (`test_calculations_sub_types`,
   `test_sports_engine`, `test_prestige_service`, `test_streak_manager`, `test_user_stats_service`)
   para import normal — senão a suíte não exercita o grafo real.
6. Rodar suíte + teste de ciclo: SCC `{xp, oe, user}` não deve mais existir.
- **Aceite:** suíte verde; teste de ciclo passa (grafo em DAG); perfis/ranked (que passam por
  `apply_match_progression`/`submit_box_score`) com comportamento idêntico (verbo de contrato).

### Fase 5 — Expôr `to_court_read` (P5) (🟢) [~0,5 h]
- Renomear `_to_court_read`→`to_court_read` no service; atualizar `api/court.py`.
- **Aceite:** endpoints de court marcados no contrato continuam iguais; suíte verde.

### Fase 6 — Remover aresta schemas→models (P6) (🟡, opcional) [~1–2 h]
- Mover `BookingStatusEnum`/`LeagueDivisionEnum` para `core/enums` (ou schema) e remapear imports
  (`models` passam a importar de `core` quando precisarem; schemas não importam models).
- **Aceite:** suíte verde; teste de dependência reportando zero `schemas → models`.

### Fase 7 — Estabilizar contratos públicos e testes (🟡) [~2–3 h]
- Converter usos de privados (`_normalize_*`, `_resolve_xp_per_level` etc. que sobraram) para APIs
  públicas; revisar docstrings de "Input/Output" para alinhar `api → services → repositories`.
- **Aceite:** nenhum teste novo importando símbolo `_`-prefixado de `python -m pytest -q`.

### Fase 8 — Documentação & fechamento (🟢) [~1 h]
- Atualizar `ARCHITECTURE.md`/`CONVENTIONS.md` com o grafo alvo (T3.1), a regra de camadas (T3.3) e a
  lista de eliminações. Persistir `INVENTARIO_BACKEND.md` (linha de base) se desejado.
- **Aceite:** docs refletem o código; `inventory`/plano versionados; suíte no estado verde de partida.

### Matriz resumo
| Fase | Conteúdo | Risco | Benefício |
|------|----------|-------|-----------|
| F0 | baseline + teste de ciclos | 🟢 | guia de regressão p/ todas |
| F1 | dedupe loggers + sessão única | 🟢 | remove duplicação/ambiguidade |
| F2 | órfãos fora | 🟢 | reduz raiz/surpresa |
| F3 | invert. repo→domínio | 🟡 | direção de camada correta |
| F4 | quebra SCC cálculo | 🔴 | mata ciclos reais |
| F5 | `to_court_read` público | 🟢 | API→service limpa |
| F6 | schemas sem models | 🟡 | aresta residual removida |
| F7 | testes em API pública | 🟡 | libera renome futuro |
| F8 | docs + INVENTARIO persistido | 🟢 | fechamento consistente |

> Nota de execução p/ quem for implementar: nunca pular a suíte entre micro-passos da F4 (é onde os
> riscos reais de comportamento vivem). Depois da F4, se houver tempo, F6–F7 podem ser adiadas se o
> verde se mantiver — são melhorias, não bloqueios.

---

## Validação (V4 Pro)

Revisão executada diretamente contra o código real (`app/` + varredura global `.py`/`.dart`). Veredito:
o plano do modelo mais barato está **substancialmente correto** nas 4 tarefas; aplicamos ajustes finos
(abaixo) sem alterar a direção geral, pois os pilares (hub `xp_service`, SCC de 3 nós, veredito dos
órfãos, ordem de fases) conferem com o código.

### O que foi CONFIRMADO (sem correção)
1. **Hub = `xp_service`** (não `ranked_service`/`user_service`). Confere: `xp_service` é o mais
   importado (user_service, ranked_service, overall_engine-lazy + 3+ testes) e o mais conectado.
2. **SCC de 3 nós `{xp_service, overall_engine, user_service}`**, com os 4 arcos comprovados:
   - `xp_service →(T) overall_engine` (L20);
   - `overall_engine._calculate_sync →(L) xp_service` (L52);
   - `user_service →(T) xp_service` (L25–27) e `user_service →(T) overall_engine` (L29);
   - `xp_service.calculate_attribute_overall →(L) user_service.calculate_player_overall` (L644–656) —
     o alias "poliatleta" é real e fecha o SCC.
3. **Órfãos:** varredura global (`.py` + `.dart`, incluindo `mobile_app/` e `scripts/`) confirma
   ZERO referências ativas a `backend_booking_endpoints.py` e `sprint3_backend_endpoints.py`; ambos
   são removíveis com segurança. `backend_auth_endpoints.py` é importado apenas por
   `tests/test_auth_flow.py:10` — a sub-etapa de re-apontar esse import antes de excluir está correta.
4. **Ordem das Fases 0→8** está de fato da mais isolada à mais arriscada, e cada "critério de aceite"
   é objetivo/verificável por outro modelo (greps, suíte, teste de ciclo, ausência de símbolo privado).

### O que foi CORRIGIDO / AJUSTADO (ajustes finos adicionados ao próprio plano)
1. **Aresta dinâmica oculta `xp_service → calculations` (era invisível ao grafo estático).**
   `xp_service` carrega `calculations.py` via `importlib.util.spec_from_file_location`
   (`_CALCULATIONS_MODULE`, linhas 27/425–437) em vez de `import` — depende dele fora do sistema de
   imports. Sem isso, o mapa de acoplamento e o "teste de ciclos" da Fase 0 ficariam incompletos.
   Inserido na TAREFA 1b.
2. **Terceira fonte de cálculo + doc dessincronizada.** Há hoje **três** fontes de overall:
   `calculate_*_overall` (xp_service) + `apply_sub_type_multipliers` (calculations.py dinâmico) +
   alias poliatleta (→ user_service). O docstring de `calculations.calculate_precise_overall` ainda
   aponta para `calculate_precise_overall_with_sub_type`, que **não existe** no código. O P1 foi
   refinado para o `overall_calculator` **consolidar as três** (e aposentar `calculations.py`), não
   apenas acrescentar um novo módulo.
3. **Risco de testes com `importlib.util`.** Os testes `test_calculations_sub_types`,
   `test_sports_engine`, `test_prestige_service`, `test_streak_manager`, `test_user_stats_service`
   (e `test_3x3_performance`) carregam os services manualmente "fora do pacote" para contornar o SCC.
   A Fase 4 agora exige reescrevê-los para import normal — do contrário a suíte falsearia verde sem
   validar o grafo real. (Este era o maior efeito colateral ignorado.)

### Conclusão
Plano aprovado com as correções acima incorporadas. Pode seguir para execução em fases; o modelo
executor deve atentar especialmente à **consolidação do `calculations.py`** e à **reescrita dos testes
com `importlib.util`** durante a Fase 4 — são os pontos onde a análise inicial estava incompleta.



