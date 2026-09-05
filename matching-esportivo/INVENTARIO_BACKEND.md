# INVENTÁRIO TÉCNICO — BACKEND (matching-esportivo/app)

Invólucro do inventário técnico do backend FastAPI/SQLModel/PostGIS, levantado por leitura direta dos
arquivos e verificado na rodada V4. Formato por arquivo: `exporta` (símbolos/contratos principais) e
`importa (interno)` (dependências dentro do projeto). Convenção: `A → B` = "A importa B"; `(T)` =
import top-level; `(L)` = lazy/dentro de função.

Escopo coberto: `app/api/`, `app/core/`, `app/models/`, `app/repositories/`, `app/schemas/`,
`app/services/`. (Fora do escopo, mas existentes: `app/positions.py`, `app/db/migrations/`,
`app/middleware/`.)

> Nota de acoplamento (ver PLANO_REFATORACAO_BACKEND.md): existe um SCC
> `{xp_service, overall_engine, user_service}` e uma aresta dinâmica `xp_service → calculations`
> via `importlib.util` (não import normal).

---

## 1. app/api/

- arquivo: `__init__.py`
  - exporta: reexport lazy de `auth_router, clubs_router, events_router, feed_router,
    notifications_router, users_router, ranked_router, ranking_router, chat_router, court_router`
    (via `__getattr__` + mapa `_ROUTER_MODULES`; cada um resolve o atributo `router` do submódulo).
  - importa (interno): `app.api.{auth,clubs,events,feed,notifications,users,ranked,ranking,chat,court}`.

- arquivo: `auth.py`
  - exporta: `router` (prefix `/api/auth`); endpoints `POST /login`, `POST /refresh`, `POST /logout`;
    Pydantic `LoginRequest, RefreshTokenRequest, TokenUser, TokenResponse`; dataclass `AuthUser`;
    helpers `_bootstrap_user, _issue_access_token, _issue_refresh_token, _serialize_user`.
  - importa (interno): `app.core.config` (settings).

- arquivo: `chat.py`
  - exporta: `router` (prefix `/api/chat`); `POST /rooms/{event_id}`, `GET /rooms/{room_id}/messages`,
    `GET /rooms/{room_id}`, `POST /rooms/{room_id}/messages` (persistência + Redis Pub/Sub).
  - importa (interno): `app.core.database` (get_session), `app.models.chat` (ChatRoom),
    `app.schemas.chat`, `app.services.chat_service`.

- arquivo: `clubs.py`
  - exporta: `router` (prefix `/api/clubs`); `POST /`, `GET /nearby`, `POST /{club_id}/join`,
    `POST /{club_id}/members/{user_id}/approve`, `.../reject`, `GET /{club_id}/members/{user_id}/synergy`.
  - importa (interno): `app.core.database`, `app.schemas.club`, `app.schemas.event` (UserLocation),
    `app.services.club_service`.

- arquivo: `court.py`
  - exporta: `router` (prefix `/api/courts`); `GET ""`, `POST ""`, `GET /{court_id}`,
    `POST /{court_id}/bookings`, `GET /{court_id}/availability`, `GET /bookings/my`.
  - importa (interno): `app.core.database`, `app.models.court` (Court), `app.schemas.court`,
    `app.services.court_service` (incl. `_to_court_read` — privado, ver P5 do plano).

- arquivo: `events.py`
  - exporta: `router` (prefix `/api/events`); `POST /`, `GET /search`, `POST /{event_id}/join`,
    `GET /{event_id}/suggestions`.
  - importa (interno): `app.core.database`, `app.schemas.event`, `app.services.event_service`,
    `app.services.matching_service` (suggest_players_for_event).

- arquivo: `feed.py`
  - exporta: `router` (prefix `/api/feed`); `GET /`.
  - importa (interno): `app.core.database`, `app.schemas.event` (PersonalizedFeedResponse),
    `app.services.event_service` (get_personalized_feed).

- arquivo: `notifications.py`
  - exporta: `router` (prefix `/api/notifications`); só `GET /` (listar).
  - importa (interno): `app.core.database`, `app.schemas.notification`,
    `app.services.notification_service` (list_notifications).

- arquivo: `ranked.py`
  - exporta: `router` (prefix `/api/ranked`); `GET /`, `GET /{user_id}`,
    `POST /match/{winner_id}/{loser_id}`, `POST /box-score`.
  - importa (interno): `app.core.database`, `app.schemas.ranked`, `app.services.ranked_service`.

