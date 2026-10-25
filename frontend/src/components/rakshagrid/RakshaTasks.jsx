import React, { useState } from 'react';
import { DemoNoticeBanner, ModalDialog } from './StateComponents';

const DEMO_TASKS = [
  { id: 'TSK-01', incident: 'RG-2026-FL-001', title: 'Deploy 6 Inflatable Rescue Boats to Sector 4 Low-Lands', priority: 'critical', assignedTo: 'NDRF-BRAVO-12', status: 'in_progress', due: 'In 45 mins' },
  { id: 'TSK-02', incident: 'RG-2026-FL-001', title: 'Establish Emergency Trauma Triage at Assam High Grounds', priority: 'critical', assignedTo: 'MED-TRIAGE-ALPHA', status: 'in_progress', due: 'In 1 hour' },
  { id: 'TSK-03', incident: 'RG-2026-CY-002', title: 'Verify Structural Integrity of Puri Cyclone Shelter Alpha', priority: 'high', assignedTo: 'SDRF-ODISHA-04', status: 'completed', due: 'Completed' },
  { id: 'TSK-04', incident: 'RG-2026-LS-003', title: 'Aerial Drone Survey of Km 44 Debris Ridge', priority: 'high', assignedTo: 'AERO-DRONE-RECON-7', status: 'assigned', due: 'In 2 hours' },
  { id: 'TSK-05', incident: 'RG-2026-WF-005', title: 'Coordinate Aerial Water Drop Perimeter with Forestry Division', priority: 'medium', assignedTo: 'Logistics Division', status: 'pending', due: 'In 4 hours' },
];

export default function RakshaTasks() {
  const [taskModal, setTaskModal] = useState(false);

  return (
    <>
      <DemoNoticeBanner text="Tactical Response Tasks Board. Models verified against PostgreSQL response_tasks schema." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Operational Response Tasks</h2>
          <p>Prioritized mission assignments, team allocations, and execution status</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={() => setTaskModal(true)}>
            + Dispatch Task
          </button>
        </div>
      </div>

      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Task Dispatch Board</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            RELATIONAL DISPATCH ENGINE
          </span>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          <div className="rg-table-wrapper">
            <table className="rg-table">
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>Incident</th>
                  <th>Mission Description</th>
                  <th>Assigned Team</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Due</th>
                </tr>
              </thead>
              <tbody>
                {DEMO_TASKS.map((t) => (
                  <tr key={t.id}>
                    <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>{t.id}</td>
                    <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-blue-subtle)' }}>{t.incident}</td>
                    <td style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{t.title}</td>
                    <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '12px' }}>{t.assignedTo}</td>
                    <td>
                      <span className={`rg-pill rg-pill-${t.priority === 'critical' ? 'critical' : t.priority === 'high' ? 'severe' : 'minor'}`}>
                        {t.priority}
                      </span>
                    </td>
                    <td>
                      <span className="rg-pill rg-pill-active">{t.status}</span>
                    </td>
                    <td style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>{t.due}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <ModalDialog isOpen={taskModal} onClose={() => setTaskModal(false)} title="Dispatch Task Engine">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="rg-pulse-dot warning" />
            <strong style={{ color: 'var(--rg-amber-light)' }}>Phase 1 Foundation Scope</strong>
          </div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            The <code>response_tasks</code> entity is fully modeled with foreign keys linking to both <code>incidents</code> and <code>response_teams</code>. Dynamic creation and drag-and-drop Kanban dispatch are scheduled for Phase 2.
          </p>
        </div>
      </ModalDialog>
    </>
  );
}
