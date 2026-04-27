"""Configuration system for Traktor Collection Tools."""

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


CONFIG_DIR = Path.home() / ".traktor-tools"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class SearchRoot:
    path: str
    max_depth: int = 3


@dataclass
class PathMapping:
    from_prefix: str
    to_prefix: str
    reason: str = ""


@dataclass
class Config:
    traktor_nml: str = ""
    search_roots: list[SearchRoot] = field(default_factory=list)
    path_mappings: list[PathMapping] = field(default_factory=list)


def get_default_config() -> Config:
    default_traktor_nml = str(Path.home() / "Documents" / "Native Instruments" / "Traktor 4.1.0" / "collection.nml")
    return Config(
        traktor_nml=default_traktor_nml,
        search_roots=[
            SearchRoot(path=str(Path.home() / "Music"), max_depth=3),
        ],
        path_mappings=[],
    )


def config_to_dict(cfg: Config) -> dict:
    result = {
        "paths": {
            "traktor_nml": cfg.traktor_nml,
        }
    }
    if cfg.search_roots:
        result["paths"]["search_roots"] = [
            {"path": sr.path, "max_depth": sr.max_depth}
            for sr in cfg.search_roots
        ]
    if cfg.path_mappings:
        result["paths"]["mappings"] = [
            {"from_prefix": pm.from_prefix, "to_prefix": pm.to_prefix, "reason": pm.reason}
            for pm in cfg.path_mappings
        ]
    return result


def dict_to_config(d: dict) -> Config:
    paths = d.get("paths", {})
    traktor_nml = paths.get("traktor_nml", "")

    search_roots = []
    for sr in paths.get("search_roots", []):
        if isinstance(sr, dict):
            search_roots.append(SearchRoot(
                path=sr.get("path", ""),
                max_depth=sr.get("max_depth", 3),
            ))

    path_mappings = []
    for pm in paths.get("mappings", []):
        if isinstance(pm, dict):
            path_mappings.append(PathMapping(
                from_prefix=pm.get("from_prefix", ""),
                to_prefix=pm.get("to_prefix", ""),
                reason=pm.get("reason", ""),
            ))

    return Config(
        traktor_nml=traktor_nml,
        search_roots=search_roots,
        path_mappings=path_mappings,
    )


def load_config(config_path: Path = None) -> Config:
    if config_path is None:
        config_path = CONFIG_FILE

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return dict_to_config(data)


def _toml_escape(s: str) -> str:
    if any(c in s for c in '"\\\n\r'):
        s = s.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{s}"'


def save_config(cfg: Config, config_path: Path = None) -> None:
    if config_path is None:
        config_path = CONFIG_FILE

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines = ["[paths]", f"traktor_nml = {_toml_escape(cfg.traktor_nml)}"]

    for sr in cfg.search_roots:
        lines.append("")
        lines.append("[[paths.search_roots]]")
        lines.append(f"path = {_toml_escape(sr.path)}")
        lines.append(f"max_depth = {sr.max_depth}")

    for pm in cfg.path_mappings:
        lines.append("")
        lines.append("[[paths.mappings]]")
        lines.append(f"from_prefix = {_toml_escape(pm.from_prefix)}")
        lines.append(f"to_prefix = {_toml_escape(pm.to_prefix)}")
        lines.append(f"reason = {_toml_escape(pm.reason)}")

    with open(config_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def init_default_config(config_path: Path = None) -> Config:
    cfg = get_default_config()
    save_config(cfg, config_path)
    return cfg


def validate_config(cfg: Config) -> list[str]:
    errors = []

    if not cfg.traktor_nml:
        errors.append("traktor_nml is not set")
    elif not Path(cfg.traktor_nml).exists():
        errors.append(f"traktor_nml file does not exist: {cfg.traktor_nml}")

    for i, sr in enumerate(cfg.search_roots):
        if not sr.path:
            errors.append(f"search_roots[{i}].path is not set")
        elif not Path(sr.path).exists():
            errors.append(f"search_roots[{i}].path does not exist: {sr.path}")

    for i, pm in enumerate(cfg.path_mappings):
        if not pm.from_prefix:
            errors.append(f"path_mappings[{i}].from_prefix is not set")

    return errors


def format_config(cfg: Config) -> str:
    lines = ["[paths]", f"traktor_nml = {_toml_escape(cfg.traktor_nml)}"]

    for sr in cfg.search_roots:
        lines.append("")
        lines.append("[[paths.search_roots]]")
        lines.append(f"path = {_toml_escape(sr.path)}")
        lines.append(f"max_depth = {sr.max_depth}")

    for pm in cfg.path_mappings:
        lines.append("")
        lines.append("[[paths.mappings]]")
        lines.append(f"from_prefix = {_toml_escape(pm.from_prefix)}")
        lines.append(f"to_prefix = {_toml_escape(pm.to_prefix)}")
        lines.append(f"reason = {_toml_escape(pm.reason)}")

    return "\n".join(lines).strip()