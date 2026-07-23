"""Rewrite the lower bounds in pyproject.toml to match the versions resolved in uv.lock.

uv resolves `>=` constraints to the newest compatible release, so the lock file is always
ahead of the bounds declared in pyproject.toml. This realigns the two so the declared
floors reflect what is actually being installed and tested.
"""

import re
import tomllib
from pathlib import Path

root = Path(__file__).resolve().parent.parent
pyproject_path = root / "pyproject.toml"
lock_path = root / "uv.lock"


def canonical(name: str) -> str:
    """Normalize a distribution name per PEP 503 so pyproject and uv.lock names line up."""
    return re.sub(r"[-_.]+", "-", name).lower()


locked = {canonical(p["name"]): p["version"] for p in tomllib.loads(lock_path.read_text())["package"]}
dependencies = tomllib.loads(pyproject_path.read_text())["project"]["dependencies"]

content = pyproject_path.read_text()
bumped = 0
for dependency in dependencies:
    match = re.fullmatch(r"([A-Za-z0-9._-]+)(\[[^\]]*\])?>=([^,;\s]+)", dependency)
    if match is None:
        print(f"skipped {dependency} (not a plain >= constraint)")
        continue

    name, extras, bound = match.group(1), match.group(2) or "", match.group(3)
    version = locked.get(canonical(name))
    if version is None:
        print(f"skipped {name} (not found in uv.lock)")
        continue
    if version == bound:
        continue

    content = content.replace(f'"{dependency}"', f'"{name}{extras}>={version}"')
    print(f"{name} >={bound} -> >={version}")
    bumped += 1

if bumped:
    pyproject_path.write_text(content)
    print(f"bumped {bumped} constraint(s) in pyproject.toml")
else:
    print("all constraints already match uv.lock")
