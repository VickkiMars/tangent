# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Agent Registry & Reuse-First Spawning**:
  - Implemented `personas`, `persona_metrics`, `persona_lineage` tables in `db.py` to store battle-tested agents.
  - New `registry_search.py` module to execute Spawning Decision Tree (REUSE, MUTATE, SPAWN).
  - Post-run feedback loop in `JITCompiler` to track success rates and organically register mutated/spawned agents.
- **Documentation**:
  - `tangent-docs/agent_registry.md` deep dive into the registry architecture.
  - `tangent-docs/backend.md`, `tangent-docs/database.md`, `tangent-docs/frontend.md`, `tangent-docs/optimization.md` for comprehensive system documentation.
  - Added marketing post `agent_registry_launch.md`.
- **"My Apps" Parameterization**: Complete end-to-end framework for saving and running workflows with dynamic variables.
  - New `SaveAppModal` in `TaskBoard.jsx` allowing users to map prompt text to variable keys (e.g. `{{TOPIC}}`).
  - New `RunAppModal` in `Apps.jsx` to collect parameter values before deployment.
  - Backend interpolation engine in `apps.py` that injects user values into manifests before agent compilation.
- **Marketing & Social**:
  - Created a draft thread for X (Twitter) in `marketing/posts/` summarizing the My Apps launch.
  - Reorganized `feat-desc` and `marketing` folders; moved internal marketing assets to an ignored `marketing/` directory.
- **Premium Marketing Assets**:
  - `MarketingMyApps.jsx`: A high-end, 3-step interactive screenshot flow (Library -> Prompt -> Result).
  - Indigo-based eye-friendly design system for marketing screenshots.
- **Documentation**:
  - `TANGENT.md`: In-depth framework architecture description covering JIT orchestration, MetaAgent logic, and FIPA ACL protocols.
- **Database**:
  - Added `parameters` JSONB column to `predefined_workflows` table.

### Changed
- **Frontend Architecture**:
  - Refactored `App.jsx` to support "Naked" routes for pixel-perfect marketing extractions without global layout interference.
  - Replaced `window.prompt` flows with custom React modals for a more premium UX.
- **API**:
  - Updated `AppCreateRequest` and `AppRunRequest` to support parameter metadata and runtime values.
