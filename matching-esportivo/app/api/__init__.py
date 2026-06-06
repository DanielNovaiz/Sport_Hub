"""API endpoints do projeto (lazy imports para evitar side effects em testes)."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "auth_router",
    "clubs_router",
    "events_router",
    "feed_router",
    "notifications_router",
    "users_router",
    "ranked_router",
    "ranking_router",
    "chat_router",
    "court_router",
]


_ROUTER_MODULES = {
    "auth_router": "app.api.auth",
    "clubs_router": "app.api.clubs",
    "events_router": "app.api.events",
    "feed_router": "app.api.feed",
    "notifications_router": "app.api.notifications",
    "users_router": "app.api.users",
    "ranked_router": "app.api.ranked",
    "ranking_router": "app.api.ranking",
    "chat_router": "app.api.chat",
    "court_router": "app.api.court",
}


def __getattr__(name: str):
    module_name = _ROUTER_MODULES.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name)
    return getattr(module, "router")
