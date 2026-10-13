"""voxentity CLI.

Exit codes: 0 completed, 1 quality gate failed, 2 invalid input/config,
3 missing dependency/resource. Partial runs still produce a report and exit
non-zero. stdout is JSON with --json; logs go to stderr.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from typing import Any

EXIT_OK = 0
EXIT_QUALITY_GATE = 1
EXIT_INVALID_INPUT = 2
EXIT_MISSING_DEP = 3

log = logging.getLogger("voxentity")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voxentity",
        description="VoxEntity-EU: exact spoken-entity capture evaluation (DE/FR).",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable stdout")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="preflight check for a compute profile")
    p.add_argument("--profile", choices=["local", "kaggle", "hf"], default="local")

    p = sub.add_parser("corpus", help="corpus lifecycle")
    csub = p.add_subparsers(dest="corpus_command", required=True)
    cb = csub.add_parser("build")
    cb.add_argument("--config", default="configs/corpus.yaml")
    cb.add_argument("--out", default="data/generated")
    cb.add_argument("--suite", choices=["main", "es"], default="main",
                    help="main = de/fr core corpus; es = separate extension suite")
    cv = csub.add_parser("validate")
    cv.add_argument("--manifest", required=True)
    cv.add_argument("--gold", required=True)
    cx = csub.add_parser("export-inputs")
    cx.add_argument("--manifest", required=True)
    cx.add_argument("--out", required=True)

    p = sub.add_parser("synthesize", help="run TTS over the manifest")
    p.add_argument("--manifest", required=True)
    p.add_argument("--profile", default="qwen")
    p.add_argument("--resume", action="store_true")

    p = sub.add_parser("qa", help="automated audio QA")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("transform", help="apply the telephone channel recipe")
    p.add_argument("--manifest", required=True)
    p.add_argument("--recipe", default="configs/channel.yaml")
    p.add_argument("--resume", action="store_true")

    p = sub.add_parser("run", help="inference run over isolated inputs")
    p.add_argument("--inputs", required=True)
    p.add_argument("--system", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--resume", action="store_true")

    p = sub.add_parser("score", help="deterministic offline scoring")
    p.add_argument("--gold", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("compare", help="paired comparison of two scored runs")
    p.add_argument("runs", nargs=2)
    p.add_argument("--out", required=True)

    p = sub.add_parser("human-control", help="build the FLEURS human control")
    p.add_argument("--source-lock", default="research/artifacts.json")
    p.add_argument("--out", required=True)

    p = sub.add_parser("export", help="export to external formats")
    esub = p.add_subparsers(dest="export_command", required=True)
    ev = esub.add_parser("voice-evals")
    ev.add_argument("--manifest", required=True)
    ev.add_argument("--voice-id", required=True)
    ev.add_argument("--condition", required=True)
    ev.add_argument("--out", required=True)

    p = sub.add_parser("report", help="render tables and findings from frozen results")
    p.add_argument("--results", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("release", help="release controls")
    rsub = p.add_subparsers(dest="release_command", required=True)
    rv = rsub.add_parser("validate")
    rv.add_argument("--bundle", required=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    from . import commands

    try:
        result = commands.dispatch(args)
    except commands.InvalidInput as exc:
        log.error("invalid input: %s", exc)
        return _emit(args, {"status": "invalid_input", "error": str(exc)}, EXIT_INVALID_INPUT)
    except commands.MissingDependency as exc:
        log.error("missing dependency: %s", exc)
        return _emit(args, {"status": "missing_dependency", "error": str(exc)}, EXIT_MISSING_DEP)
    except commands.QualityGateFailed as exc:
        log.error("quality gate failed: %s", exc)
        return _emit(args, {"status": "quality_gate_failed", "error": str(exc)}, EXIT_QUALITY_GATE)
    return _emit(args, result, EXIT_OK)


def _emit(args: argparse.Namespace, payload: dict[str, Any], code: int) -> int:
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, default=str))
    else:
        for key, value in payload.items():
            print(f"{key}: {value}")
    return code


if __name__ == "__main__":
    sys.exit(main())