- arquivo: `ranking.py`
  - exporta: `router` (prefix `/api/ranking`); `GET /regional` (Top 50 por overall).
  - importa (interno): `app.core.database`, `app.schemas.ranked`,
    `app.services.ranked_service` (DEFAULT_REGIONAL_CITY, list_regional_ranked_users).

- arquivo: `users.py`
  - exporta: `router` (prefix `/api/users`); `POST /`, `GET /{user_id}`, `GET /{user_id}/profile`,
    `GET /` (listar), `PATCH /{user_id}`, `PATCH /me/stats`, `DELETE /{user_id}`.
  - importa (interno): `app.core` (get_session — via barril, ver P3), `app.schemas.user`,
    `app.services.user_service`.

---

## 2. app/core/

- arquivo: `__init__.py`
  - exporta: `settings`, `get_session`, `init_db`, `close_db`, `SportType`, `FootballSubType`,
    `BasketballSubType`, `VolleyballSubType`, `SportSubType`, `POSITIONS_MAP`,
    `normalize_position_input` (mistura reexport de enums/positions + wrappers de db — ver P3).
  - importa (interno): `app.core.config`, `app.core.enums`, `app.positions`, lazy `app.core.database`.

- arquivo: `config.py`
  - exporta: `settings` (instância única de `Settings`); env vars app/db/redis/security/raio;
    propriedades `database_url`, `database_url_async`, `redis_url`, `allowed_origins_list`; `_validate`.
  - importa (interno): nenhum.

- arquivo: `database.py`
  - exporta: `engine`, `async_session`, `init_db(max_attempts, initial_delay_seconds)`,
    `get_session()` (dependency FastAPI), `close_db()`, `_is_transient_database_startup_error`; cria
    tabelas + índices PostGIS (ST/GIST/geography) e relacionais.
  - importa (interno): `app.core.config` (settings), `app.models` (registro de tabelas).

- arquivo: `enums.py`
  - exporta: `SportType`, `FootballSubType`, `BasketballSubType`, `VolleyballSubType`, `SportSubType`.
  - importa (interno): nenhum.

- arquivo: `logger.py`
  - exporta: `JsonFormatter` (inclui campo `extra`), `configure_logging(log_level)`. Usado por `main.py`.
  - importa (interno): nenhum.

- arquivo: `logging_config.py`
  - exporta: `JsonFormatter`, `configure_logging` — **DUPLICADO de `logger.py`** (sem coleta de extras).
  - importa (interno): nenhum.

- arquivo: `redis.py`
  - exporta: `get_redis()`, `close_redis()`, `pub_notification(user_id, message, extra)` (channel
    `notifications:{user_id}`).
  - importa (interno): `app.core.config` (settings).

- arquivo: `security.py`
  - exporta: `SecurityError`, `decode_jwt_subject_from_header(...)`, `sanitize_text(...)`,
    `sanitize_text_dict(...)`.
  - importa (interno): `app.core.config` (settings).

---

## 3. app/models/

- arquivo: `__init__.py`
  - exporta: reexport de `Club, ClubMember, TeamSynergy, Event, Match, EventParticipant, UserRank,
    Season, SeasonRank, SeasonMilestone, SeasonRewardGrant, ChatRoom, ChatMessage, Court, Booking,
    Athlete, Notification, PlayerStats, UserXP, UserAchievement, UserPrestige, MatchPerformance,
    User, UserInterest`.
  - importa (interno): todos os submódulos de `app.models.*`.

- arquivo: `athlete.py`
  - exporta: tabela `Athlete` (`athlete`; JSON preferred_sports/skill_levels).
  - importa (interno): nenhum.

- arquivo: `chat.py`
  - exporta: `ChatRoom` (`chat_room`, FK event.id), `ChatMessage` (`chat_message`, FKs room/user).
  - importa (interno): nenhum.

- arquivo: `club.py`
  - exporta: `ClubPrivacyType`, `ClubMemberStatus`, `TeamSynergyStatus`; tabelas `Club` (`club`),
    `ClubMember` (`club_member`), `TeamSynergy` (`team_synergy`); índices GIST/geography.
  - importa (interno): nenhum.

- arquivo: `court.py`
  - exporta: `BookingStatusEnum`; tabelas `Court` (`court`), `Booking` (`booking`).
  - importa (interno): nenhum.

