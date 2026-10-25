import React, { useState } from 'react';
import { DemoNoticeBanner, ModalDialog } from './StateComponents';

const RISK_ZONES = [
  { region: 'Brahmaputra Embankment Sector 4', hazard: 'Inundation / Breaching', score: 88.5, level: 'Extreme', vulnerability: 'High (Dense Alluvial Settlements)', recommended: 'Immediate mass evacuation behind reinforced contour bunds' },
  { region: 'Puri Coastal Lowland Belt', hazard: 'Storm Surge & Cat 3 Wind', score: 82.0, level: 'Extreme', vulnerability: 'High (Fisherfolk Communities & Thatched Roofs)', recommended: 'Mandatory relocation into reinforced concrete multi-purpose cyclone shelters' },
  { region: 'NH-58 Debris Ridge Km 44', hazard: 'Debris Flow & Slope Instability', score: 71.4, level: 'High', vulnerability: 'Moderate (Stranded Highway Transit)', recommended: 'Continuous seismic drone acoustic monitoring and geofenced road blockades' },
  { region: 'Kangra Fault Line Sector', hazard: 'Secondary Seismic Aftershocks', score: 48.0, level: 'Moderate', vulnerability: 'Moderate (Aged Masonry Structures)', recommended: 'Structural acoustic inspection of masonry hospitals and bridges' },
  { region: 'Simlipal Canopy Buffer', hazard: 'Dry Biomass Thermal Spread', score: 42.5, level: 'Moderate', vulnerability: 'Low (Wilderness / Buffer)', recommended: 'Create 15-meter bulldozer firebreaks along northern ridge' },
];

export default function RakshaRiskAnalysis() {
  const [simModal, setSimModal] = useState(false);

  return (
    <>
      <DemoNoticeBanner text="Multi-Hazard Vulnerability Matrix & Scenario Modeling. Verified against risk_assessments schema." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Disaster Risk Analysis & Scenario Simulation</h2>
          <p>Compound hazard modeling, population vulnerability indices, and automated intervention strategies</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={() => setSimModal(true)}>
            ⚡ Run Scenario Simulation
          </button>
        </div>
      </div>

      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Multi-Hazard Risk Assessment Matrix</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            CALCULATED RISK SCORES (0 - 100)
          </span>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          <div className="rg-table-wrapper">
            <table className="rg-table">
              <thead>
                <tr>
                  <th>Vulnerability Zone</th>
                  <th>Primary Hazard</th>
                  <th>Risk Score</th>
                  <th>Classification</th>
                  <th>Population Exposure</th>
                  <th>Recommended Interventions</th>
                </tr>
              </thead>
              <tbody>
                {RISK_ZONES.map((z, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{z.region}</td>
                    <td>{z.hazard}</td>
                    <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '13px', fontWeight: 700 }}>
                      {z.score} / 100
                    </td>
                    <td>
                      <span className={`rg-pill ${z.level === 'Extreme' ? 'rg-pill-critical' : z.level === 'High' ? 'rg-pill-severe' : 'rg-pill-moderate'}`}>
                        {z.level}
                      </span>
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--rg-text-secondary)' }}>{z.vulnerability}</td>
                    <td style={{ fontSize: '12px' }}>{z.recommended}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <ModalDialog isOpen={simModal} onClose={() => setSimModal(false)} title="Scenario Simulation Engine">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="rg-pulse-dot warning" />
            <strong style={{ color: 'var(--rg-amber-light)' }}>Phase 1 Foundation Scope</strong>
          </div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            The <code>risk_assessments</code> table schema is established with calculated scores, hazard categories, and simulated factor JSON structures. In Phase 2, Monte Carlo hydro-meteorological scenario engines will compute probabilistic loss models.
          </p>
        </div>
      </ModalDialog>
    </>
  );
}
