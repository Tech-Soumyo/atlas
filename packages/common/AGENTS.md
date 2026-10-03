# packages/common

## Overview

Shared config, logging, ids, clock, and types for every Atlas Python package and app. This is the only place env and YAML should be read for domain facing settings.

## Key files

| File | Owns |
|---|---|
| `src/atlas_common/config.py` | `Settings`, `get_settings`, YAML loaders, feature flag merge |
| `src/atlas_common/logging.py` | Logging setup used by API and worker |
| `src/atlas_common/telemetry.py` | Light OTEL setup hook |
| `src/atlas_common/ids.py` | Id helpers |
| `README.md` | Short import examples |
| `../../configs/` | YAML files loaded at startup (`ATLAS_CONFIGS_DIR`) |

## Commands

```bash
# From repo root
uv run pytest tests/unit/test_config.py
```

## Conventions

- Apps and packages import `get_settings` / `load_yaml_configs`; they do not parse env themselves.
- Prefer typed `Settings` fields over ad hoc string keys.
- Keep this package free of FastAPI, Next, and RAG pipeline logic.

## Gotchas

- `ATLAS_ENV=test` changes readiness behavior in the API; settings expose helpers such as `is_test` and DSN shaping for psycopg.
- Compose and host runs can disagree on data plane URLs; trust `Settings` after Compose overrides, not a raw `.env` copy in your head.

## Related specs

None yet. Cross cutting config choices belong in M1 specs when they appear.

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
