"""Trace=raindrop (SPEC § 25.1) and the trace fan-out. Offline: a fake `raindrop.analytics` module stands in for
the SDK. Covers begin/finish pairing under concurrency, the signal mapping, the event filter, the persona rule,
swallowed SDK failures, redaction, the null fallback, and trace invariance (SPEC § 21)."""

from __future__ import annotations

import asyncio
import json
import random
import sys
import types
from typing import Any

import pytest

from munchhausen.bootstrap import Harness, build_port, effective_name
from munchhausen.config import Settings
from munchhausen.domain.registers import EPISODE_OUTPUT, SIGNAL_AUTHORITY_CORRECTION, SIGNAL_CORRECT
from munchhausen.impl.sinks import JsonlTrace, NullTrace, RaindropTrace, TeeTrace, read_events
from munchhausen.ports.sinks import Trace

SECRET = "rk-test-write-key-0123456789abcdef"


class FakeInteraction:
    def __init__(self, sdk: FakeRaindrop, kw: dict[str, Any]) -> None:
        self.sdk, self.kw = sdk, kw

    def finish(self, **kw: Any) -> None:
        self.sdk.hit("finish")
        self.sdk.calls.append(("finish", {"event_id": self.kw["event_id"], **kw}))


class FakeRaindrop(types.ModuleType):
    """The slice of `raindrop.analytics` RaindropTrace calls, recording every call (never the key)."""

    def __init__(self) -> None:
        super().__init__("raindrop.analytics")
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.raise_on: set[str] = set()
        self.init_keys: list[str] = []

    def hit(self, what: str) -> None:
        if what in self.raise_on:
            raise RuntimeError(f"sdk {what} exploded")

    def set_debug_logs(self, value: bool) -> None:
        self.calls.append(("set_debug_logs", {"value": value}))

    def init(self, api_key: str | None = None, **kw: Any) -> None:
        self.hit("init")
        self.init_keys.append(api_key or "")
        self.calls.append(("init", kw))

    def begin(self, **kw: Any) -> FakeInteraction:
        self.hit("begin")
        self.calls.append(("begin", kw))
        return FakeInteraction(self, kw)

    def track_signal(self, **kw: Any) -> None:
        self.hit("track_signal")
        self.calls.append(("track_signal", kw))

    def track_ai(self, **kw: Any) -> str:
        self.hit("track_ai")
        self.calls.append(("track_ai", kw))
        return "evt"

    def shutdown(self) -> None:
        self.calls.append(("shutdown", {}))

    def of(self, name: str) -> list[dict[str, Any]]:
        return [kw for n, kw in self.calls if n == name]


@pytest.fixture
def sdk(monkeypatch: pytest.MonkeyPatch) -> FakeRaindrop:
    fake = FakeRaindrop()
    pkg = types.ModuleType("raindrop")
    pkg.analytics = fake  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "raindrop", pkg)
    monkeypatch.setitem(sys.modules, "raindrop.analytics", fake)
    return fake


@pytest.fixture
def keyed(tmp_path) -> Settings:  # noqa: ANN001
    return Settings(_env_file=None, var_dir=tmp_path, run_id="r", raindrop_write_key=SECRET)


def episode(i: int, *, persona: str | None = "anna", arm: str = "governed") -> dict[str, Any]:
    out: dict[str, Any] = {"episode_id": f"r:{arm}:{i}", "arm": arm, "idx": i, "stream": "stream",
                           "template": "active_count", "text": f"How many active customers in {2000 + i}?",
                           "run_id": "r"}
    if persona is not None:
        out["persona"] = persona
    return out


def trace(sdk: FakeRaindrop, s: Settings) -> RaindropTrace:
    t = RaindropTrace.create("raindrop", s)
    assert t._rd is sdk
    return t


# --- construction and the composition root ------------------------------------------------------------------


def test_init_reads_the_knobs_and_never_starts_without_a_key(sdk: FakeRaindrop, keyed: Settings,
                                                             settings_offline: Settings) -> None:
    t = trace(sdk, keyed)
    assert isinstance(t, Trace)
    assert sdk.of("set_debug_logs") == [{"value": True}] and sdk.of("init") == [{"tracing_enabled": False}]
    assert sdk.init_keys == [SECRET]
    with pytest.raises(ValueError, match="RAINDROP_WRITE_KEY"):
        RaindropTrace.create("raindrop", settings_offline)
    t.shutdown()
    assert sdk.of("shutdown") == [{}]


