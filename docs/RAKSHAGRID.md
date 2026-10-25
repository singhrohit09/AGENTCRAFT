# RakshaGrid — Disaster Intelligence and Response

**RakshaGrid** is a mission-critical disaster-management, hazard-monitoring, and emergency-response coordination platform built on the **AgentCraft** autonomous AI agent engine.

---

## 1. Project Purpose & Scope

During acute catastrophic events—such as flash floods, cyclonic storm surges, landslides, wildfires, and earthquakes—coordination between emergency operation centers (EOCs), first responders (NDRF, SDRF, Medical Triage), relief shelters, and vulnerable populations is compromised by fragmented communication and delayed situational intelligence.

RakshaGrid provides a unified operational command console to:
- Ingest and classify multi-hazard disaster incidents.
- Track evacuation shelters, available capacity, and critical life-support supplies.
- Dispatch and monitor specialized emergency response teams and tactical tasks.
- Broadcast emergency alerts conforming to the **Common Alerting Protocol (CAP v1.2)** standard.
- Model multi-hazard compound risks and simulate mitigation scenarios.
- Maintain an immutable audit trail of all command decisions and resource transfers.

---

## 2. Architecture & Coexistence with AgentCraft

RakshaGrid is integrated directly into the AgentCraft platform without breaking existing agent capabilities:

```mermaid
flowchart TD
    subgraph Frontend["Mission Control (React 19 + Vite 8)"]
        UI[Platform Mode Switcher]
        RG[RakshaGrid Tactical Operations Console]
        AC[AgentCraft Autonomous Agent Mission Control]
        UI --> RG
        UI --> AC
    end

    subgraph Backend["Unified Backend Service (FastAPI)"]
        RGRoutes["/api/rakshagrid/*"]
        ACRoutes["/api/agent/*"]
        SysRoutes["/api/health & /"]
    end

    subgraph CoreEngine["AgentCraft Core Engine"]
        Agent[Autonomous Agent Loop]
        Tools[Tool Registry & Sandboxed Tools]
        Verifier[Verification Gates]
    end

    subgraph Database["Persistent Storage Layer"]
        PG[(PostgreSQL Database)]
        Alembic[Alembic Migrations / schema_v1.sql]
        PG --> Alembic
    end

    RG --> RGRoutes
    AC --> ACRoutes
    RGRoutes --> Database
    ACRoutes --> CoreEngine
```

---

## 3. Frontend Tactical Operations Console

### Design Principles
- **Emergency Operations Center Aesthetic**: Utilitarian, mission-critical, high contrast, clean typography.
- **Harmonious Tactical Palette**:
  - Dark Charcoal (`#0f1216`, `#151920`, `#1b2029`, `#202732`)
  - Warm Off-White (`#f3f4f6`, `#e5e7eb`)
  - Muted Olive (`#3d5242`, `#527357`, `#7da584`)
  - Restrained Amber (`#d97706`, `#fbbf24`)
  - Tactical Red (`#dc2626`, `#f87171`)
- **Responsive Layouts**: Desktop multi-column grid, tablet split view, and mobile stacked navigation with overlay drawer.
- **Accessible & Transparent**: High contrast ratios; all demo data is explicitly tagged `[FICTIONAL DEMO DATA - PHASE 1 FOUNDATION]` without pretending external APIs or live GPS tracking are connected.

### Main Navigation Structure
1. **Overview**: Threat status indicator (DEFCON level), KPI cards, active incident summary, urgent alerts feed, operational activity stream.
2. **Incidents**: Disaster incident registry with search, hazard-type filters (Flood, Cyclone, Landslide, Earthquake, Wildfire), severity filters, and detailed incident inspection modal.
3. **Live Map**: Tactical geospatial coordinate grid (EPSG:4326), sector status pins, and GIS architecture preview.
4. **Alerts**: CAP v1.2 emergency broadcast queue with severity filters, evacuation warnings, and target zone advisories.
5. **Response Teams**: First responder roster (NDRF, SDRF, Medical Triage, Aerial Drone Recon, HAZMAT), unit readiness, and staging bases.
6. **Tasks**: Priority operational dispatch task board linked to incidents and teams.
7. **Shelters**: Evacuation camps with real-time capacity progress bars, occupancy counts, power backup, and medical station flags.
8. **Resources**: Stockpile inventory tracking (trauma kits, inflatable rescue rafts, mobile water purification, generators, rations).
9. **Risk Analysis**: Multi-hazard risk matrix, calculated vulnerability scores (0–100), and scenario modeling.
10. **Analytics**: Mobilization latency benchmarks, casualty mitigation rates, and immutable action audits.
11. **Settings**: PostgreSQL connection probe, declared ORM model inspector, Alembic migration revisions, and OpenAPI documentation links.

---

## 4. Backend Architecture & API Specifications

Implemented in `backend/routes/rakshagrid_routes.py` and `backend/rakshagrid/service.py`:

