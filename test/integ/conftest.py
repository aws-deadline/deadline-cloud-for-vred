# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def sync_machine_env_vars():
    """
    On Windows, read machine-level environment variables from the registry
    and merge any missing ones into the current process's os.environ.

    Machine-level env vars (e.g. VREDPRO set by the VRED installer) live in
    the registry. A running process only sees them if it was started AFTER
    they were written, AND the parent process propagated them. In CI
    (CodeBuild), the agent process may have been started before the installer
    ran, so its children never inherit the new vars even though they exist in
    the registry.
    """
    if os.name != "nt":
        return

    import winreg  # type: ignore[import-not-found]

    try:
        with winreg.OpenKey(  # type: ignore[attr-defined]
            winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)  # type: ignore[attr-defined]
                    if name not in os.environ:
                        os.environ[name] = value
                        print(f"Synced machine env var: {name}={value}")
                    i += 1
                except OSError:
                    break
    except OSError as e:
        print(f"WARNING: Could not read machine env vars from registry: {e}")
