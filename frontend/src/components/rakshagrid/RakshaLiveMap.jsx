import React, { useState } from 'react';
import { DemoNoticeBanner, ModalDialog } from './StateComponents';

const SECTORS = [
  { id: 'SEC-NW-01', name: 'Garhwal Himalayas & NH-58', incidents: 1, hazard: 'Landslide', coords: '30.146° N, 78.784° E', status: 'Blocked', color: 'var(--rg-amber-light)' },
  { id: 'SEC-NE-02', name: 'Assam Valley & Brahmaputra Basin', incidents: 1, hazard: 'Flash Flood', coords: '26.185° N, 91.748° E', status: 'Breach Active', color: 'var(--rg-red-light)' },
  { id: 'SEC-CE-03', name: 'Odisha Coastal Belt & Puri', incidents: 1, hazard: 'Category 3 Cyclone', coords: '19.813° N, 85.831° E', status: 'Landfall Watch', color: 'var(--rg-amber-light)' },
  { id: 'SEC-NW-04', name: 'Kangra Foothills & Ridge', incidents: 1, hazard: 'Seismic Tremor', coords: '32.219° N, 76.323° E', status: 'Monitoring', color: 'var(--rg-olive-light)' },
  { id: 'SEC-CE-05', name: 'Simlipal Tiger Reserve Buffer', incidents: 1, hazard: 'Wildfire', coords: '21.642° N, 86.345° E', status: 'Contained', color: 'var(--rg-olive-light)' },
];

export default function RakshaLiveMap() {
  const [selectedSector, setSelectedSector] = useState(SECTORS[1]);
  const [gisModal, setGisModal] = useState(false);

  return (
    <>
      <DemoNoticeBanner text="Tactical Geospatial Grid Preview. Real-time satellite imagery, GPS beacon tracking, and Mapbox/Leaflet vector layers are deferred to Phase 2." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Geospatial Incident Operations Map</h2>
          <p>Sector bounding grids, incident pin vectors, and emergency staging perimeters</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-outline" onClick={() => setGisModal(true)}>
            GIS Engine Status
          </button>
        </div>
      </div>

      <div className="rg-two-col">
        {/* Tactical Map Canvas Simulator */}
        <div className="rg-panel">
          <div className="rg-panel-header">
            <h3>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Tactical Coordinate Grid
            </h3>
            <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
              PROJECTION: EPSG:4326 (WGS84)
            </span>
          </div>
          <div
            className="rg-panel-body"
            style={{
              position: 'relative',
              minHeight: '380px',
              backgroundColor: '#0c0f14',
              backgroundImage: 'radial-gradient(circle, #1a222d 1px, transparent 1px)',
              backgroundSize: '24px 24px',
              borderRadius: 'var(--rg-radius-sm)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              padding: '20px',
              overflow: 'hidden',
            }}
          >
            {/* Compass Rose */}
            <div
              style={{
                position: 'absolute',
                top: '16px',
                right: '16px',
                fontFamily: 'var(--rg-font-mono)',
                fontSize: '11px',
                color: 'var(--rg-text-muted)',
                backgroundColor: 'rgba(21, 25, 32, 0.8)',
                padding: '6px 10px',
                borderRadius: '4px',
                border: '1px solid var(--rg-border-subtle)',
              }}
            >
              ▲ N • 28.6139° N, 77.2090° E
            </div>

            {/* Tactical Grid Visual Pins */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginTop: '30px' }}>
              {SECTORS.map((sec) => (
                <div
                  key={sec.id}
                  onClick={() => setSelectedSector(sec)}
                  style={{
                    backgroundColor: selectedSector.id === sec.id ? 'var(--rg-bg-hover)' : 'rgba(27, 32, 41, 0.85)',
                    border: `1px solid ${selectedSector.id === sec.id ? sec.color : 'var(--rg-border-subtle)'}`,
                    borderRadius: 'var(--rg-radius-sm)',
                    padding: '12px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '10px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                      {sec.id}
                    </span>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: sec.color }} />
                  </div>
                  <div style={{ fontWeight: 600, fontSize: '13px', color: 'var(--rg-text-primary)' }}>{sec.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-secondary)', marginTop: '4px' }}>
                    {sec.hazard} • {sec.status}
                  </div>
                  <div style={{ fontSize: '10px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)', marginTop: '4px' }}>
                    {sec.coords}
                  </div>
                </div>
              ))}
            </div>

            {/* Disclaimer at Bottom of Map */}
            <div
              style={{
                marginTop: '20px',
                padding: '8px 12px',
                backgroundColor: 'rgba(15, 18, 22, 0.9)',
                border: '1px solid var(--rg-border-subtle)',
                borderRadius: '4px',
                fontSize: '11px',
                color: 'var(--rg-text-muted)',
                display: 'flex',
                justifyContent: 'space-between',
              }}
            >
              <span>Map Layer: Vector Grid Simulator (Phase 1)</span>
              <span>PostGIS Spatial Extension Prepared</span>
            </div>
          </div>
        </div>

        {/* Selected Sector Inspector Panel */}
        <div className="rg-panel">
          <div className="rg-panel-header">
            <h3>Sector Tactical Telemetry</h3>
          </div>
          <div className="rg-panel-body">
            {selectedSector ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <div style={{ fontSize: '10px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>SECTOR ID</div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--rg-text-primary)' }}>{selectedSector.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--rg-text-secondary)' }}>Code: {selectedSector.id}</div>
                </div>

                <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: 'var(--rg-radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>PRIMARY HAZARD</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: selectedSector.color }}>{selectedSector.hazard}</div>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-secondary)', marginTop: '2px' }}>Operational Status: {selectedSector.status}</div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>GPS COORDINATES</div>
                  <div style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '13px', color: 'var(--rg-text-primary)' }}>{selectedSector.coords}</div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>STAGED RESPONSE UNITS</div>
                  <div style={{ fontSize: '13px', color: 'var(--rg-text-primary)', marginTop: '4px' }}>
                    • NDRF Task Force 12 (Water Rescue)<br />
                    • State Disaster Medical Triage Mobile Unit
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--rg-border-subtle)', paddingTop: '12px', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                  * Coordinates match spatial schema in <code>incidents</code> table (lat/lon float indexes).
                </div>
              </div>
            ) : (
              <div>Select a sector pin on the map.</div>
            )}
          </div>
        </div>
      </div>

      <ModalDialog isOpen={gisModal} onClose={() => setGisModal(false)} title="GIS Engine Architecture">
        <div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            The spatial schema for RakshaGrid is architected with dual float coordinate indexing (<code>latitude</code>, <code>longitude</code>) and PostGIS geometry readiness.
          </p>
          <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '10px', borderRadius: '4px', fontSize: '12px', marginTop: '10px' }}>
            <strong>Phase 2 GIS Integrations:</strong>
            <ul style={{ paddingLeft: '18px', marginTop: '6px' }}>
              <li>Leaflet / Mapbox tile rendering with dark tactical base maps</li>
              <li>Real-time automated incident perimeter polygon rendering</li>
              <li>Live rescue vehicle GPS telemetry updates via WebSocket</li>
              <li>Dynamic shelter evacuation buffer zone calculations</li>
            </ul>
          </div>
        </div>
      </ModalDialog>
    </>
  );
}
