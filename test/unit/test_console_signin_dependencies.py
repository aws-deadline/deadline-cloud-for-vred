# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Guards the dependency declaration that AWS Console sign-in depends on.

Console sign-in is not exercised by the integration tests: CI authenticates by assuming a
role, so the console path is never taken there. What can break silently is the dependency
declaration, which is what these tests pin.

Reads ``pyproject.toml`` directly rather than installed distribution metadata, since
``importlib.metadata`` would not see an edit until the environment is reinstalled.

Splits into a negative guard (the floor must exclude releases with no console sign-in
support) and a positive guard (the extra must still reach pip via ``_add_console_extra``
and ``_build_base_environment``, and ``NATIVE_DEPENDENCIES`` must still be correct).
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

# 0.60.1-0.60.3 have no AWS_CONSOLE_LOGIN credentials source and declare no `console`
# extra; 0.60.3 is the highest version that must stay excluded.
HIGHEST_DEADLINE_WITHOUT_CONSOLE_SIGNIN = "0.60.3"


def test_deadline_floor_excludes_releases_without_console_signin():
    """Pins the declared deadline floor, independent of whatever a resolver selects."""
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
    """Pins that awscrt and pyyaml stay in NATIVE_DEPENDENCIES."""
    assert "awscrt" in deps_bundle.NATIVE_DEPENDENCIES
    assert "pyyaml" in deps_bundle.NATIVE_DEPENDENCIES


def test_build_base_environment_requests_the_console_extra(tmp_path, monkeypatch):
    """Pins that _build_base_environment passes the console extra to pip."""
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
    """Pins _add_console_extra's contract: preserve extras, be idempotent, ignore others."""
    assert deps_bundle._add_console_extra(requirement) == expected


def test_add_console_extra_changes_the_real_base_dependencies():
    """Pins that _add_console_extra actually changes pyproject.toml's real dependencies,
    not just a synthetic requirement string like the parametrized test above.
    """
    pyproject_dict = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = deps_bundle._get_dependencies(pyproject_dict)
    dependencies_for_pip = [deps_bundle._add_console_extra(dep) for dep in dependencies]

    assert dependencies_for_pip != dependencies, (
        "_add_console_extra left every real base dependency unchanged; the `deadline` "
        "requirement it targets may have been renamed, wrapped, or removed from "
        "project.dependencies"
    )
