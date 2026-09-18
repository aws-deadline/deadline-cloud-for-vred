# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Guards the dependency declaration that AWS Console sign-in depends on.

Console sign-in is not exercised by the integration tests: it needs an interactive
browser OAuth handshake and Deadline Cloud Monitor, while CI authenticates by
assuming a role, so credentials are host-provided and the console path is never
taken. What can break silently is the dependency declaration, which is what this
test pins.

The test reads ``pyproject.toml`` rather than installed distribution metadata.
``importlib.metadata`` reflects what was captured at install time, so an edit to
``pyproject.toml`` would not be seen until the environment is reinstalled -- and
"somebody edited that line" is precisely the regression being guarded.

The test above guards the negative side: the floor itself must exclude releases with no
console sign-in support. The tests below guard the positive side -- that
``_add_console_extra`` adds the extra correctly, that ``_build_base_environment`` still
passes it to pip, and that ``NATIVE_DEPENDENCIES`` still carries awscrt and pyyaml -- so that
removing any of those silently breaks console sign-in in the shipped bundle without failing
the negative-side test above.
"""

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from packaging.requirements import Requirement

SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    # Appended rather than prepended: scripts/ holds generically named modules (common.py),
    # and prepending would shadow any same-named import for the rest of the pytest session.
    sys.path.append(str(SCRIPTS_DIR))

import deps_bundle  # importable only after the sys.path append above

PYPROJECT = Path(__file__).parents[2] / "pyproject.toml"

# Console sign-in landed in deadline 0.60.4 and nowhere earlier: 0.60.1 through
# 0.60.3 have no AWS_CONSOLE_LOGIN credentials source and do not declare a
# `console` extra at all. 0.60.3 is the highest version that must be excluded.
HIGHEST_DEADLINE_WITHOUT_CONSOLE_SIGNIN = "0.60.3"


def test_deadline_floor_excludes_releases_without_console_signin():
    """Guards the floor itself, not whatever a resolver happened to select.

    An installed-version check cannot do this: with a loosened ">= 0.60.1"
    requirement, pip still resolves the newest 0.60.x, so the regression passes
    unnoticed. The floor matters beyond feature availability: requesting the
    console extra against a release that does not declare it makes pip silently
    backtrack to one without it, dropping awscrt with only a warning.
    """
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    requirements = [Requirement(r) for r in pyproject["project"]["dependencies"]]
    deadline_requirements = [r for r in requirements if r.name == "deadline"]

    assert deadline_requirements, "pyproject.toml declares no requirement on deadline"
    for requirement in deadline_requirements:
        assert not requirement.specifier.contains(HIGHEST_DEADLINE_WITHOUT_CONSOLE_SIGNIN), (
            f"allows deadline {HIGHEST_DEADLINE_WITHOUT_CONSOLE_SIGNIN}, which has no "
            f"console sign-in support: {requirement}"
        )


def test_native_dependencies_include_awscrt_and_pyyaml():
    """Pins the packages deps_bundle.py fetches per-version for their compiled artifacts.

    Console sign-in needs awscrt to be importable under whichever Python VRED embeds; pyyaml
    needs the same because it silently falls back to a pure-Python parser otherwise. Dropping
    either from NATIVE_DEPENDENCIES would ship a bundle where a subset of interpreters cannot
    load one of them, with nothing here to catch it.
    """
    assert "awscrt" in deps_bundle.NATIVE_DEPENDENCIES
    assert "pyyaml" in deps_bundle.NATIVE_DEPENDENCIES


def test_build_base_environment_requests_the_console_extra(tmp_path, monkeypatch):
    """Pins the positive half of the console sign-in fix: the extra actually reaches pip.

    test_deadline_floor_excludes_releases_without_console_signin guards the floor pyproject.toml
    declares; this guards that _build_base_environment still adds the console extra back
    before invoking pip, mirroring the subprocess.run monkeypatch already used in
    test_deps_bundle_native_merge.py. If the _add_console_extra call here were dropped, that
    other test would stay green while the shipped bundle silently lost console sign-in.
    """
    captured_args: list[str] = []

    def record(args, **kwargs):
        captured_args.extend(args)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(deps_bundle.subprocess, "run", record)

    deps_bundle._build_base_environment(tmp_path, ["deadline>=0.60.4,<0.61", "xxhash"])

    console_reqs = [arg for arg in captured_args if arg.lower().startswith("deadline[")]
    assert console_reqs, f"no deadline requirement with an extra was passed to pip: {captured_args}"
    assert "console" in console_reqs[0], f"console extra missing from pip argv: {console_reqs[0]}"


@pytest.mark.parametrize(
    "requirement,expected",
    [
        ("deadline>=0.60.4,<0.61", "deadline[console]>=0.60.4,<0.61"),
        ("deadline[gui]>=0.60.4", "deadline[gui,console]>=0.60.4"),
        ("deadline[gui,console]>=0.60.4", "deadline[gui,console]>=0.60.4"),
        ("deadline[console]>=0.60.4", "deadline[console]>=0.60.4"),
        ("xxhash>=3.0", "xxhash>=3.0"),
    ],
)
def test_add_console_extra_pins_behavior(requirement, expected):
    """Pins _add_console_extra's contract: preserve existing extras, be idempotent, and leave
    non-deadline requirements untouched.
    """
    assert deps_bundle._add_console_extra(requirement) == expected


def test_add_console_extra_changes_the_real_base_dependencies():
    """Stronger than the parametrized behavior test above: proves the injection takes effect
    against pyproject.toml's actual dependencies, not just a synthetic requirement string.

    ``_add_console_extra`` no-ops on any requirement it does not recognize as ``deadline``. If
    that requirement were ever renamed, wrapped, or split -- say the base dependency became
    ``deadline-cloud`` -- this test fails, whereas test_add_console_extra_pins_behavior above
    would keep passing forever since it never exercises the real declaration. A rename passing
    silently is exactly how the bundle would ship with no awscrt and no build-time signal.
    """
    pyproject_dict = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = deps_bundle._get_dependencies(pyproject_dict)
    dependencies_for_pip = [deps_bundle._add_console_extra(dep) for dep in dependencies]

    assert dependencies_for_pip != dependencies, (
        "_add_console_extra left every real base dependency unchanged; the `deadline` "
        "requirement it targets may have been renamed, wrapped, or removed from "
        "project.dependencies"
    )
