"""Command implementations behind the CLI.

Each command returns a dict for stdout. Raise InvalidInput / MissingDependency /
QualityGateFailed to map onto exit codes 2 / 3 / 1.
"""

from __future__ import annotations

import argparse
from typing import Any


class InvalidInput(Exception):
    pass


class MissingDependency(Exception):
    pass


class QualityGateFailed(Exception):
    pass


def dispatch(args: argparse.Namespace) -> dict[str, Any]:
    cmd = args.command
    if cmd == "doctor":
        from .doctor import run_doctor

        return run_doctor(args.profile)
    if cmd == "corpus":
        from .corpus.export_inputs import cli_export_inputs
        from .corpus.generate import cli_build
        from .corpus.validate import cli_validate

        if args.corpus_command == "build":
            suite = getattr(args, "suite", "main")
            out = args.out
            if suite == "es" and out == "data/generated":
                out = "data/ext/es"
            return cli_build(args.config, out, suite=suite)
        if args.corpus_command == "validate":
            return cli_validate(args.manifest, args.gold)
        if args.corpus_command == "export-inputs":
            return cli_export_inputs(args.manifest, args.out)
        raise InvalidInput(f"unknown corpus command {args.corpus_command}")
    if cmd == "synthesize":
        from .audio.synthesize import cli_synthesize

        return cli_synthesize(args.manifest, args.profile, resume=args.resume)
    if cmd == "qa":
        from .audio.qa import cli_qa

        return cli_qa(args.manifest, args.out)
    if cmd == "transform":
        from .audio.channel import cli_transform

        return cli_transform(args.manifest, args.recipe, resume=args.resume)
    if cmd == "run":
        from .runner import cli_run

        return cli_run(args.inputs, args.system, args.out, resume=args.resume)
    if cmd == "score":
        from .scoring.match import IncompleteRun, cli_score

        try:
            return cli_score(args.gold, args.predictions, args.manifest, args.out)
        except IncompleteRun as exc:
            raise QualityGateFailed(
                f"incomplete run ({len(exc.missing)} missing rows); report written, not ranked"
            ) from exc
    if cmd == "compare":
        from .scoring.aggregate import cli_compare

        return cli_compare(args.runs[0], args.runs[1], args.out)
    if cmd == "human-control":
        from .corpus.human_control import cli_human_control

        return cli_human_control(args.source_lock, args.out)
    if cmd == "export" and args.export_command == "voice-evals":
        from .adapters.voice_evals_export import cli_export_voice_evals

        return cli_export_voice_evals(args.manifest, args.voice_id, args.condition, args.out)
    if cmd == "report":
        from .reporting.render import cli_report

        return cli_report(args.results, args.out)
    if cmd == "release" and args.release_command == "validate":
        from .release import cli_release_validate

        return cli_release_validate(args.bundle)
    raise InvalidInput(f"unknown command {cmd}")
