import React, { useState } from 'react';
import { DemoNoticeBanner, ModalDialog } from './StateComponents';

const DEMO_RESOURCES = [
  { code: 'RES-MED-01', name: 'Emergency Trauma & Surgical Field Kits', category: 'Medical', total: 450, available: 310, unit: 'kits', status: 'Adequate', staging: 'Guwahati Depot' },
  { code: 'RES-WAT-02', name: 'Reverse Osmosis Mobile Water Purification Units', category: 'Food & Water', total: 60, available: 42, unit: 'units', status: 'Adequate', staging: 'Puri Municipal Complex' },
  { code: 'RES-RFT-03', name: 'Inflatable High-Tonnage Flood Rescue Rafts', category: 'Rescue Equipment', total: 120, available: 45, unit: 'craft', status: 'High Utilization', staging: 'Assam Relief Base' },
  { code: 'RES-PWR-04', name: 'Heavy-Duty Diesel Generator Units (45kVA)', category: 'Power & Fuel', total: 35, available: 12, unit: 'generators', status: 'High Utilization', staging: 'Rudraprayag Staging' },
  { code: 'RES-RAT-05', name: 'High-Calorie Ready-to-Eat Disaster Rations', category: 'Food & Water', total: 15000, available: 11400, unit: 'packs', status: 'Adequate', staging: 'Kolkata Depot' },
  { code: 'RES-TNT-06', name: 'All-Weather Modular Family Shelter Tents', category: 'Shelter Gear', total: 800, available: 220, unit: 'units', status: 'Critical Reserve', staging: 'Puri Warehouse' },
];

export default function RakshaResources() {
  const [transferModal, setTransferModal] = useState(false);

  return (
    <>
      <DemoNoticeBanner text="Emergency Stockpile & Relief Supply Logistics. Models verified against resources and resource_movements schema." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Emergency Logistics & Resource Stockpiles</h2>
          <p>Inventory reserves, medical supplies, water purification, rescue gear, and movement audits</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={() => setTransferModal(true)}>
            + Dispatched Transfer
          </button>
        </div>
      </div>

      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Emergency Supplies Stockpile</h3>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          <div className="rg-table-wrapper">
            <table className="rg-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Supply Name</th>
                  <th>Category</th>
                  <th>Total Stock</th>
                  <th>Available</th>
                  <th>Unit</th>
                  <th>Stockpile Staging</th>
                  <th>Readiness Status</th>
                </tr>
              </thead>
              <tbody>
                {DEMO_RESOURCES.map((r) => (
                  <tr key={r.code}>
                    <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>{r.code}</td>
                    <td style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{r.name}</td>
                    <td>
                      <span className="rg-pill rg-pill-minor">{r.category}</span>
                    </td>
                    <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{r.total.toLocaleString()}</td>
                    <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700, color: 'var(--rg-text-primary)' }}>
                      {r.available.toLocaleString()}
                    </td>
                    <td style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>{r.unit}</td>
                    <td>{r.staging}</td>
                    <td>
                      <span className={`rg-pill ${r.status === 'Adequate' ? 'rg-pill-moderate' : r.status === 'High Utilization' ? 'rg-pill-severe' : 'rg-pill-critical'}`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <ModalDialog isOpen={transferModal} onClose={() => setTransferModal(false)} title="Resource Transfer Pipeline">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="rg-pulse-dot warning" />
            <strong style={{ color: 'var(--rg-amber-light)' }}>Phase 1 Foundation Scope</strong>
          </div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            The <code>resources</code> and <code>resource_movements</code> tables feature relational constraints preventing stock depletion beyond available limits. Multi-depot transfer requests, carrier airlifts, and RFID barcode tracking are planned for Phase 2.
          </p>
        </div>
      </ModalDialog>
    </>
  );
}
