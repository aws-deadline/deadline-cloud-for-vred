@echo off
for %%f in (test_*.py) do (
    echo Running tests in %%f
    python -m pytest %%f
)