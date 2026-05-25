"""
Configuration loader for MobileAutoQA.

Resolution order (highest priority wins):
    1. Environment variables  (MAQA_<PATH>, e.g. MAQA_BROWSERSTACK_ENABLED=false)
    2. secrets.yaml           (gitignored — passwords, webhook, BrowserStack key)
    3. config.yaml            (committed base config)

Usage:
    from core.config_loader import config
    config.get("browserstack.enabled")            -> bool/str
    config.get("credentials.prod.employee_password")
    config.platform                                -> "android" | "ios"
"""

import os
import yaml
from pathlib import Path
from functools import reduce


class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        root = Path(__file__).resolve().parent.parent
        config_path = root / "config" / "config.yaml"
        secrets_path = root / "config" / "secrets.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

        # Deep-merge secrets if present
        if secrets_path.exists():
            with open(secrets_path, "r", encoding="utf-8") as f:
                secrets = yaml.safe_load(f) or {}
            self._deep_merge(self._data, secrets)
            print(f"[Config] Loaded secrets.yaml")
        else:
            print(f"[Config] WARN: secrets.yaml not found — copy secrets.example.yaml and fill it in")

        self.root = root

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(base.get(k), dict):
                ConfigLoader._deep_merge(base[k], v)
            else:
                base[k] = v

    def get(self, dotted_key: str, default=None):
        """
        Get a value by dotted path, e.g. "browserstack.android.device".
        Environment variable MAQA_BROWSERSTACK_ANDROID_DEVICE overrides if set.
        """
        # Env var override
        env_key = "MAQA_" + dotted_key.upper().replace(".", "_")
        if env_key in os.environ:
            return self._coerce(os.environ[env_key])

        try:
            val = reduce(lambda d, k: d[k], dotted_key.split("."), self._data)
            return val if val is not None else default
        except (KeyError, TypeError):
            return default

    @staticmethod
    def _coerce(s: str):
        """Coerce env-var strings to bool/int where obvious."""
        low = s.strip().lower()
        if low in ("true", "false"):
            return low == "true"
        if low.isdigit():
            return int(s)
        return s

    # ─── Convenience accessors ────────────────────────────────────────────────

    @property
    def platform(self) -> str:
        return str(self.get("platform", "android")).lower()

    @property
    def run_mode(self) -> str:
        return str(self.get("run_mode", "browserstack")).lower()

    @property
    def environment(self) -> str:
        return str(self.get("environment", "prod")).lower()

    @property
    def browserstack_enabled(self) -> bool:
        if self.run_mode == "local":
            return False
        return bool(self.get("browserstack.enabled", True))

    def credential(self, key: str):
        """Get a credential for the current environment, e.g. credential('employee_password')."""
        return self.get(f"credentials.{self.environment}.{key}")

    def timeout(self, key: str = "default") -> int:
        return int(self.get(f"timeouts.{key}", 30))


# Module-level singleton
config = ConfigLoader()