def test_fan_out_and_null_fallback_are_recorded(sdk: FakeRaindrop, keyed: Settings,
                                                settings_offline: Settings) -> None:
    both = keyed.model_copy(update={"trace_impl": "jsonl,raindrop"})
    tee = Harness(settings=both, store=None, arms=both.arms()).trace()  # type: ignore[arg-type]
    assert isinstance(tee, TeeTrace) and [type(t) for t in tee.traces] == [JsonlTrace, RaindropTrace]
    tee.event("run_start", {"arms": ["frozen"]})
    assert [e["name"] for e in read_events(both.var_dir, both.run_id)] == ["run_start"]

    sdk.calls.clear()
    unkeyed = settings_offline.model_copy(update={"trace_impl": "jsonl,raindrop"})
    assert effective_name("trace", "jsonl,raindrop", unkeyed) == "jsonl,null"
    h = Harness(settings=unkeyed, store=None, arms=unkeyed.arms())  # type: ignore[arg-type]
    assert all(sel["trace"] == "jsonl,null" for sel in h.selection().values())
    built = h.trace()
    assert [type(t) for t in built.traces] == [JsonlTrace, NullTrace] and not sdk.calls
    assert type(build_port("trace", "jsonl", unkeyed)) is JsonlTrace


# --- the episode interaction --------------------------------------------------------------------------------


def test_begin_finish_pair_under_six_concurrent_episodes(sdk: FakeRaindrop, keyed: Settings) -> None:
    t = trace(sdk, keyed)
    rng = random.Random(5)

    async def one(i: int) -> None:
        t.begin(episode(i, persona=("anna", "benny", "claire")[i % 3]))
        await asyncio.sleep(rng.random() / 100)
        t.event(EPISODE_OUTPUT, {"episode_id": f"r:governed:{i}", "pipeline": [{"$count": f"n{i}"}],
                                 "confidence": i / 10})
        await asyncio.sleep(rng.random() / 100)
        t.signal(SIGNAL_CORRECT, i % 2 == 0)
        await asyncio.sleep(rng.random() / 100)
        t.finish(i * 100)

    async def main() -> None:
        await asyncio.gather(*(asyncio.create_task(one(i)) for i in range(6)))

    asyncio.run(main())
    begins = {kw["event_id"]: kw for kw in sdk.of("begin")}
    assert len(begins) == 6
    for i in range(6):
        b = begins[f"r:governed:{i}"]
        assert b["user_id"] == ("anna", "benny", "claire")[i % 3] and b["event"] == "episode"
        assert b["convo_id"] == "r:governed" and b["input"] == f"How many active customers in {2000 + i}?"
        assert b["properties"] == {"arm": "governed", "template": "active_count", "idx": i, "stream": "stream",
                                   "run_id": "r"}
    finishes = {kw["event_id"]: kw for kw in sdk.of("finish")}
    assert len(finishes) == 6
    for i in range(6):
        f = finishes[f"r:governed:{i}"]
        assert f["output"] == str(i * 100) and f["properties"] == {"confidence": i / 10}
        (att,) = f["attachments"]
        assert att["type"] == "code" and json.loads(att["value"]) == [{"$count": f"n{i}"}]
    signals = {kw["event_id"]: kw for kw in sdk.of("track_signal")}
    assert {e: s["sentiment"] for e, s in signals.items()} == {
        f"r:governed:{i}": "POSITIVE" if i % 2 == 0 else "NEGATIVE" for i in range(6)}
    assert t.counts["begun"] == t.counts["finished"] == 6 and not t.counts["errors"]


