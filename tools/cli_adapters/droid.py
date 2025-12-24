"""
Factory.ai Droid CLI adapter for sf-skills.

Droid CLI (v0.26.0+) natively supports Claude Code skills format:
- Skills location: .factory/skills/{name}/ or ~/.factory/skills/{name}/
- Uses standard Agent Skills format (SKILL.md + scripts/)
- Can also import from .claude/skills/ directory

Droid CLI is highly compatible with Claude Code, requiring minimal transformation.
"""

from pathlib import Path
from typing import Optional

from .base import CLIAdapter, SkillOutput


class DroidAdapter(CLIAdapter):
    """
    Adapter for Factory.ai Droid CLI.

    Droid CLI follows Claude Code's skill format closely.
    Skills are installed to .factory/skills/ by default.
    """

    @property
    def cli_name(self) -> str:
        return "droid"

    @property
    def default_install_path(self) -> Path:
        """
        Default to project-level .factory/skills/ directory.

        Droid CLI checks:
        1. .factory/skills/{name}/ (project scope)
        2. ~/.factory/skills/{name}/ (user scope)
        3. .claude/skills/{name}/ (Claude Code compatibility)
        """
        cwd = Path.cwd()
        return cwd / ".factory" / "skills"

    def transform_skill_md(self, content: str, skill_name: str) -> str:
        """
        Transform SKILL.md for Droid CLI compatibility.

        Droid CLI is highly compatible with Claude Code, so
        minimal transformation is needed.
        """
        # Apply common transformations
        content = self._common_skill_md_transforms(content)

        # Add Droid-specific section
        droid_section = f"""

---

## Droid CLI Usage

This skill is compatible with Factory.ai Droid CLI (v0.26.0+). To use:

```bash
# Skills are auto-discovered from .factory/skills/{skill_name}/
# Use the /skills command to manage skills

# To run validation scripts manually:
cd .factory/skills/{skill_name}/scripts
python validate_*.py path/to/your/file
```

### Features

Droid CLI with this skill provides:
- Claude Code skills compatibility
- Auto-discovery from .claude/skills/ directory
- Self-healing and auto-debugging capabilities
- Custom Droids for specialized workflows

### Enabling Skills

Ensure Custom Droids are enabled:
```bash
# Via settings
/settings → Experimental → Custom Droids

# Or add to ~/.factory/settings.json
{{"enableCustomDroids": true}}
```

See `scripts/README.md` for validation script usage.
"""

        # Only add if not already present
        if "## Droid CLI Usage" not in content:
            content += droid_section

        return content

    def transform_skill(self, source_dir: Path) -> SkillOutput:
        """
        Transform skill for Droid CLI.

        Bundles shared modules for self-contained installation.
        """
        # Get base transformation
        output = super().transform_skill(source_dir)

        # Bundle shared modules if scripts reference them
        if self._needs_shared_modules(output.scripts):
            shared_modules = self._bundle_shared_modules()
            for path, content in shared_modules.items():
                output.scripts[f"shared/{path}"] = content

        return output

    def _needs_shared_modules(self, scripts: dict) -> bool:
        """Check if any scripts import from shared/ modules."""
        for content in scripts.values():
            if isinstance(content, str):
                if "from shared" in content or "import shared" in content:
                    return True
                if "lsp_client" in content or "code_analyzer" in content:
                    return True
        return False

    def _bundle_shared_modules(self) -> dict:
        """Bundle shared modules for self-contained installation."""
        modules = {}

        # Bundle lsp-engine
        lsp_dir = self.shared_dir / "lsp-engine"
        if lsp_dir.exists():
            for file_path in lsp_dir.rglob("*.py"):
                rel_path = file_path.relative_to(self.shared_dir)
                content = file_path.read_text(encoding='utf-8')
                modules[str(rel_path)] = content

        # Bundle code_analyzer
        analyzer_dir = self.shared_dir / "code_analyzer"
        if analyzer_dir.exists():
            for file_path in analyzer_dir.rglob("*.py"):
                rel_path = file_path.relative_to(self.shared_dir)
                content = file_path.read_text(encoding='utf-8')
                modules[str(rel_path)] = content

            for file_path in analyzer_dir.rglob("*.yml"):
                rel_path = file_path.relative_to(self.shared_dir)
                modules[str(rel_path)] = file_path.read_text(encoding='utf-8')

            for file_path in analyzer_dir.rglob("*.xml"):
                rel_path = file_path.relative_to(self.shared_dir)
                modules[str(rel_path)] = file_path.read_text(encoding='utf-8')

        return modules
