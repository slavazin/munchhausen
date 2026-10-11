"""Forward-pass commands (S2, M2): `run`, `episode`, `seed-vocab`, `isolation`."""

from __future__ import annotations

import asyncio
import json
import logging
from itertools import islice
from typing import Any

import typer

from munchhausen.bootstrap import Harness, harness

log = logging.getLogger("munchhausen.forward")


def _echo(obj: Any) -> None:
    typer.echo(json.dumps(obj, indent=2, default=str))


async def _start_run(h: Harness, length: int | None = None) -> None:
    from munchhausen import evidence

    try:
        await evidence.start_run(h, length=length)
    except NotImplementedError as e:
        log.error("RUN RECORD NOT WRITTEN (%s): this run has no pre-registered `runs` row", e)


async def _finish_run(h: Harness) -> None:
    from munchhausen import evidence

    try:
        await evidence.finish_run(h)
    except Exception as e:  # noqa: BLE001 - a failed stamp is logged; it never masks the run's own error
        log.error("RUN END NOT STAMPED (%s: %s)", type(e).__name__, e)


async def run_arms(h: Harness, arms: list[str], length: int | None) -> dict[str, Any]:
    """Every arm concurrently over one World; one arm's failure is reported, never cancels the others."""
    await _start_run(h, length)
    # the vocabulary precedes the first episode: hooks, the nominator and the escape all read `terms`.
    # Idempotent (terms upsert by name; the same seed mines the same phrases), so a resume re-runs it safely.
    log.info("seed-vocab: %s", {k: v for k, v in (await seed_vocab(h)).items() if k != "sample"})
    world = await h.ready_world()
    runners = {a: h.arm_runner(a, world) for a in arms}
    results = await asyncio.gather(*(r.run(length) for r in runners.values()), return_exceptions=True)
    out: dict[str, Any] = {}
    for arm, res in zip(runners, results, strict=True):
        if isinstance(res, BaseException):
            log.error("[%s] stopped: %s: %s", arm, type(res).__name__, res, exc_info=res)
            out[arm] = {"error": f"{type(res).__name__}: {res}"}
        else:
            out[arm] = res
    return out


async def seed_vocab(h: Harness) -> dict[str, Any]:
    """Seed `terms` from the schema summary and the first VOCAB_WARMUP stream questions (never the pack)."""
    from munchhausen.agent.terms import seed_terms

    s, world = h.settings, await h.ready_world()
    questions = list(islice(world.questions(s.stream_seed), s.vocab_warmup))
    rows = seed_terms(world.schema_summary(), questions, min_questions=s.vocab_min_questions,
                      max_tokens=s.vocab_max_phrase_tokens, run_id=s.run_id)
    for t in rows:
        await h.store.terms.add(t)
    synonyms = await h.store.terms.compile_synonyms()
    by_source = {src: sum(t.source == src for t in rows) for src in ("schema", "question")}
    sample = sorted(t.term for t in rows)[: s.vocab_report_sample]
    return {"terms": len(rows), "by_source": by_source, "synonym_mappings": synonyms, "sample": sample}


def register(app: typer.Typer) -> None:
    @app.command("run")
    def run_cmd(arm: list[str] = typer.Option(None, "--arm", help="Arm(s) to run; default every arm."),  # noqa: B008
                length: int = typer.Option(None, "--length", help="Stream length (default RUN_LENGTH).")) -> None:
        """Run arms concurrently: cursor claim → lease → forward pass → round barrier → round close. Resumes
        an existing RUN_ID from its cursors."""
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

        async def go() -> None:
            h = harness()
            try:
                chosen = arm or [a for a in h.arms]
                unknown = set(chosen) - set(h.arms)
                if unknown:
                    raise typer.BadParameter(f"unknown arms: {sorted(unknown)}")
                try:
                    _echo({"run_id": h.settings.run_id, "ports": {a: h.selection()[a] for a in chosen},
                           "results": await run_arms(h, chosen, length)})
                finally:
                    await _finish_run(h)
            finally:
                await h.close()
        asyncio.run(go())

    @app.command("episode")
    def episode_cmd(arm: str = typer.Option("frozen", "--arm"), idx: int = typer.Option(0, "--idx")) -> None:
        """Run one stream question through the forward pass and print the episode. Debug: it writes under
        the run id `debug-<RUN_ID>`, never into a run's own records."""
        logging.basicConfig(level=logging.INFO)

        async def go() -> None:
            from munchhausen.config import settings

            base = settings()
            h = harness(base.model_copy(update={"run_id": f"{base.debug_run_prefix}{base.run_id}"}))
            try:
                world = await h.ready_world()
                question = next(islice(world.questions(h.settings.stream_seed), idx, None))
                ep = await h.forward_pass(arm, world).run(idx, question)
                _echo(ep.model_dump(mode="json", by_alias=True))
            finally:
                await h.close()
        asyncio.run(go())

    @app.command("seed-vocab")
    def seed_vocab_cmd() -> None:
        """Seed the term vocabulary from the schema summary and warmup questions; compile synonyms."""
        async def go() -> None:
            h = harness()
            try:
                _echo(await seed_vocab(h))
            finally:
                await h.close()
        asyncio.run(go())

    @app.command("isolation")
    def isolation_cmd() -> None:
        """Report `isolation: roles|convention` and which databases each role's connection reaches."""
        from munchhausen.config import settings
        from munchhausen.store.atlas import role_reach

        _echo(asyncio.run(role_reach(settings())))

    @app.command("verify-roles")
    def verify_roles_cmd() -> None:
        """Probe each database role's allowed and forbidden operations live; `isolation: roles` only when
        every cell matches SPEC § 20.2 and the four connections are distinct users."""
        from munchhausen.config import settings
        from munchhausen.store.atlas import verify_roles

        _echo(asyncio.run(verify_roles(settings())))
