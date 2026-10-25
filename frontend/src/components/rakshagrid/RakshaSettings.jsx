import React, { useState } from 'react';
import { DemoNoticeBanner, ModalDialog } from './StateComponents';

export default function RakshaSettings({ dbStatus, onRefreshDb }) {
  const [testingDb, setTestingDb] = useState(false);
  const [dbResult, setDbResult] = useState(null);
  const [envInfoModal, setEnvInfoModal] = useState(false);

  const handleTestDatabase = async () => {
    setTestingDb(true);
    try {
      const res = await fetch('/api/rakshagrid/database/status');
      if (res.ok) {
        const data = await res.json();
        setDbResult(data);
      }
    } catch (e) {
      setDbResult({ status: 'error', detail: `Handshake failed: ${e.message}` });
    } finally {
      setTestingDb(false);
      if (onRefreshDb) onRefreshDb();
    }
  };

  const statusObj = dbResult || dbStatus;

  return (
    <>
      <DemoNoticeBanner text="RakshaGrid Platform Infrastructure & Database Settings Console." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>System Infrastructure & Configuration</h2>
          <p>PostgreSQL connection verification, Alembic migrations, and environment variable audits</p>
        </div>
      </div>

      <div className="rg-two-col">
        {/* Left Column: Database Status & Test */}
        <div className="rg-panel">
          <div className="rg-panel-header">
            <h3>PostgreSQL Database & Migration Status</h3>
            <span className={`rg-pill ${statusObj?.connection ? 'rg-pill-moderate' : 'rg-pill-severe'}`}>
              {statusObj?.connection ? 'CONNECTED' : 'PREPARED / FALLBACK'}
            </span>
          </div>
          <div className="rg-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', backgroundColor: 'var(--rg-bg-card)', padding: '14px', borderRadius: '4px' }}>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>HOST</div>
                <div style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '13px' }}>{statusObj?.host || 'localhost'}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>PORT</div>
                <div style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '13px' }}>{statusObj?.port || 5432}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>DATABASE</div>
                <div style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '13px' }}>{statusObj?.database || 'rakshagrid'}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>MIGRATION REVISION</div>
                <div style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '13px', color: 'var(--rg-olive-light)' }}>
                  {statusObj?.active_migration_version || '0001_initial'}
                </div>
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                CONNECTIVITY DIAGNOSTIC:
              </div>
              <div
                style={{
                  fontSize: '12px',
                  backgroundColor: 'var(--rg-bg-inset)',
                  border: '1px solid var(--rg-border-subtle)',
                  padding: '10px 12px',
                  borderRadius: '4px',
                  color: statusObj?.connection ? 'var(--rg-olive-light)' : 'var(--rg-amber-light)',
                  lineHeight: 1.5,
                }}
              >
                {statusObj?.detail ||
                  'PostgreSQL connection prepared. 11 declarative models registered in SQLAlchemy schema.'}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                className="rg-btn rg-btn-primary"
                onClick={handleTestDatabase}
                disabled={testingDb}
              >
                {testingDb ? 'Probing Port 5432...' : '🔄 Test PostgreSQL Connectivity'}
              </button>
              <button className="rg-btn rg-btn-outline" onClick={() => setEnvInfoModal(true)}>
                Config Guide
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Registered ORM Entities & API Endpoints */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="rg-panel">
            <div className="rg-panel-header">
              <h3>Registered Relational Entities ({statusObj?.models_registered_count || 11})</h3>
            </div>
            <div className="rg-panel-body" style={{ padding: 0 }}>
              <div style={{ padding: '12px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {[
                  'incidents',
                  'incident_updates',
                  'alerts',
                  'response_teams',
                  'response_tasks',
                  'shelters',
                  'resources',
                  'resource_movements',
                  'environmental_observations',
                  'risk_assessments',
                  'audit_logs',
                ].map((tbl) => (
                  <span
                    key={tbl}
                    style={{
                      backgroundColor: 'var(--rg-bg-card)',
                      border: '1px solid var(--rg-border-subtle)',
                      padding: '4px 8px',
                      borderRadius: '3px',
                      fontFamily: 'var(--rg-font-mono)',
                      fontSize: '11px',
                      color: 'var(--rg-text-primary)',
                    }}
                  >
                    {tbl}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="rg-panel">
            <div className="rg-panel-header">
              <h3>FastAPI Endpoints Reference</h3>
            </div>
            <div className="rg-panel-body" style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div>
                <a href="/docs" target="_blank" rel="noreferrer" style={{ color: 'var(--rg-blue-subtle)', fontWeight: 600 }}>
                  Interactive OpenAPI Swagger Docs (/docs) ↗
                </a>
              </div>
              <div>
                <a href="/redoc" target="_blank" rel="noreferrer" style={{ color: 'var(--rg-blue-subtle)', fontWeight: 600 }}>
                  ReDoc API Specification (/redoc) ↗
                </a>
              </div>
              <div style={{ color: 'var(--rg-text-muted)', fontSize: '11px', marginTop: '6px' }}>
                Endpoints: <code>/api/rakshagrid/health</code>, <code>/api/rakshagrid/overview</code>, <code>/api/rakshagrid/incidents</code>, <code>/api/rakshagrid/alerts</code>, <code>/api/rakshagrid/teams</code>, <code>/api/rakshagrid/shelters</code>, <code>/api/rakshagrid/database/status</code>
              </div>
            </div>
          </div>
        </div>
      </div>

      <ModalDialog isOpen={envInfoModal} onClose={() => setEnvInfoModal(false)} title="PostgreSQL Environment Configuration">
        <div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            To bind RakshaGrid to a local or cloud PostgreSQL instance:
          </p>
          <pre style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px', fontSize: '11px', fontFamily: 'var(--rg-font-mono)', overflowX: 'auto', color: 'var(--rg-text-primary)' }}>
{`# Add to .env (see .env.example)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=rakshagrid
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Or explicit connection string:
DATABASE_URL=postgresql+psycopg://postgres:secret@localhost:5432/rakshagrid`}
          </pre>
          <p style={{ color: 'var(--rg-text-secondary)', fontSize: '12px', marginTop: '8px' }}>
            Run migrations using Alembic:
          </p>
          <pre style={{ backgroundColor: 'var(--rg-bg-card)', padding: '8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'var(--rg-font-mono)' }}>
            alembic upgrade head
          </pre>
        </div>
      </ModalDialog>
    </>
  );
}
