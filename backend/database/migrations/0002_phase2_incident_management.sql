-- ==============================================================================
-- RakshaGrid Phase 2: Database-Backed Incident Management Migration v0002
-- PostgreSQL DDL Script for Incidents and Incident Updates enhancements
-- ==============================================================================

-- 1. Upgrade incidents table
ALTER TABLE incidents
ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'other',
ADD COLUMN IF NOT EXISTS location_description VARCHAR(255),
ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'operator_report',
ADD COLUMN IF NOT EXISTS verification_status VARCHAR(30) DEFAULT 'unverified',
ADD COLUMN IF NOT EXISTS created_by VARCHAR(100) DEFAULT 'system',
ADD COLUMN IF NOT EXISTS assigned_commander VARCHAR(100),
ADD COLUMN IF NOT EXISTS affected_population INTEGER DEFAULT 0;

CREATE INDEX IF NOT EXISTS ix_incidents_category ON incidents (category);
CREATE INDEX IF NOT EXISTS ix_incidents_source_type ON incidents (source_type);
CREATE INDEX IF NOT EXISTS ix_incidents_verification_status ON incidents (verification_status);

-- 2. Upgrade incident_updates table
ALTER TABLE incident_updates
ADD COLUMN IF NOT EXISTS actor_id VARCHAR(100) DEFAULT 'system',
ADD COLUMN IF NOT EXISTS previous_status VARCHAR(30),
ADD COLUMN IF NOT EXISTS new_status VARCHAR(30),
ADD COLUMN IF NOT EXISTS metadata_payload TEXT;

CREATE INDEX IF NOT EXISTS ix_incident_updates_actor_id ON incident_updates (actor_id);
CREATE INDEX IF NOT EXISTS ix_incident_updates_update_type ON incident_updates (update_type);
