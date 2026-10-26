-- ==============================================================================
-- RakshaGrid Disaster Intelligence & Response — Schema Migration v0001
-- PostgreSQL DDL Script (UUID Extension, Constraints, Foreign Keys, Indexes)
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    disaster_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    affected_region VARCHAR(255) NOT NULL,
    affected_population_estimate INTEGER DEFAULT 0,
    casualty_count_estimate INTEGER DEFAULT 0,
    description TEXT,
    reported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_incident_severity CHECK (severity IN ('low', 'medium', 'high', 'critical', 'severe', 'moderate', 'minor')),
    CONSTRAINT ck_incident_status CHECK (status IN ('reported', 'under_assessment', 'confirmed', 'response_active', 'contained', 'resolved', 'closed', 'active', 'assessing'))
);

CREATE INDEX IF NOT EXISTS ix_incidents_incident_code ON incidents (incident_code);
CREATE INDEX IF NOT EXISTS ix_incidents_disaster_type ON incidents (disaster_type);
CREATE INDEX IF NOT EXISTS ix_incidents_severity ON incidents (severity);
CREATE INDEX IF NOT EXISTS ix_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS ix_incidents_lat_lon ON incidents (latitude, longitude);
CREATE INDEX IF NOT EXISTS ix_incidents_type_status ON incidents (disaster_type, status);

-- 2. Shelters
CREATE TABLE IF NOT EXISTS shelters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    shelter_type VARCHAR(50) NOT NULL,
    capacity INTEGER NOT NULL,
    current_occupancy INTEGER NOT NULL DEFAULT 0,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    address TEXT NOT NULL,
    contact_person VARCHAR(100) NOT NULL,
    contact_phone VARCHAR(50) NOT NULL,
    supplies_status VARCHAR(30) NOT NULL DEFAULT 'adequate',
    power_backup BOOLEAN NOT NULL DEFAULT TRUE,
    medical_station BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_shelters_name ON shelters (name);
CREATE INDEX IF NOT EXISTS ix_shelters_status ON shelters (status);

-- 3. Incident Updates
CREATE TABLE IF NOT EXISTS incident_updates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    author_name VARCHAR(100) DEFAULT 'system',
    author_role VARCHAR(100) DEFAULT 'operator',
    update_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_incident_updates_incident_id ON incident_updates (incident_id);
CREATE INDEX IF NOT EXISTS ix_incident_updates_created_at ON incident_updates (created_at);

-- 4. Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    alert_code VARCHAR(50) UNIQUE NOT NULL,
    headline VARCHAR(255) NOT NULL,
    urgency VARCHAR(20) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    certainty VARCHAR(20) NOT NULL,
    target_region VARCHAR(255) NOT NULL,
    evacuation_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    instructions TEXT NOT NULL,
    broadcast_status VARCHAR(20) NOT NULL DEFAULT 'active',
    issued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_alert_status CHECK (broadcast_status IN ('active', 'expired', 'cancelled', 'draft'))
);

CREATE INDEX IF NOT EXISTS ix_alerts_alert_code ON alerts (alert_code);
CREATE INDEX IF NOT EXISTS ix_alerts_incident_id ON alerts (incident_id);
CREATE INDEX IF NOT EXISTS ix_alerts_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS ix_alerts_status ON alerts (broadcast_status);

-- 5. Response Teams
CREATE TABLE IF NOT EXISTS response_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_callsign VARCHAR(100) UNIQUE NOT NULL,
    unit_type VARCHAR(50) NOT NULL,
    personnel_count INTEGER NOT NULL DEFAULT 1,
    commander_name VARCHAR(100) NOT NULL,
    contact_channel VARCHAR(100) NOT NULL,
    current_status VARCHAR(30) NOT NULL DEFAULT 'standby',
    current_latitude DOUBLE PRECISION,
    current_longitude DOUBLE PRECISION,
    base_location VARCHAR(255) NOT NULL,
    assigned_base_shelter_id UUID REFERENCES shelters(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_response_teams_callsign ON response_teams (team_callsign);
CREATE INDEX IF NOT EXISTS ix_response_teams_unit_type ON response_teams (unit_type);
CREATE INDEX IF NOT EXISTS ix_response_teams_status ON response_teams (current_status);

-- 6. Response Tasks
CREATE TABLE IF NOT EXISTS response_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    assigned_team_id UUID REFERENCES response_teams(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'high',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    target_latitude DOUBLE PRECISION,
    target_longitude DOUBLE PRECISION,
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_response_tasks_incident_id ON response_tasks (incident_id);
CREATE INDEX IF NOT EXISTS ix_response_tasks_assigned_team_id ON response_tasks (assigned_team_id);
CREATE INDEX IF NOT EXISTS ix_response_tasks_priority ON response_tasks (priority);
CREATE INDEX IF NOT EXISTS ix_response_tasks_status ON response_tasks (status);

-- 7. Resources
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity_total DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    quantity_available DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    unit VARCHAR(50) NOT NULL,
    shelter_id UUID REFERENCES shelters(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_resources_code ON resources (resource_code);
CREATE INDEX IF NOT EXISTS ix_resources_category ON resources (category);
CREATE INDEX IF NOT EXISTS ix_resources_shelter_id ON resources (shelter_id);

-- 8. Resource Movements
CREATE TABLE IF NOT EXISTS resource_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE RESTRICT,
    source_location VARCHAR(255) NOT NULL,
    destination_location VARCHAR(255) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'dispatched',
    transport_mode VARCHAR(50) NOT NULL,
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_resource_movements_resource_id ON resource_movements (resource_id);
CREATE INDEX IF NOT EXISTS ix_resource_movements_status ON resource_movements (status);

-- 9. Environmental Observations
CREATE TABLE IF NOT EXISTS environmental_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    station_id VARCHAR(100) NOT NULL,
    station_name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    unit VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'nominal',
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_env_obs_station_id ON environmental_observations (station_id);
CREATE INDEX IF NOT EXISTS ix_env_obs_metric_type ON environmental_observations (metric_type);
CREATE INDEX IF NOT EXISTS ix_env_obs_status ON environmental_observations (status);
CREATE INDEX IF NOT EXISTS ix_env_obs_recorded_at ON environmental_observations (recorded_at);

-- 10. Risk Assessments
CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES incidents(id) ON DELETE SET NULL,
    target_area VARCHAR(255) NOT NULL,
    hazard_type VARCHAR(50) NOT NULL,
    calculated_risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    simulated_factors TEXT,
    recommended_interventions TEXT NOT NULL,
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_risk_assessments_incident_id ON risk_assessments (incident_id);
CREATE INDEX IF NOT EXISTS ix_risk_assessments_risk_level ON risk_assessments (risk_level);

-- 11. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id VARCHAR(100) NOT NULL,
    actor_role VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_id ON audit_logs (actor_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs (created_at);
