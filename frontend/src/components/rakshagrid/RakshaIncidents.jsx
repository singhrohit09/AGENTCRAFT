import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, EmptyState, LoadingState, ModalDialog } from './StateComponents';

const HAZARD_TYPES = ['all', 'flood', 'cyclone', 'landslide', 'earthquake', 'wildfire'];
const SEVERITIES = ['all', 'critical', 'severe', 'moderate'];

export default function RakshaIncidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHazard, setSelectedHazard] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeModalIncident, setActiveModalIncident] = useState(null);
  const [createNotice, setCreateNotice] = useState(false);

  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedHazard !== 'all') params.append('disaster_type', selectedHazard);
      if (selectedSeverity !== 'all') params.append('severity', selectedSeverity);

      const res = await fetch(`/api/rakshagrid/incidents?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setIncidents(data);
      }
    } catch (e) {
      console.error('Failed to query incidents:', e);
    } finally {
      setLoading(false);
    }
  }, [selectedHazard, selectedSeverity]);

  useEffect(() => {
    let ignore = false;
    fetchIncidents().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [fetchIncidents]);

  const filteredIncidents = incidents.filter((i) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      i.title.toLowerCase().includes(q) ||
      i.incident_code.toLowerCase().includes(q) ||
      i.location_name.toLowerCase().includes(q)
    );
  });

  return (
    <>
      <DemoNoticeBanner text="Disaster Incident Registry: Verified against the 11 relational PostgreSQL schema models. Demonstration records active." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Disaster Incident Registry</h2>
          <p>Real-time intake, severity categorization, and impact radius tracking</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={() => setCreateNotice(true)}>
            + Log Incident
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rg-panel">
        <div className="rg-filter-bar">
          <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase', fontFamily: 'var(--rg-font-mono)' }}>
            Hazard:
          </span>
          {HAZARD_TYPES.map((h) => (
            <button
              key={h}
              className={`rg-filter-chip ${selectedHazard === h ? 'active' : ''}`}
              onClick={() => setSelectedHazard(h)}
            >
              {h.toUpperCase()}
            </button>
          ))}

          <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase', fontFamily: 'var(--rg-font-mono)', marginLeft: '12px' }}>
            Severity:
          </span>
          {SEVERITIES.map((s) => (
            <button
              key={s}
              className={`rg-filter-chip ${selectedSeverity === s ? 'active' : ''}`}
              onClick={() => setSelectedSeverity(s)}
            >
              {s.toUpperCase()}
            </button>
          ))}

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="text"
              placeholder="Search code or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                backgroundColor: 'var(--rg-bg-card)',
                border: '1px solid var(--rg-border-subtle)',
                color: 'var(--rg-text-primary)',
                padding: '4px 8px',
                borderRadius: 'var(--rg-radius-sm)',
                fontSize: '12px',
                width: '180px',
              }}
            />
          </div>
        </div>

        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Querying disaster incident database..." />
          ) : filteredIncidents.length === 0 ? (
            <EmptyState
              title="No Incidents Match Filters"
              description="Adjust the hazard type, severity level, or search parameters above."
            />
          ) : (
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Title & Region</th>
                    <th>Hazard</th>
                    <th>Severity</th>
                    <th>Coordinates</th>
                    <th>Affected Pop.</th>
                    <th>Reported Time</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIncidents.map((i) => (
                    <tr key={i.id}>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>{i.incident_code}</td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{i.title}</div>
                        <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>{i.location_name} • {i.affected_region}</div>
                      </td>
                      <td>
                        <span style={{ textTransform: 'uppercase', fontSize: '10px', fontFamily: 'var(--rg-font-mono)' }}>
                          {i.disaster_type}
                        </span>
                      </td>
                      <td>
                        <span className={`rg-pill rg-pill-${i.severity}`}>{i.severity}</span>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px' }}>
                        {i.latitude.toFixed(3)}°N, {i.longitude.toFixed(3)}°E
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)' }}>
                        {i.affected_population_estimate?.toLocaleString()}
                      </td>
                      <td style={{ fontSize: '11px' }}>
                        {new Date(i.reported_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </td>
                      <td>
                        <button
                          className="rg-btn rg-btn-outline rg-btn-sm"
                          onClick={() => setActiveModalIncident(i)}
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Incident Detail Modal */}
      <ModalDialog
        isOpen={Boolean(activeModalIncident)}
        onClose={() => setActiveModalIncident(null)}
        title={activeModalIncident ? `${activeModalIncident.incident_code} — ${activeModalIncident.title}` : ''}
      >
        {activeModalIncident && (
          <div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '14px' }}>
              <span className={`rg-pill rg-pill-${activeModalIncident.severity}`}>{activeModalIncident.severity}</span>
              <span className="rg-pill rg-pill-active">{activeModalIncident.status}</span>
              <span className="rg-pill rg-pill-minor">{activeModalIncident.disaster_type}</span>
            </div>
            <p style={{ color: 'var(--rg-text-secondary)', marginBottom: '14px' }}>{activeModalIncident.description}</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px' }}>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>LOCATION</div>
                <div style={{ fontWeight: 600 }}>{activeModalIncident.location_name}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>COORDINATES</div>
                <div style={{ fontFamily: 'var(--rg-font-mono)' }}>{activeModalIncident.latitude}° N, {activeModalIncident.longitude}° E</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>CASUALTIES REPORTED</div>
                <div style={{ fontWeight: 700, color: activeModalIncident.casualty_count_estimate > 0 ? 'var(--rg-red-light)' : 'inherit' }}>
                  {activeModalIncident.casualty_count_estimate}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>ESTIMATED IMPACT</div>
                <div style={{ fontWeight: 700 }}>{activeModalIncident.affected_population_estimate?.toLocaleString()} Persons</div>
              </div>
            </div>
          </div>
        )}
      </ModalDialog>

      {/* Log Incident Modal */}
      <ModalDialog
        isOpen={createNotice}
        onClose={() => setCreateNotice(false)}
        title="Incident Ingestion Engine"
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="rg-pulse-dot warning" />
            <strong style={{ color: 'var(--rg-amber-light)' }}>Phase 1 Foundation Scope</strong>
          </div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            The relational schema for <code>incidents</code> and <code>incident_updates</code> has been fully constructed in SQLAlchemy and Alembic. In Phase 2, interactive triage submission forms with GIS reverse geocoding and live database commits will be enabled.
          </p>
        </div>
      </ModalDialog>
    </>
  );
}