- arquivo: `event.py`
  - exporta: `EventStatus`, `EventParticipantStatus`; tabelas `Event` (`event`),
    `EventParticipant` (`event_participant`); alias `Match = Event`.
  - importa (interno): nenhum.

- arquivo: `notification.py`
  - exporta: `NotificationType = Literal["invite","match","event_update"]`; tabela `Notification`.
  - importa (interno): nenhum.

- arquivo: `player_stats.py`
  - exporta: `PlayerPosition`; tabelas `PlayerStats` (dezenas de atributos 0-99), `UserXP`,
    `UserAchievement`, `UserPrestige`, `MatchPerformance`.
  - importa (interno): nenhum.

- arquivo: `ranked.py`
  - exporta: `LeagueDivisionEnum` (bronze..global); tabela `UserRank` (`user_rank`, MMR/divisão).
  - importa (interno): nenhum.

- arquivo: `season.py`
  - exporta: `SeasonStatus`, `SeasonRewardKind`; tabelas `Season`, `SeasonRank`, `SeasonMilestone`,
    `SeasonRewardGrant`.
  - importa (interno): nenhum.

- arquivo: `user.py`
  - exporta: `UserSkillLevel`; tabelas `User` (`user`, location geom + Relationship interests),
    `UserInterest` (`user_interest`).
  - importa (interno): nenhum.

---

## 4. app/repositories/

- arquivo: `__init__.py`
  - exporta: `StructuredTelemetryRepository`, `SqlAlchemyXpRepository`.
  - importa (interno): `app.repositories.{telemetry_repository,xp_repository}`.

- arquivo: `telemetry_repository.py`
  - exporta: classe `StructuredTelemetryRepository` (`emit(category, user_id, entries, extra)` →
    logger JSONL rotacionado em `logs/telemetry.log`).
  - importa (interno): nenhum.

- arquivo: `xp_repository.py`
  - exporta: dataclass `AchievementTriggerLike`, protocolo `XpRepository`, classe
    `SqlAlchemyXpRepository` (get/ensure_user_xp_rows, get/ensure_player_stats,
    upsert_user_achievements).
  - importa (interno): `app.models.player_stats` (PlayerStats, UserAchievement, UserXP);
    `app.services.xp_constants` (ALL_PROGRESS_ATTRIBUTES); lazy `app.services.achievement_service`
    (apply_achievement_rarity_bonus, resolve_achievement_rarity) — **inversão repo→service (ver P2)**.

---

## 5. app/schemas/

- arquivo: `__init__.py`
  - exporta: reexport de todos os contracts (event, club, notification, athlete, ranked, chat, court, user).
  - importa (interno): `app.schemas.{event,club,notification,athlete,ranked,chat,court,user}`.

- arquivo: `athlete.py` — exporta `AthleteCreate`, `AthleteResponse`; importa interno: nenhum.
- arquivo: `chat.py` — exporta `ChatMessageCreate/Read/Response`, `ChatRoomRead/Response`,
  `ChatMessageListResponse`; importa interno: nenhum.
- arquivo: `club.py` — exporta `ClubPrivacyType`, `ClubMemberStatus`, `ClubCreate/Read/Response`,
  `ClubNearbyResponse`, `ClubJoinRequest/Response`, `ClubMemberRead`,
  `ClubMembershipReviewRequest/Response`, `TeamSynergyCardRead/Response`; importa interno:
  `app.core.security` (sanitize_text).
- arquivo: `court.py` — exporta `CourtCreate/Read/Response`, `CourtListResponse`,
  `BookingCreate/Read/Response`, `BookingWithCourtRead`, `BookingListResponse`; importa interno:
  `app.models.court` (BookingStatusEnum) — **aresta schemas→models (ver P6)**.
- arquivo: `event.py` — exporta `EventStatus`, `EventParticipantStatus`, `UserLocation`,
  `EventSearchFilters`, `EventCreate/Read/Response`, `EventSearchResponse`, `JoinEventRequest/Response`,
  `EventParticipantRead`, `SuggestedPlayerRead`, `EventSuggestionsResponse`, `PersonalizedFeedItem/Response`;
  importa interno: nenhum.
- arquivo: `notification.py` — exporta `NotificationType`, `NotificationRead`, `NotificationListResponse`;
  importa interno: nenhum.
- arquivo: `ranked.py` — exporta `AchievementRead`, `UserRankRead/Response`, `RankedUserRead`,
  `RankedUsersResponse`, `BoxScoreCreate`, `BoxScoreResultRead`, `BoxScoreResponse`; importa interno:
  `app.core.security` (sanitize_text), `app.models.ranked` (LeagueDivisionEnum) — **aresta schemas→models**.
