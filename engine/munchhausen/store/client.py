"""Atlas connections, one client per database role (SPEC § 20.2 gold isolation).

    learner   readWrite@munchhausen, read@world    — the engine's stores
    executor  read@world                           — proposer pipelines, the nominator's world tool
    evaluator read@truth                           — the Truth implementation only

Until per-role users exist, every role falls back to MONGODB_URI and isolation holds by convention
(and by the import test); the roles make it hold at the database.
"""

from __future__ import annotations

from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from munchhausen.config import Role, Settings


class AtlasClients:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._clients: dict[str, AsyncMongoClient[dict[str, Any]]] = {}

    def client(self, role: Role) -> AsyncMongoClient[dict[str, Any]]:
        uri = self._settings.uri_for(role)
        if uri not in self._clients:   # roles sharing one URI share one connection pool
            self._clients[uri] = AsyncMongoClient(uri, appname=f"munchhausen-{role}", tz_aware=True)
        return self._clients[uri]

    def store_db(self) -> AsyncDatabase[dict[str, Any]]:
        return self.client("learner")[self._settings.store_db]

    def world_db(self, *, write: bool = False) -> AsyncDatabase[dict[str, Any]]:
        return self.client("learner" if write else "executor")[self._settings.world_db]

    def source_db(self) -> AsyncDatabase[dict[str, Any]]:
        return self.client("learner")[self._settings.source_db]

    def truth_db(self) -> AsyncDatabase[dict[str, Any]]:
        """Handed to the Truth implementation by the composition root, and to nothing else."""
        return self.client("evaluator")[self._settings.truth_db]

    async def close(self) -> None:
        for c in self._clients.values():
            await c.close()
        self._clients.clear()
