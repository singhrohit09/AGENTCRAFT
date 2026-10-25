import React from 'react';
import { DemoNoticeBanner } from './StateComponents';

export default function RakshaAnalytics() {
  return (
    <>
      <DemoNoticeBanner text="Operational Analytics & Response Telemetry Reporting. Demonstration metrics active." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Disaster Analytics & Post-Incident Audit</h2>
          <p>Mobilization latency benchmarks, casualty mitigation rates, and audit logs</p>
        </div>
      </div>

      <div className="rg-kpi-grid">
        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">Average Triage Time</div>
          <div className="rg-kpi-value">18.4 min</div>
          <div className="rg-kpi-subtext">-4.2m vs national benchmark</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Evacuation Completion</div>
          <div className="rg-kpi-value">91.2%</div>
          <div className="rg-kpi-subtext">Across Kamrup & Coastal sectors</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Resource Utilization</div>
          <div className="rg-kpi-value">74.8%</div>
          <div className="rg-kpi-subtext">Relief stockpile efficiency</div>
        </div>
        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">Audit Gate Integrity</div>
          <div className="rg-kpi-value">100%</div>
          <div className="rg-kpi-subtext">0 unverified dispatch overrides</div>
        </div>
      </div>

      <div className="rg-two-col" style={{ marginTop: '20px' }}>
        <div className="rg-panel">
          <div className="rg-panel-header">
            <h3>Disaster Incidents by Hazard Classification</h3>
          </div>
          <div className="rg-panel-body">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {[
                { name: 'Floods & Inundation', count: 18, pct: 40, color: 'var(--rg-blue-subtle)' },
                { name: 'Cyclones & Storm Surges', count: 12, pct: 27, color: 'var(--rg-amber-light)' },
                { name: 'Landslides & Debris Flow', count: 8, pct: 18, color: 'var(--rg-red-light)' },
                { name: 'Earthquakes & Tremors', count: 4, pct: 9, color: 'var(--rg-olive-light)' },
                { name: 'Wildfires', count: 3, pct: 6, color: '#f97316' },
              ].map((item, idx) => (
                <div key={idx}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600 }}>{item.name}</span>
                    <span style={{ fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                      {item.count} incidents ({item.pct}%)
                    </span>
                  </div>
                  <div style={{ height: '8px', backgroundColor: 'var(--rg-bg-inset)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${item.pct}%`, height: '100%', backgroundColor: item.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rg-panel">
          <div className="rg-panel-header">
            <h3>Immutable Audit Trail (audit_logs)</h3>
          </div>
          <div className="rg-panel-body">
            <div className="rg-activity-list">
              {[
                { time: '18:42 UTC', actor: 'NDRF Command', action: 'DISPATCH_TEAM', desc: 'Mobilized NDRF-BRAVO-12 to Sector 4' },
                { time: '18:14 UTC', actor: 'State EOC', action: 'ISSUE_ALERT', desc: 'Escalated ALT-2026-0091 to Extreme' },
                { time: '17:50 UTC', actor: 'Medical Director', action: 'REALLOCATE_STOCK', desc: 'Transferred 50 trauma kits to Relief Center #1' },
                { time: '17:15 UTC', actor: 'System Sensor', action: 'WATER_LEVEL_ALERT', desc: 'Station Kamrup-4 water surge threshold breached' },
              ].map((log, idx) => (
                <div key={idx} className="rg-activity-item">
                  <div className="rg-activity-time">{log.time}</div>
                  <div className="rg-activity-content">
                    <span className="rg-activity-actor">{log.actor}</span>
                    <span className="rg-pill rg-pill-minor" style={{ fontSize: '9px', marginRight: '6px' }}>{log.action}</span>
                    <div style={{ color: 'var(--rg-text-secondary)', fontSize: '11px', marginTop: '2px' }}>{log.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