def test_signal_mapping(sdk: FakeRaindrop, keyed: Settings) -> None:
    t = trace(sdk, keyed)
    t.begin(episode(1))
    t.signal(SIGNAL_CORRECT, True)
    t.signal(SIGNAL_CORRECT, False)
    t.signal(SIGNAL_AUTHORITY_CORRECTION, 12.0, comment="That is not how active customers are counted.")
    t.signal(SIGNAL_AUTHORITY_CORRECTION, 12.0, comment=None)
    t.finish(10)
    t.signal(SIGNAL_CORRECT, True)   # after finish: no open episode
    s = sdk.of("track_signal")
    assert s[0] == {"event_id": "r:governed:1", "name": "correct", "signal_type": "default", "sentiment": "POSITIVE"}
    assert s[1]["sentiment"] == "NEGATIVE" and s[1]["signal_type"] == "default"
    assert s[2] == {"event_id": "r:governed:1", "name": "authority_correction", "signal_type": "feedback",
                    "comment": "That is not how active customers are counted.", "sentiment": "NEGATIVE"}
    assert len(s) == 3
    assert t.counts["skipped_no_comment"] == 1 and t.counts["signal_without_episode"] == 1


def test_a_missing_persona_is_skipped_and_counted(sdk: FakeRaindrop, keyed: Settings) -> None:
    t = trace(sdk, keyed)
    t.begin(episode(3, persona=None))
    t.event(EPISODE_OUTPUT, {"pipeline": [{"$count": "n"}], "confidence": 0.5})
    t.signal(SIGNAL_CORRECT, True)
    t.finish(4)
    t.begin(episode(4, persona="  "))
    assert not sdk.of("begin") and not sdk.of("finish") and not sdk.of("track_signal")
    assert t.counts["skipped_no_persona"] == 2


# --- events -------------------------------------------------------------------------------------------------


def test_event_filter_and_shape(sdk: FakeRaindrop, keyed: Settings) -> None:
    t = trace(sdk, keyed)
    sent = {"fire_raised": {"fire_id": "F-1", "decision_id": "D-1", "arm": "governed", "role": "dispositive"},
            "admission": {"decision_id": "D-2", "draft_id": "d-2", "kind": "taxonomic", "flips": []},
            "lifecycle.retired": {"decision_id": "D-1", "at_idx": 40, "reason": "idle", "released_views": []},
            "backtest": {"draft_id": "d-2", "arm": "governed", "verdict": "admit", "fixed": 3, "broken": 0,
                         "sampled": ["e1", "e2"], "replays": [{"episode_id": "e1", "with": 12, "without": 10}]},
            "draft.written": {"arm": "governed", "draft_id": "d-2", "title": "t"},
            "draft.adjudicated": {"arm": "governed", "draft_id": "d-2", "verdict": "admit", "layers": ["L0"]},
            "injection.started": {"job": "j1", "run_id": "r", "arm": "governed"}}
    local = ["consultation_set", "episode_written", "view.create", "round_closed", "observation.written"]
    for name, payload in sent.items():
        t.event(name, payload)
    for name in local:
        t.event(name, {"arm": "governed", "episode_id": "e"})
    calls = sdk.of("track_ai")
    assert [c["event"] for c in calls] == list(sent)
    assert all(c["user_id"] == "adjudicator" for c in calls)
    bt = calls[3]
    assert bt["convo_id"] == "r:governed" and bt["output"] == "admit"
    assert json.loads(bt["input"]) == {"draft_id": "d-2"}
    assert bt["properties"] == {"draft_id": "d-2", "arm": "governed", "verdict": "admit", "fixed": 3, "broken": 0,
                                "n_sampled": 2, "n_replays": 1}
    assert [a["name"] for a in bt["attachments"]] == ["sampled", "replays"]
    assert json.loads(bt["attachments"][1]["value"]) == [{"episode_id": "e1", "with": 12, "without": 10}]
    assert calls[2]["convo_id"] == "r" and calls[2]["output"] == "idle"     # no arm on lifecycle payloads
    assert calls[0]["output"] == "fire_raised" and calls[1]["attachments"] is None
    assert all(isinstance(v, str | int | float | bool) for c in calls for v in c["properties"].values())


def test_sdk_exceptions_are_swallowed_and_counted(sdk: FakeRaindrop, keyed: Settings) -> None:
    t = trace(sdk, keyed)
    sdk.raise_on = {"begin", "track_ai", "track_signal", "finish"}
    t.begin(episode(1))
    t.finish(1)
    sdk.raise_on = {"track_ai", "track_signal", "finish"}
    t.begin(episode(2))
    t.signal(SIGNAL_CORRECT, True)
    t.event("admission", {"decision_id": "D-1"})
    t.finish(2)
    assert t.counts["errors"] == 4
    assert {k: v for k, v in t.counts.items() if k.startswith("errors.")} == {
        "errors.begin": 1, "errors.signal": 1, "errors.event": 1, "errors.finish": 1}

    sdk.raise_on = {"init"}
    broken = RaindropTrace.create("raindrop", keyed)
    broken.begin(episode(3))
    broken.event("admission", {"decision_id": "D-1"})
    assert broken.counts["errors.init"] == 1 and len(sdk.of("begin")) == 1