| Endpoint | Method | Response Model | Description |
|---|---|---|---|
| `/api/rakshagrid/health` | GET | `RakshaGridHealthResponse` | Subsystem diagnostics (database, incident engine, alert broadcaster, geospatial indexer, uptime) |
| `/api/rakshagrid/database/status` | GET | `DatabaseStatusResponse` | PostgreSQL TCP connection test, migration version, model count |
| `/api/rakshagrid/overview` | GET | `OverviewResponse` | Aggregated tactical metrics, incidents, alerts, and audit stream |
| `/api/rakshagrid/incidents` | GET | `List[IncidentSummary]` | Query incidents with filters: `disaster_type`, `severity`, `status` |
| `/api/rakshagrid/alerts` | GET | `List[AlertSummary]` | Query alerts with filters: `severity`, `active_only` |
| `/api/rakshagrid/teams` | GET | `List[ResponseTeamSummary]` | Query response units with filter: `status` |
| `/api/rakshagrid/shelters` | GET | `List[ShelterSummary]` | Relief shelter capacities and occupancy utilization |
| `/api/rakshagrid/config` | GET | `dict` | Public sanitized configuration parameters (no secrets) |

---

## 5. Database Schema & Migration Foundation

Database models reside in `backend/rakshagrid/models.py`. All 11 required entities are fully specified with UUID primary keys, foreign keys, timestamps, check constraints, and performance indexes:

1. `incidents`: Disaster code, title, hazard type, severity, status, latitude, longitude, affected region, casualties, description.
2. `incident_updates`: Situation reports, author, role, verification flag, timestamp.
3. `alerts`: CAP v1.2 alert code, headline, urgency, severity, certainty, evacuation flag, instructions, broadcast status.
4. `response_teams`: Callsign, unit type, personnel count, commander, contact channel, operational status, base location.
5. `response_tasks`: Incident link, assigned team link, priority, status, due timestamp.
6. `shelters`: Name, facility type, capacity, occupancy, coordinates, address, contact, supplies status, backup power, medical station.
7. `resources`: Resource code, category, total quantity, available quantity, unit, shelter link.
8. `resource_movements`: Movement audit, source, destination, transport mode, delivery status.
9. `environmental_observations`: Sensor station telemetry, metric type, value, alert status.
10. `risk_assessments`: Target area, hazard type, calculated score (0-100), risk level, recommended interventions.
11. `audit_logs`: Immutable action trail, actor role, entity ID, action payload, timestamp.

### Migration Tooling
- **Alembic Configuration**: `alembic.ini` and `backend/database/migrations/`
- **Initial Migration**: `backend/database/migrations/versions/0001_initial_rakshagrid_schema.py`
- **Idempotent SQL DDL**: `backend/database/migrations/0001_initial_rakshagrid_schema.sql`

To apply migrations against a configured PostgreSQL database:
```bash
alembic upgrade head
```

---

## 6. Environment Variables

Configure these settings in `.env` (derived from `.env.example`):

```bash
# RakshaGrid Operational Settings
RAKSHAGRID_ENV=development
RAKSHAGRID_DEMO_MODE=true
RAKSHAGRID_DEFCON_LEVEL=2
RAKSHAGRID_ALERT_THRESHOLD=MODERATE

# PostgreSQL Credentials
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rakshagrid
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
# Or explicit URI override:
# DATABASE_URL=postgresql+psycopg://postgres:secret@localhost:5432/rakshagrid
```

*Note: If PostgreSQL is not running locally, RakshaGrid starts safely in demonstration fallback mode without crashing.*

---

## 7. How to Run Locally

### 1. Backend Service
```bash
.\.venv\Scripts\Activate.ps1
python -m backend.app
# Runs on http://127.0.0.1:8000 (OpenAPI docs at /docs)
```

### 2. Frontend Development Server
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000 (proxies /api to port 8000)
```

### 3. Unified Production Serving
```bash
cd frontend
npm run build
cd ..
python -m backend.app
# Access complete application at http://127.0.0.1:8000
```

---

## 8. Verification Results

All automated verification gates have executed cleanly:

- **Pytest Suite**: 53 passed in 19s:
  - 42 existing AgentCraft agent & backend tests
  - 11 new RakshaGrid API, database status, and model registration tests
- **Frontend Build**: Vite 8 production build transformed 32 modules with 0 errors (`dist/index.html` 0.99 kB, `dist/assets/index-LYiELaNH.js` 307 kB).
- **Linter**: Oxlint executed with 0 errors across all frontend files.

---

## 9. Phase Roadmap

### Completed in Phase 1
- [x] Application shell, responsive sidebar, and tactical navigation for all 11 modules.
- [x] Dark charcoal, warm off-white, muted olive, and restrained amber/red design system.
- [x] Overview dashboard with threat level, KPI cards, incident tables, and alert streams.
- [x] Dedicated view components for Incidents, Live Map, Alerts, Teams, Tasks, Shelters, Resources, Risk Analysis, Analytics, and Settings.
- [x] Structured loading, empty, and error states; clear demonstration data labels.
- [x] Backend RakshaGrid module with `/api/rakshagrid/health`, `/overview`, `/database/status`, and query endpoints.
- [x] 11 SQLAlchemy PostgreSQL models and Alembic version-controlled migration files.
- [x] Pydantic v2 validation and non-blocking database connection testing.
- [x] Full test suite (53 tests passing).

### Deferred to Phase 2
- [ ] Live PostgreSQL database connection and data ingestion persistence.
- [ ] Interactive incident reporting and casualty update forms.
- [ ] Leaflet / Mapbox GIS map integration with dark vector tile rendering and polygon overlays.
- [ ] CAP v1.2 alert dispatch to external SMS/VHF broadcaster gateways.
- [ ] Drag-and-drop task dispatch and team mobilization tracking.
- [ ] Dynamic shelter check-in/check-out barcode intake.
