import React, { useState } from 'react';
import { DemoNoticeBanner, ModalDialog } from './StateComponents';

export default function RakshaOverview({ overviewData, onNavigate }) {
  const [selectedIncident, setSelectedIncident] = useState(null);

  const stats = overviewData?.stats || {
    defcon_level: 2,
    threat_description: 'DEFCON 2 — High Severity Multi-Hazard Escalation',
    active_incidents_count: 5,
    critical_incidents_count: 1,
    deployed_teams_count: 3,
    active_alerts_count: 3,
    shelters_open_count: 4,
    total_sheltered_population: 6940,
    total_shelter_capacity: 8800,
    overall_shelter_occupancy_pct: 78.8,
    resource_readiness_pct: 87.4,
    database_status: 'prepared',
    demo_mode_active: true,
  };

  const incidents = overviewData?.active_incidents || [];
  const alerts = overviewData?.high_priority_alerts || [];
  const activity = overviewData?.recent_activity || [];

  return (
    <>
      <DemoNoticeBanner text={overviewData?.disclaimer} />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Mission Control Overview</h2>
          <p>{stats.threat_description}</p>
        </div>
        <div className="rg-page-controls">
          <button
            className="rg-btn rg-btn-primary"
            onClick={() => onNavigate && onNavigate('incidents')}
          >
            + Report Incident
          </button>
          <button
            className="rg-btn rg-btn-outline"
            onClick={() => onNavigate && onNavigate('alerts')}
          >
            Broadcast Console →
          </button>
          <button
            className="rg-btn rg-btn-outline"
            onClick={() => onNavigate && onNavigate('risk-analysis')}
          >
            Intelligence & Agent →
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="rg-kpi-grid">
        <div className="rg-kpi-card alert">
          <div className="rg-kpi-header">
            <span>Active Incidents</span>
            <span className="rg-pill rg-pill-critical">{stats.critical_incidents_count} Critical</span>
          </div>
          <div className="rg-kpi-value">{stats.active_incidents_count}</div>
          <div className="rg-kpi-subtext">Across 4 disaster zones</div>
        </div>

        <div className="rg-kpi-card warning">
          <div className="rg-kpi-header">
            <span>Active Broadcasts</span>
            <span className="rg-pill rg-pill-severe">CAP Alerts</span>
          </div>
          <div className="rg-kpi-value">{stats.active_alerts_count}</div>
          <div className="rg-kpi-subtext">2 Red Warnings • 1 Traffic Advisory</div>
        </div>

        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">
            <span>Deployed Units</span>
            <span className="rg-pill rg-pill-moderate">NDRF / SDRF</span>
          </div>
          <div className="rg-kpi-value">{stats.deployed_teams_count}</div>
          <div className="rg-kpi-subtext">95 First Responders Deployed</div>
        </div>

        <div className="rg-kpi-card">
          <div className="rg-kpi-header">
            <span>Shelter Occupancy</span>
            <span>{stats.overall_shelter_occupancy_pct}%</span>
          </div>
          <div className="rg-kpi-value">
            {stats.total_sheltered_population?.toLocaleString()}
          </div>
          <div className="rg-kpi-subtext">Capacity: {stats.total_shelter_capacity?.toLocaleString()}</div>
        </div>

        <div className="rg-kpi-card">
          <div className="rg-kpi-header">
            <span>Resource Readiness</span>
            <span className="rg-pill rg-pill-moderate">Stockpile</span>
          </div>
          <div className="rg-kpi-value">{stats.resource_readiness_pct}%</div>
          <div className="rg-kpi-subtext">Medical, Rafts, Generators</div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="rg-two-col">
        {/* Left Column: Incidents Table */}
        <div className="rg-panel">
          <div className="rg-panel-header">
            <h3>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Active Disaster Incidents
            </h3>
            <button className="rg-btn rg-btn-outline rg-btn-sm" onClick={() => onNavigate('incidents')}>
              View All Incidents →
            </button>
          </div>
          <div className="rg-panel-body" style={{ padding: 0 }}>
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Incident</th>
                    <th>Type</th>
                    <th>Severity</th>
                    <th>Affected Pop.</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '36px', color: 'var(--rg-text-muted)' }}>
                        <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--rg-text-primary)', marginBottom: '6px' }}>
                          No Active Disaster Incidents
                        </div>
                        <div style={{ fontSize: '12px', marginBottom: '14px' }}>
                          All monitored emergency sectors are currently nominal with zero uncontained hazards.
                        </div>
                        <button
                          className="rg-btn rg-btn-primary rg-btn-sm"
                          onClick={() => onNavigate && onNavigate('incidents')}
                        >
                          + Report Incident
                        </button>
                      </td>
                    </tr>
                  ) : (
                    incidents.map((inc) => (
                      <tr key={inc.id}>
                        <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>{inc.incident_code}</td>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{inc.title}</div>
                          <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>{inc.location_name}</div>
                        </td>
                        <td>
                          <span style={{ textTransform: 'uppercase', fontSize: '10px', fontFamily: 'var(--rg-font-mono)' }}>
                            {inc.disaster_type}
                          </span>
                        </td>
                        <td>
                          <span className={`rg-pill rg-pill-${inc.severity}`}>
                            {inc.severity}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--rg-font-mono)' }}>
                          {inc.affected_population_estimate?.toLocaleString() || 'N/A'}
                        </td>
                        <td>
                          <span className="rg-pill rg-pill-active">{inc.status}</span>
                        </td>
                        <td>
                          <button
                            className="rg-btn rg-btn-outline rg-btn-sm"
                            onClick={() => setSelectedIncident(inc)}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Alerts & Telemetry */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Active Alerts Panel */}
          <div className="rg-panel">
            <div className="rg-panel-header">
              <h3>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                Emergency Broadcasts
              </h3>
              <button className="rg-btn rg-btn-outline rg-btn-sm" onClick={() => onNavigate('alerts')}>
                Broadcast Console →
              </button>
            </div>
            <div className="rg-panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {alerts.length === 0 ? (
                <div style={{ padding: '24px', textAlign: 'center', color: 'var(--rg-text-muted)', fontSize: '12px' }}>
                  No active emergency broadcasts at this time.
                </div>
              ) : (
                alerts.map((alt) => (
                  <div
                    key={alt.id}
                    style={{
                      backgroundColor: 'var(--rg-bg-card)',
                      borderLeft: alt.severity === 'extreme' ? '3px solid var(--rg-red-base)' : '3px solid var(--rg-amber-base)',
                      borderRadius: 'var(--rg-radius-sm)',
                      padding: '12px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span className={`rg-pill rg-pill-${alt.severity === 'extreme' ? 'critical' : 'severe'}`}>
                        {alt.severity}
                      </span>
                      <span style={{ fontSize: '10px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                        {alt.alert_code}
                      </span>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--rg-text-primary)', marginBottom: '4px' }}>
                      {alt.headline}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--rg-text-secondary)', marginBottom: '6px' }}>
                      Target: {alt.target_region}
                    </div>
                    {alt.evacuation_recommended && (
                      <div style={{ fontSize: '11px', color: 'var(--rg-red-light)', fontWeight: 600 }}>
                        ⚠️ Immediate Evacuation Recommended
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>


          {/* Rapid Field Telemetry Stream */}
          <div className="rg-panel">
            <div className="rg-panel-header">
              <h3>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Operational Activity Stream
              </h3>
            </div>
            <div className="rg-panel-body">
              <div className="rg-activity-list">
                {activity.map((act, idx) => (
                  <div key={idx} className="rg-activity-item">
                    <div className="rg-activity-time">
                      {new Date(act.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div className="rg-activity-content">
                      <span className="rg-activity-actor">{act.actor}</span>
                      <span style={{ color: 'var(--rg-text-secondary)' }}>{act.description}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Incident Details Modal */}
      <ModalDialog
        isOpen={Boolean(selectedIncident)}
        onClose={() => setSelectedIncident(null)}
        title={selectedIncident ? `${selectedIncident.incident_code} — ${selectedIncident.title}` : ''}
      >
        {selectedIncident && (
          <div>
            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              <span className={`rg-pill rg-pill-${selectedIncident.severity}`}>{selectedIncident.severity}</span>
              <span className="rg-pill rg-pill-active">{selectedIncident.status}</span>
              <span className="rg-pill rg-pill-minor">{selectedIncident.disaster_type}</span>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase' }}>Location & Coordinates</div>
              <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{selectedIncident.location_name}</div>
              <div style={{ fontSize: '12px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-secondary)' }}>
                LAT: {selectedIncident.latitude}° N | LON: {selectedIncident.longitude}° E
              </div>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase' }}>Situation Summary</div>
              <p style={{ color: 'var(--rg-text-secondary)', margin: '4px 0' }}>{selectedIncident.description}</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: 'var(--rg-radius-sm)' }}>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>AFFECTED POPULATION</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--rg-text-primary)' }}>
                  {selectedIncident.affected_population_estimate?.toLocaleString()}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>CASUALTY ESTIMATE</div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: selectedIncident.casualty_count_estimate > 0 ? 'var(--rg-red-light)' : 'var(--rg-text-primary)' }}>
                  {selectedIncident.casualty_count_estimate}
                </div>
              </div>
            </div>
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                className="rg-btn rg-btn-secondary rg-btn-sm"
                onClick={() => setSelectedIncident(null)}
              >
                Close
              </button>
              <button
                className="rg-btn rg-btn-outline rg-btn-sm"
                onClick={() => {
                  setSelectedIncident(null);
                  if (onNavigate) onNavigate('live-map');
                }}
              >
                🗺️ View on GIS Map
              </button>
              <button
                className="rg-btn rg-btn-primary rg-btn-sm"
                onClick={() => {
                  setSelectedIncident(null);
                  if (onNavigate) onNavigate('risk-analysis');
                }}
              >
                📊 Assess Risk & AI Response
              </button>
            </div>
          </div>
        )}
      </ModalDialog>
    </>
  );
}

