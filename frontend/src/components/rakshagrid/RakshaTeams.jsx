import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, LoadingState, ModalDialog } from './StateComponents';

export default function RakshaTeams() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dispatchModal, setDispatchModal] = useState(null);

  const fetchTeams = useCallback(async () => {
    try {
      const res = await fetch('/api/rakshagrid/teams');
      if (res.ok) {
        const data = await res.json();
        setTeams(data);
      }
    } catch (e) {
      console.error('Failed to fetch response teams:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    fetchTeams().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [fetchTeams]);

  return (
    <>
      <DemoNoticeBanner text="Emergency Response Units Roster (NDRF, SDRF, Medical Triage, Drone Recon). Demonstration units active." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Emergency Response Units</h2>
          <p>Personnel mobilization, communications channels, and tactical field staging</p>
        </div>
      </div>

      <div className="rg-kpi-grid" style={{ marginBottom: '20px' }}>
        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">Total Responders</div>
          <div className="rg-kpi-value">117</div>
          <div className="rg-kpi-subtext">Across 5 specialized units</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Active in Field</div>
          <div className="rg-kpi-value">3 Units</div>
          <div className="rg-kpi-subtext">Guwahati, Puri, Rudraprayag</div>
        </div>
        <div className="rg-kpi-card warning">
          <div className="rg-kpi-header">En Route</div>
          <div className="rg-kpi-value">1 Unit</div>
          <div className="rg-kpi-subtext">Aerial Drone Recon #7</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Standby Reserve</div>
          <div className="rg-kpi-value">1 Unit</div>
          <div className="rg-kpi-subtext">HAZMAT Containment</div>
        </div>
      </div>

      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Unit Roster & Telemetry</h3>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Querying team telemetry..." />
          ) : (
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Callsign</th>
                    <th>Type</th>
                    <th>Personnel</th>
                    <th>Commander</th>
                    <th>Comms Channel</th>
                    <th>Current Base / Staging</th>
                    <th>Status</th>
                    <th>Dispatch</th>
                  </tr>
                </thead>
                <tbody>
                  {teams.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700, color: 'var(--rg-text-primary)' }}>
                        {t.team_callsign}
                      </td>
                      <td>
                        <span style={{ textTransform: 'uppercase', fontSize: '10px', fontFamily: 'var(--rg-font-mono)' }}>
                          {t.unit_type}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{t.personnel_count} Officers</td>
                      <td style={{ fontWeight: 500 }}>{t.commander_name}</td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                        {t.contact_channel}
                      </td>
                      <td style={{ fontSize: '12px' }}>{t.base_location}</td>
                      <td>
                        <span className={`rg-pill ${t.current_status === 'deployed' ? 'rg-pill-moderate' : t.current_status === 'en_route' ? 'rg-pill-severe' : 'rg-pill-minor'}`}>
                          {t.current_status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="rg-btn rg-btn-outline rg-btn-sm"
                          onClick={() => setDispatchModal(t)}
                        >
                          Mobilize
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

      <ModalDialog
        isOpen={Boolean(dispatchModal)}
        onClose={() => setDispatchModal(null)}
        title={dispatchModal ? `Mobilize: ${dispatchModal.team_callsign}` : ''}
      >
        <div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            <strong>Commander:</strong> {dispatchModal?.commander_name}<br />
            <strong>Comms:</strong> {dispatchModal?.contact_channel}<br />
            <strong>Personnel Count:</strong> {dispatchModal?.personnel_count} Responders
          </p>
          <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '10px', borderRadius: '4px', fontSize: '12px', marginTop: '12px' }}>
            <span className="rg-pulse-dot warning" /> <strong>Phase 1 Scope:</strong> Dynamic field mobilization and GPS tracking are verified in the database schema (<code>response_teams</code> table). Real-time task dispatch workflows activate in Phase 2.
          </div>
        </div>
      </ModalDialog>
    </>
  );
}