def test_no_key_like_strings_reach_the_sdk(sdk: FakeRaindrop, keyed: Settings) -> None:
    t = trace(sdk, keyed)
    uri = "mongodb+srv://learner:hunter2@cluster0.example.net/db"
    ep = {**episode(1), "text": f"How many? {SECRET}", "api_key": SECRET}
    t.begin(ep)
    t.event(EPISODE_OUTPUT, {"pipeline": [{"$match": {"note": SECRET}}], "confidence": 0.9})
    t.signal(SIGNAL_AUTHORITY_CORRECTION, 12, comment=f"see {uri}")
    t.finish(f"answer {SECRET}")
    t.event("admission", {"decision_id": "D-1", "write_key": SECRET, "mongodb_uri": uri, "anthropic_auth_token": "x",
                          "world_truth": {"gold": 12}, "detail": {"voyage_api_key": "pa-123", "ok": f"sk-ant-{SECRET}"},
                          "reason": f"connect {uri}"})
    blob = json.dumps(sdk.calls, default=str)
    assert SECRET not in blob and "hunter2" not in blob and "mongodb+srv" not in blob and "pa-123" not in blob
    for word in ("api_key", "write_key", "mongodb_uri", "auth_token", "world_truth", "gold"):
        assert word not in blob, word
    assert "[redacted]" in blob


# --- trace invariance (SPEC § 21) ---------------------------------------------------------------------------


def _harness_trace(s: Settings, impl: str) -> Any:
    sel = s.model_copy(update={"trace_impl": impl})
    return Harness(settings=sel, store=None, arms=sel.arms()).trace()  # type: ignore[arg-type]


def _forward_run(t: Any) -> dict[str, Any]:
    from tests.test_forward import FakeStore, FakeWorld, arm, decision, forward
    from tests.test_forward_runner import runner

    store, world = FakeStore([decision(arm="hooks")]), FakeWorld()
    fp, _ = forward(store, arm())
    fp.trace = t
    asyncio.run(runner(store, world, fp, [], workers=1).run())
    return {"episodes": {k: e.model_dump(mode="json", exclude={"latency_ms"}) for k, e in store.episodes.docs.items()},
            "fires": {k: f.model_dump(mode="json") for k, f in store.fires.rows.items()},
            "decisions": [d.model_dump(mode="json") for d in store.decisions.rows],
            "refreshed": list(store.decisions.refreshed)}


def _adjudication_run(t: Any) -> dict[str, Any]:
    from tests.test_adjudication import World
    from tests.test_adjudication_fakes import draft

    w = World()
    w.trace = t
    w.store.st.events.clear()
    asyncio.run(w.adjudicator("governed").adjudicate(
        draft("d-gen", "Active customers hold the RULE status set.", w.sources), w.ctx()))
    st = w.store.st
    return {"decisions": {k: d.model_dump(mode="json") for k, d in st.decisions.items()},
            "drafts": {k: d.model_dump(mode="json") for k, d in st.drafts.items()},
            "backtests": {k: b.model_dump(mode="json") for k, b in st.backtests.items()}}


def test_trace_invariance_null_versus_jsonl_and_raindrop(sdk: FakeRaindrop, keyed: Settings) -> None:
    null, both = _harness_trace(keyed, "null"), _harness_trace(keyed, "jsonl,raindrop")
    assert isinstance(null, NullTrace) and isinstance(both, TeeTrace)

    a, b = _forward_run(null), _forward_run(both)
    assert a == b and a["episodes"] and a["fires"]
    assert sdk.of("begin") and sdk.of("finish") and sdk.of("track_signal") and sdk.of("track_ai")

    c, d = _adjudication_run(null), _adjudication_run(both)
    assert c == d and c["decisions"], "an admitted decision is written identically under either trace"
    assert any(kw["event"] == "admission" for kw in sdk.of("track_ai"))
    assert read_events(keyed.var_dir, keyed.run_id)
