# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

"""Guards which compiled artifact the dependency bundle ships for each interpreter.

The bundle is one flat ``PYTHONPATH`` directory, so it holds a single file per name no
matter how many Python versions VRED might embed. When two per-version installs supply the
same filename, only one survives the merge, and a copy built for a newer Python fails to
import on an older one.

These tests drive the merge over synthetic trees named like the real wheels' extension
modules. They assert which artifact is selected, not that it loads -- that needs the target
interpreter, which the unit suite has no access to.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    # Appended rather than prepended: scripts/ holds generically named modules (common.py),
    # and prepending would shadow any same-named import for the rest of the pytest session.
    sys.path.append(str(SCRIPTS_DIR))

import deps_bundle

# awscrt's abi3 wheels all install this one name, whatever Python they were built for.
ABI3_ARTIFACT = "_awscrt.abi3.so"

# awscrt ships a version-specific wheel through this version and abi3 wheels above it.
AWSCRT_LAST_NON_ABI3_VERSION = "3.10"

# Stands in for the copy the base environment resolved for the build host's own
# interpreter, which is not necessarily a version the bundle targets.
BASE_ENV_SENTINEL = "build-host"


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _tag(version: str) -> str:
    """The interpreter tag a wheel puts in a version-specific extension module name."""
    return version.replace(".", "")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.fixture
def supported_versions() -> list[str]:
    versions = sorted(deps_bundle.SUPPORTED_PYTHON_VERSIONS, key=_version_key)
    assert len(versions) >= 2, "a filename collision needs at least two supported versions"
    return versions


@pytest.fixture
def merged_bundle(tmp_path, supported_versions) -> Path:
    """Run the merge over trees named the way the real wheels name their artifacts.

    awscrt is version-specific through AWSCRT_LAST_NON_ABI3_VERSION and shares the abi3 name
    above it; xxhash and pyyaml are version-specific for every version; psutil ships one
    shared abi3 wheel, so every tree holds identical bytes for it. Each file's content
    records which version produced it. The base environment is seeded with a sentinel
    standing in for the build host's own interpreter.
    """
    base_env = tmp_path / "base_env"
    _write(base_env / ABI3_ARTIFACT, BASE_ENV_SENTINEL)

    boundary = _version_key(AWSCRT_LAST_NON_ABI3_VERSION)
    assert any(_version_key(v) <= boundary for v in supported_versions) and any(
        _version_key(v) > boundary for v in supported_versions
    ), (
        "AWSCRT_LAST_NON_ABI3_VERSION needs supported versions on both sides of it for this "
        "fixture to exercise both the version-specific and the abi3-collision case"
    )

    native_paths = []
    for version in supported_versions:
        tree = tmp_path / "native" / _tag(version)
        native_paths.append(tree)
        if _version_key(version) <= boundary:
            _write(tree / f"_awscrt.cpython-{_tag(version)}-darwin.so", version)
        else:
            _write(tree / ABI3_ARTIFACT, version)
        _write(tree / "xxhash" / f"_xxhash.cpython-{_tag(version)}-darwin.so", version)
        _write(tree / "yaml" / f"_yaml.cpython-{_tag(version)}-darwin.so", version)
        _write(tree / "psutil" / "_psutil_osx.abi3.so", "shared")

    deps_bundle._copy_native_to_base_env(base_env, native_paths)
    return base_env


def test_colliding_abi3_artifact_comes_from_the_lowest_supported_abi(
    merged_bundle, supported_versions
):
    """abi3 is forward-compatible only, so the lowest supported version's copy must win.

    A copy built for a newer Python fails to import on an older one -- botocore then leaves
    its crypto binding unset, and Console sign-in reports sign-in is needed indefinitely.
    """
    lowest_abi3_version = min(
        (
            version
            for version in supported_versions
            if _version_key(version) > _version_key(AWSCRT_LAST_NON_ABI3_VERSION)
        ),
        key=_version_key,
    )
    shipped = (merged_bundle / ABI3_ARTIFACT).read_text()

    assert shipped != BASE_ENV_SENTINEL, (
        f"{ABI3_ARTIFACT} is the copy the base environment resolved for the build host's "
        f"interpreter, which is not a version the bundle targets"
    )
    assert shipped == lowest_abi3_version, (
        f"{ABI3_ARTIFACT} was built for Python {shipped}, so it cannot be imported by "
        f"Python {lowest_abi3_version}; the copy built for the lowest supported abi3 "
        f"version is the one every supported interpreter can load"
    )


def test_version_specific_artifacts_are_kept_for_every_supported_version(
    merged_bundle, supported_versions
):
    """Version-specific names never collide, so every supported version keeps its copy."""
    for version in supported_versions:
        for package, module in (("xxhash", "_xxhash"), ("yaml", "_yaml")):
            artifact = merged_bundle / package / f"{module}.cpython-{_tag(version)}-darwin.so"
            assert (
                artifact.exists()
            ), f"the bundle carries no {package} artifact for Python {version}"
            assert artifact.read_text() == version

    for version in supported_versions:
        if _version_key(version) > _version_key(AWSCRT_LAST_NON_ABI3_VERSION):
            continue
        awscrt_non_abi3 = merged_bundle / f"_awscrt.cpython-{_tag(version)}-darwin.so"
        assert (
            awscrt_non_abi3.exists()
        ), f"the bundle carries no awscrt artifact for Python {version}"


def test_native_trees_are_merged_lowest_python_version_first(tmp_path, monkeypatch):
    """Downloads happen in ascending numeric order (string-sort would put "3.9" after "3.10")."""
    monkeypatch.setattr(deps_bundle, "SUPPORTED_PYTHON_VERSIONS", ["3.13", "3.9", "3.11", "3.10"])
    monkeypatch.setattr(deps_bundle, "_get_package_version", lambda package, install_path: "1.2.3")

    requested_versions: list[str] = []

    def record(args, **kwargs):
        requested_versions.append(args[args.index("--python-version") + 1])
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(deps_bundle.subprocess, "run", record)

    tree_paths = deps_bundle._download_native_dependencies(tmp_path, tmp_path / "base_env")

    assert requested_versions == ["3.9", "3.10", "3.11", "3.13"]
    assert [path.name for path in tree_paths] == ["3_9", "3_10", "3_11", "3_13"]


def test_get_package_version_matches_pip_list_casing(monkeypatch):
    """`pip list` prints the distribution's own casing (`PyYAML`), not the requirement's."""
    output = b"Package  Version\n-------- -------\nPyYAML   6.0.3\nxxhash   3.6.0\n"
    monkeypatch.setattr(
        deps_bundle.subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, 0, stdout=output),
    )

    assert deps_bundle._get_package_version("pyyaml", Path("/unused")) == "6.0.3"
