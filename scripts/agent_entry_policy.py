"""Check that each current and future project has a copyable Agent entry."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SUPPORT = {"docs", "scripts", "tests"}


def check() -> list[str]:
    errors = []
    overview = (ROOT / "README.md").read_text(encoding="utf-8")
    for project in sorted(ROOT.iterdir()):
        if not project.is_dir() or project.name.startswith(".") or project.name in SUPPORT:
            continue
        readme = project / "README.md"
        install = project / "INSTALL.md"
        if not readme.exists() or not install.exists():
            errors.append(f"{project.name}: README.md and INSTALL.md are required")
            continue
        text = readme.read_text(encoding="utf-8")
        if "## 直接让 Agent 帮你使用" not in text:
            errors.append(f"{project.name}: missing Agent entry heading")
        prompts = re.findall(r"```text\s*\n(.*?)```", text, flags=re.S)
        if not any(project.name in p and "INSTALL.md" in p and "https://github.com/strive822/zyd-vibe-lab" in p for p in prompts):
            errors.append(f"{project.name}: missing copyable Agent prompt with repository, project and INSTALL.md")
        if f"{project.name}/INSTALL.md" not in overview:
            errors.append(f"{project.name}: missing root README installation link")
    return errors


if __name__ == "__main__":
    errors = check()
    for error in errors:
        print("FAIL", error)
    print("FAIL" if errors else "PASS: all projects have copyable Agent entries")
    raise SystemExit(bool(errors))