- arquivo: `user.py` — exporta `UserSkillLevel`, `User*` (base/create/read/update/list/delete/profile),
  `UserInterest*`, `PlayerStatsBase/Update/Read/Response`, `UserXPRead`, `UserAchievementRead`,
  `UserProfileCard`, `UserProfileResponse`; importa interno: `app.core.security` (sanitize_text).

---

## 6. app/services/

- arquivo: `__init__.py`
  - exporta: nada (`__all__ = []`; pacote leve, submódulos importados diretamente). importa interno: nenhum.

- arquivo: `achievement_service.py`
  - exporta: dataclass `AchievementSpec`; `ACHIEVEMENT_SPECS` (HAT_TRICK, WALL);
    `ACHIEVEMENT_RARITY_MULTIPLIERS`; `resolve_achievement_rarity`, `apply_achievement_rarity_bonus`,
    `award_match_achievements`.
  - importa (interno): `app.models.player_stats` (MatchPerformance, UserAchievement).

- arquivo: `calculations.py`
  - exporta: `FOOTBALL_ATTRIBUTE_TO_PACKAGE`, `FUTSAL_MULTIPLIERS`, `SOCIETY_MULTIPLIERS`,
    `FOOTBALL_SUB_TYPE_MULTIPLIERS`, `apply_sub_type_multipliers(...)`, `_get_multipliers_for_sport`,
    `calculate_precise_overall(...)` (marcado Deprecated; referencia
    `calculate_precise_overall_with_sub_type` que NÃO existe). **Carregado por `xp_service` via
    `importlib.util` (não via import).**
  - importa (interno): nenhum.

- arquivo: `chat_service.py`
  - exporta: `create_chat_room`, `list_messages`, `send_message` (persistência + Redis Pub/Sub).
  - importa (interno): `app.core.redis` (get_redis), `app.models.chat`, `app.schemas.chat`.

- arquivo: `club_service.py`
  - exporta: constantes de sinergia; `create_club`, `search_nearby_clubs`, `request_club_join`,
    `review_club_membership`, `build_members_key`, `resolve_synergy_status`, `has_high_synergy`,
    `upsert_team_synergy`, `list_user_synergy_badges`.
  - importa (interno): `app.models.club`, `app.schemas.club`, `app.schemas.event` (UserLocation).

- arquivo: `court_service.py`
  - exporta: `_to_court_read` (privado), `create_court`, `list_courts`, `check_booking_availability`,
    `create_booking` (concorrência via SELECT FOR UPDATE), `list_user_bookings`.
  - importa (interno): `app.models.court`, `app.schemas.court`.

- arquivo: `event_service.py`
  - exporta: `find_nearby_events`, `create_event`, `join_event` (notificação + waitlist),
    `get_personalized_feed`; helper `_count_confirmed_participants`.
  - importa (interno): `app.models.{club,event,user}`, `app.schemas.event`, `app.core.redis`
    (pub_notification), `app.services.notification_service` (create_notification).

- arquivo: `maintenance_service.py`
  - exporta: dataclasses `XpIntegerConversion`, `XpApplyResult`, `XpConsistencyReport`, `CleanupReport`,
    `BackfillReport`; `convert_xp_to_attribute_points`, `apply_penalty_with_rollback_guard`,
    `credit_prestige_xp`, `sync_user_prestige_entries`, `apply_common_xp_with_cap`,
    `check_xp_consistency`, `cleanup_orphaned_matches`, `backfill_missing_sub_attributes`.
  - importa (interno): `app.positions` (normalize_position_input), `app.models.player_stats`,
    `app.models.user`.

- arquivo: `matching_service.py`
  - exporta: `suggest_players_for_event` (filtro ST_DWithin/ST_Distance).
  - importa (interno): `app.models.{event,user}`, `app.schemas.event` (SuggestedPlayerRead).

- arquivo: `notification_service.py`
  - exporta: `list_notifications`, `create_notification`.
  - importa (interno): `app.models.notification`, `app.schemas.notification`.

- arquivo: `overall_engine.py`
  - exporta: dataclass `OverallRequest`; `_normalize_sport`, `_normalize_sub_type`, `_calculate_sync`,
    `calculate_overall_async` (unifica via `to_thread`; sub-tipo "flex" usa `calculate_attribute_overall`).
  - importa (interno): `app.models.player_stats` (PlayerStats); lazy `app.services.xp_service`
    (calculators) — **aresta `overall_engine →(L) xp_service` (ciclo)**.

- arquivo: `profile_cache_service.py`
  - exporta: `PROFILE_CACHE_TTL_SECONDS`, `build_user_profile_cache_key`, `get_cached_user_profile`,
    `set_cached_user_profile`, `invalidate_user_profile_cache`.
  - importa (interno): `app.core.redis` (get_redis), `app.schemas.user` (UserProfileCard).

- arquivo: `season_manager.py`
  - exporta: dataclasses `SeasonMilestoneGrantResult`, `SeasonProgressResult`, `SeasonSnapshot`;
    `get_current_season`, `get_or_create_season_rank`, `get_active_xp_multiplier`, `award_season_progress`,
    `get_current_frame_code`, `get_user_season_snapshot`, `grant_season_completion_badge`,
    `finalize_season`, `finalize_overdue_seasons`.
  - importa (interno): `app.models.player_stats` (UserAchievement), `app.models.season`,
    `app.services.profile_cache_service`.

- arquivo: `self_healing_service.py`
  - exporta: `_is_invalid_overall`, `recalculate_impossible_overalls`.
  - importa (interno): `app.models.player_stats`, `app.services.overall_engine` (OverallRequest,
    calculate_overall_async).

- arquivo: `streak_manager.py`
  - exporta: constantes badge "On Fire"; dataclass `StreakResult`; `evaluate_on_fire_streak`.
  - importa (interno): `app.models.player_stats` (MatchPerformance, PlayerStats).

- arquivo: `xp_constants.py`
  - exporta: `ALL_PROGRESS_ATTRIBUTES` (tuple deduplicada). importa interno: nenhum.

- arquivo: `ranked_service.py`
  - exporta: `DEFAULT_REGIONAL_CITY`; `calculate_mmr_change`, `get_or_create_user_rank`,
    `get_user_rank_read`, `update_rank_after_match`, `list_ranked_users`, `_normalize_city_key`,
    `_resolve_city_center`, `list_regional_ranked_users`, `_normalize_sport`, `submit_box_score`.
  - importa (interno): `app.models.{event,player_stats,user,ranked}`, `app.schemas.ranked`,
    `app.services.{club_service, profile_cache_service, season_manager, xp_service}`,
    `app.repositories` (StructuredTelemetryRepository).

- arquivo: `user_service.py` (hub de negócio)
  - exporta: `PLAYER_OVERALL_WEIGHTS`; `create_user`, `get_user_by_id`, `list_users`, `update_user`,
    `delete_user`, `get_user_profile_card` (usa cache), `update_user_stats`, `calculate_player_overall`,
    `calculate_playstyle_archetype`; helpers privados.
  - importa (interno): `app.models.{player_stats,user}`, `app.positions` (normalize_position_input),
    `app.schemas.user`, `app.services.{xp_service, overall_engine, maintenance_service, club_service,
    profile_cache_service, season_manager}`.

- arquivo: `xp_service.py` (HUB de dependências; maior e mais conectado)
  - exporta: `XP_PER_LEVEL`, `MAX_LEVEL_GAIN_PER_MATCH`, `MAX_XP_APPLIED_PER_MATCH`; mapas de
    packages/pesos por posição; dataclasses `AchievementTrigger`, `MatchXpResult`, `PackageXpBreakdown`;
    funções de overall (`calculate_basketball/football/volleyball/attribute_overall[_by_position]`),
    `calculate_attribute_overall` (alias poliatleta → user_service), `apply_multiplier`,
    `process_3x3_performance`, `distribute_match_xp`, `process_match_performance`,
    `apply_achievement_bonuses`, `upsert_user_achievements`, `apply_match_progression`,
    `normalize_profile_sport_type`.
  - importa (interno): `app.models.player_stats`, `app.services.xp_constants`,
    `app.services.overall_engine` (T — ciclo), `app.services.maintenance_service`,
    `app.repositories` (StructuredTelemetryRepository, SqlAlchemyXpRepository),
    `app.repositories.xp_repository` (AchievementTriggerLike); lazy `app.services.user_service`
    (`calculate_player_overall`, no alias poliatleta) — **ciclo**; dinâmico `calculations.py` via
    `importlib.util` (`_CALCULATIONS_MODULE`, linhas 27/425-437).




