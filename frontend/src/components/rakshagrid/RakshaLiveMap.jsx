import React, { useState, useEffect, useRef, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { LoadingState } from './StateComponents';

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#d97706',
  medium: '#38bdf8',
  low: '#7da584',
  minor: '#7da584',
  severe: '#d97706',
};

export default function RakshaLiveMap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersLayerRef = useRef(null);

  const [incidents, setIncidents] = useState([]);
  const [shelters, setShelters] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showShelters, setShowShelters] = useState(true);
  const [showTeams, setShowTeams] = useState(true);

  // Selected item inspection
  const [selectedItem, setSelectedItem] = useState(null);
  const [showUnmapped, setShowUnmapped] = useState(false);

  // Fetch real data from persistent backend
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [incRes, shRes, tmRes] = await Promise.all([
        fetch('/api/v1/incidents?page_size=100'),
        fetch('/api/v1/shelters?page_size=100'),
        fetch('/api/v1/teams?page_size=100'),
      ]);

      if (!incRes.ok) throw new Error(`Incidents API error (${incRes.status})`);
      if (!shRes.ok) throw new Error(`Shelters API error (${shRes.status})`);
      if (!tmRes.ok) throw new Error(`Teams API error (${tmRes.status})`);

      const incData = await incRes.json();
      const shData = await shRes.json();
      const tmData = await tmRes.json();

      setIncidents(incData.items || []);
      setShelters(shData.items || []);
      setTeams(tmData.items || []);

      // Auto-select first incident if available
      if (incData.items && incData.items.length > 0 && !selectedItem) {
        setSelectedItem({ type: 'incident', data: incData.items[0] });
      }
    } catch (err) {
      console.error('Failed to load geospatial data:', err);
      setError(err.message || 'Unable to synchronize map data.');
    } finally {
      setLoading(false);
    }
  }, [selectedItem]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Initialize Leaflet Map once
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center on India subcontinent tactical bounding
    const map = L.map(mapContainerRef.current, {
      center: [23.5, 82.5],
      zoom: 5,
      zoomControl: false,
      attributionControl: true,
    });

    // Dark Matter tile layer (CartoDB Dark Matter with OpenStreetMap contributors)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    // Zoom control at top right
    L.control.zoom({ position: 'topright' }).addTo(map);

    // Feature group for auto-clearing and bounds
    const markersLayer = L.featureGroup().addTo(map);
    markersLayerRef.current = markersLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Filter incidents with coordinates vs without
  const mappedIncidents = incidents.filter((inc) => {
    const hasCoords = typeof inc.latitude === 'number' && typeof inc.longitude === 'number' &&
      !isNaN(inc.latitude) && !isNaN(inc.longitude);
    if (!hasCoords) return false;

    if (severityFilter !== 'all' && inc.severity.toLowerCase() !== severityFilter) return false;
    if (categoryFilter !== 'all' && inc.category.toLowerCase() !== categoryFilter) return false;
    if (statusFilter !== 'all' && inc.status.toLowerCase() !== statusFilter) return false;

    return true;
  });

  const unmappedIncidents = incidents.filter((inc) => {
    return inc.latitude === null || inc.longitude === null || isNaN(inc.latitude) || isNaN(inc.longitude);
  });

  // Render markers whenever data or filters change
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer) return;

    markersLayer.clearLayers();
    const bounds = [];

    // 1. Plot Incidents
    mappedIncidents.forEach((inc) => {
      const color = SEVERITY_COLORS[inc.severity.toLowerCase()] || '#38bdf8';
      const isCritical = inc.severity.toLowerCase() === 'critical';

      const icon = L.divIcon({
        className: 'custom-leaflet-icon',
        html: `
          <div style="
            position: relative;
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
          ">
            <span style="
              position: absolute;
              width: 100%;
              height: 100%;
              border-radius: 50%;
              background-color: ${color};
              opacity: 0.35;
              animation: ${isCritical ? 'leafletPulse 1.4s infinite ease-out' : 'none'};
            "></span>
            <span style="
              width: 14px;
              height: 14px;
              border-radius: 50%;
              background-color: ${color};
              border: 2px solid #ffffff;
              box-shadow: 0 0 10px ${color};
            "></span>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([inc.latitude, inc.longitude], { icon });

      const popupHtml = `
        <div style="font-family: var(--rg-font-sans); color: #f3f4f6; padding: 4px 2px;">
          <div style="font-size: 10px; font-family: monospace; color: ${color}; font-weight: bold; text-transform: uppercase;">
            ${inc.severity} • ${inc.category}
          </div>
          <div style="font-size: 13px; font-weight: 700; margin: 4px 0 6px 0; color: #fff;">
            ${inc.title}
          </div>
          <div style="font-size: 11px; color: #9ca3af; margin-bottom: 4px;">
            📍 ${inc.location_description || 'Unspecified Location'}
          </div>
          <div style="font-size: 10px; font-family: monospace; color: #6b7280;">
            COORDS: ${inc.latitude.toFixed(4)}°, ${inc.longitude.toFixed(4)}°
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml, {
        className: 'rg-leaflet-popup',
      });

      marker.on('click', () => {
        setSelectedItem({ type: 'incident', data: inc });
      });

      markersLayer.addLayer(marker);
      bounds.push([inc.latitude, inc.longitude]);
    });

    // 2. Plot Shelters
    if (showShelters) {
      shelters.forEach((sh) => {
        if (typeof sh.latitude !== 'number' || typeof sh.longitude !== 'number') return;

        const shelterColor = sh.status === 'full' ? '#dc2626' : sh.status === 'closed' ? '#6b7280' : '#2dd4bf';
        const icon = L.divIcon({
          className: 'custom-shelter-icon',
          html: `
            <div style="
              width: 24px;
              height: 24px;
              border-radius: 4px;
              background-color: #111419;
              border: 2px solid ${shelterColor};
              display: flex;
              align-items: center;
              justify-content: center;
              box-shadow: 0 0 8px ${shelterColor};
              cursor: pointer;
            ">
              <span style="font-size: 11px;">⛺</span>
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([sh.latitude, sh.longitude], { icon });
        const popupHtml = `
          <div style="font-family: var(--rg-font-sans); color: #f3f4f6; padding: 4px;">
            <div style="font-size: 10px; font-family: monospace; color: ${shelterColor}; font-weight: bold; text-transform: uppercase;">
              RELIEF SHELTER • ${sh.status}
            </div>
            <div style="font-size: 13px; font-weight: 700; margin: 4px 0; color: #fff;">
              ${sh.name}
            </div>
            <div style="font-size: 11px; color: #9ca3af;">
              Occupancy: <strong>${sh.current_occupancy}</strong> / ${sh.capacity} (${sh.occupancy_pct}%)
            </div>
            <div style="font-size: 11px; color: #9ca3af;">
              Remaining Capacity: <strong>${sh.remaining_capacity}</strong> spaces
            </div>
          </div>
        `;

        marker.bindPopup(popupHtml, { className: 'rg-leaflet-popup' });
        marker.on('click', () => {
          setSelectedItem({ type: 'shelter', data: sh });
        });

        markersLayer.addLayer(marker);
        bounds.push([sh.latitude, sh.longitude]);
      });
    }

    // 3. Plot Teams
    if (showTeams) {
      teams.forEach((tm) => {
        if (typeof tm.current_latitude !== 'number' || typeof tm.current_longitude !== 'number') return;

        const teamColor = tm.current_status === 'assigned' ? '#fbbf24' : tm.current_status === 'available' ? '#7da584' : '#6b7280';
        const icon = L.divIcon({
          className: 'custom-team-icon',
          html: `
            <div style="
              width: 22px;
              height: 22px;
              border-radius: 50%;
              background-color: #151920;
              border: 2px solid ${teamColor};
              display: flex;
              align-items: center;
              justify-content: center;
              box-shadow: 0 0 8px ${teamColor};
              cursor: pointer;
            ">
              <span style="font-size: 10px;">🛡️</span>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const marker = L.marker([tm.current_latitude, tm.current_longitude], { icon });
        const popupHtml = `
          <div style="font-family: var(--rg-font-sans); color: #f3f4f6; padding: 4px;">
            <div style="font-size: 10px; font-family: monospace; color: ${teamColor}; font-weight: bold; text-transform: uppercase;">
              UNIT • ${tm.current_status}
            </div>
            <div style="font-size: 13px; font-weight: 700; margin: 4px 0; color: #fff;">
              ${tm.team_callsign}
            </div>
            <div style="font-size: 11px; color: #9ca3af;">
              ${tm.unit_type} (${tm.personnel_count} Personnel)
            </div>
            <div style="font-size: 11px; color: #9ca3af;">
              Commander: ${tm.commander_name}
            </div>
          </div>
        `;

        marker.bindPopup(popupHtml, { className: 'rg-leaflet-popup' });
        marker.on('click', () => {
          setSelectedItem({ type: 'team', data: tm });
        });

        markersLayer.addLayer(marker);
        bounds.push([tm.current_latitude, tm.current_longitude]);
      });
    }

    // Auto-fit to bounds if markers exist
    if (bounds.length > 0) {
      try {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
      } catch (e) {
        console.warn('fitBounds caught non-critical error:', e);
      }
    }
  }, [mappedIncidents, shelters, teams, showShelters, showTeams]);

  const handleCenterOnSelected = (item) => {
    const map = mapInstanceRef.current;
    if (!map || !item) return;

    let lat = null;
    let lon = null;
    if (item.type === 'incident') {
      lat = item.data.latitude;
      lon = item.data.longitude;
    } else if (item.type === 'shelter') {
      lat = item.data.latitude;
      lon = item.data.longitude;
    } else if (item.type === 'team') {
      lat = item.data.current_latitude;
      lon = item.data.current_longitude;
    }

    if (typeof lat === 'number' && typeof lon === 'number') {
      map.flyTo([lat, lon], 11, { duration: 1.2 });
    }
  };

  return (
    <>
      <style>{`
        @keyframes leafletPulse {
          0% { transform: scale(0.9); opacity: 0.8; }
          70% { transform: scale(2.2); opacity: 0; }
          100% { transform: scale(2.2); opacity: 0; }
        }
        .rg-leaflet-popup .leaflet-popup-content-wrapper {
          background-color: #1b2029;
          border: 1px solid #3f4a5c;
          border-radius: 6px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
        }
        .rg-leaflet-popup .leaflet-popup-tip {
          background-color: #1b2029;
          border: 1px solid #3f4a5c;
        }
        .rg-map-filter-badge {
          background-color: var(--rg-bg-card);
          border: 1px solid var(--rg-border-subtle);
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .rg-map-filter-badge select {
          background: transparent;
          border: none;
          color: var(--rg-text-primary);
          font-family: inherit;
          font-size: 12px;
          cursor: pointer;
          outline: none;
        }
        .rg-map-filter-badge select option {
          background-color: var(--rg-bg-panel);
          color: var(--rg-text-primary);
        }
      `}</style>

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Interactive Incident Operations Map</h2>
          <p>Real-time geospatial tracking of disaster incidents, emergency response units, and evacuation shelters</p>
        </div>
        <div className="rg-page-controls" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            className="rg-btn rg-btn-outline"
            onClick={() => {
              if (mapInstanceRef.current) {
                mapInstanceRef.current.flyTo([23.5, 82.5], 5, { duration: 1.0 });
              }
            }}
          >
            Reset View
          </button>
          <button className="rg-btn rg-btn-primary" onClick={fetchData}>
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Filter and Layer Control Bar */}
      <div
        className="rg-panel"
        style={{
          marginBottom: '16px',
          padding: '12px 16px',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
          {/* Severity Filter */}
          <div className="rg-map-filter-badge">
            <span style={{ color: 'var(--rg-text-muted)' }}>Severity:</span>
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="rg-map-filter-badge">
            <span style={{ color: 'var(--rg-text-muted)' }}>Category:</span>
            <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
              <option value="all">All Hazards</option>
              <option value="flood">Flood</option>
              <option value="severe_weather">Cyclone / Weather</option>
              <option value="landslide">Landslide</option>
              <option value="earthquake">Earthquake</option>
              <option value="wildfire">Wildfire</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="rg-map-filter-badge">
            <span style={{ color: 'var(--rg-text-muted)' }}>Status:</span>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">All Statuses</option>
              <option value="response_active">Response Active</option>
              <option value="reported">Reported</option>
              <option value="under_assessment">Under Assessment</option>
              <option value="confirmed">Confirmed</option>
              <option value="contained">Contained</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>

        {/* Layer Toggles */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showShelters}
              onChange={(e) => setShowShelters(e.target.checked)}
            />
            <span style={{ color: 'var(--rg-cyan-subtle)' }}>⛺ Evacuation Shelters ({shelters.length})</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showTeams}
              onChange={(e) => setShowTeams(e.target.checked)}
            />
            <span style={{ color: 'var(--rg-amber-light)' }}>🛡️ Response Units ({teams.length})</span>
          </label>
        </div>
      </div>

      {error && (
        <div className="rg-alert-banner" style={{ backgroundColor: '#751a1a', color: '#f87171', marginBottom: '16px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Main Two Column Map and Inspector Area */}
      <div className="rg-two-col" style={{ gridTemplateColumns: 'minmax(0, 1.8fr) minmax(320px, 1fr)', gap: '16px' }}>
        {/* Leaflet Map Canvas */}
        <div className="rg-panel" style={{ display: 'flex', flexDirection: 'column', height: '640px', overflow: 'hidden' }}>
          <div className="rg-panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ marginRight: '6px' }}>
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Tactical Coordinate Grid
            </h3>
            <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
              MAPPED HAZARDS: {mappedIncidents.length} • PROJECTION: EPSG:4326
            </span>
          </div>

          <div style={{ position: 'relative', flex: 1, minHeight: '400px' }}>
            {loading && (
              <div style={{ position: 'absolute', inset: 0, zIndex: 1000, background: 'rgba(15,18,22,0.85)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <LoadingState message="Synchronizing geospatial coordinates..." />
              </div>
            )}
            <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

            {/* Tactical Map Overlay Legend */}
            <div
              style={{
                position: 'absolute',
                bottom: '16px',
                left: '16px',
                zIndex: 400,
                backgroundColor: 'rgba(21, 25, 32, 0.92)',
                border: '1px solid var(--rg-border-subtle)',
                borderRadius: '6px',
                padding: '10px 14px',
                fontSize: '11px',
                fontFamily: 'var(--rg-font-mono)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
              }}
            >
              <div style={{ fontWeight: 'bold', color: 'var(--rg-text-primary)', marginBottom: '2px' }}>
                OPERATIONAL LEGEND
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#dc2626', boxShadow: '0 0 6px #dc2626' }} />
                <span>Critical Hazard Pin</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#d97706' }} />
                <span>High Severity Hazard</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#38bdf8' }} />
                <span>Medium / Local Advisory</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '11px' }}>⛺</span>
                <span style={{ color: 'var(--rg-cyan-subtle)' }}>Evacuation Shelter</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '10px' }}>🛡️</span>
                <span style={{ color: 'var(--rg-amber-light)' }}>Response Team Unit</span>
              </div>
            </div>
          </div>
        </div>

        {/* Side Details Inspector & Unmapped Accompanying List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Selected Item Inspector Panel */}
          <div className="rg-panel" style={{ flex: 1 }}>
            <div className="rg-panel-header">
              <h3>
                {selectedItem ? (
                  <>
                    {selectedItem.type === 'incident' && '⚠️ Incident Inspector'}
                    {selectedItem.type === 'shelter' && '⛺ Shelter Inspector'}
                    {selectedItem.type === 'team' && '🛡️ Unit Inspector'}
                  </>
                ) : (
                  'Tactical Object Inspector'
                )}
              </h3>
            </div>
            <div className="rg-panel-body">
              {selectedItem ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {selectedItem.type === 'incident' && (
                    <>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-blue-subtle)' }}>
                            {selectedItem.data.incident_code}
                          </span>
                          <span
                            className="rg-pill"
                            style={{
                              backgroundColor: `${SEVERITY_COLORS[selectedItem.data.severity] || '#38bdf8'}22`,
                              color: SEVERITY_COLORS[selectedItem.data.severity] || '#38bdf8',
                              border: `1px solid ${SEVERITY_COLORS[selectedItem.data.severity] || '#38bdf8'}`,
                              textTransform: 'uppercase',
                              fontWeight: 700,
                            }}
                          >
                            {selectedItem.data.severity}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--rg-text-primary)', margin: '4px 0 8px 0' }}>
                          {selectedItem.data.title}
                        </h4>
                        <p style={{ fontSize: '13px', color: 'var(--rg-text-secondary)', lineHeight: 1.5 }}>
                          {selectedItem.data.description || 'No detailed incident description provided.'}
                        </p>
                      </div>

                      <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px', border: '1px solid var(--rg-border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                        <div>
                          <strong style={{ color: 'var(--rg-text-muted)' }}>Location:</strong> {selectedItem.data.location_description || 'Unspecified'}
                        </div>
                        <div>
                          <strong style={{ color: 'var(--rg-text-muted)' }}>Status:</strong> <span style={{ textTransform: 'capitalize' }}>{selectedItem.data.status}</span>
                        </div>
                        <div>
                          <strong style={{ color: 'var(--rg-text-muted)' }}>Coordinates:</strong>{' '}
                          <span style={{ fontFamily: 'var(--rg-font-mono)' }}>
                            {typeof selectedItem.data.latitude === 'number'
                              ? `${selectedItem.data.latitude.toFixed(4)}° N, ${selectedItem.data.longitude.toFixed(4)}° E`
                              : 'Location Coordinates Unavailable'}
                          </span>
                        </div>
                        {selectedItem.data.affected_population > 0 && (
                          <div>
                            <strong style={{ color: 'var(--rg-text-muted)' }}>Est. Impact:</strong> {selectedItem.data.affected_population.toLocaleString()} civilians
                          </div>
                        )}
                        {selectedItem.data.assigned_commander && (
                          <div>
                            <strong style={{ color: 'var(--rg-text-muted)' }}>Commander:</strong> {selectedItem.data.assigned_commander}
                          </div>
                        )}
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          className="rg-btn rg-btn-primary"
                          style={{ flex: 1 }}
                          onClick={() => handleCenterOnSelected(selectedItem)}
                        >
                          Focus on Map
                        </button>
                      </div>
                    </>
                  )}

                  {selectedItem.type === 'shelter' && (
                    <>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-cyan-subtle)' }}>
                            {selectedItem.data.shelter_type}
                          </span>
                          <span className={`rg-pill rg-pill-${selectedItem.data.status === 'open' ? 'nominal' : 'critical'}`}>
                            {selectedItem.data.status.toUpperCase()}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '16px', fontWeight: 700, margin: '6px 0 8px 0' }}>
                          {selectedItem.data.name}
                        </h4>
                        <p style={{ fontSize: '12px', color: 'var(--rg-text-secondary)' }}>
                          📍 {selectedItem.data.address}
                        </p>
                      </div>

                      <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px', border: '1px solid var(--rg-border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                        <div>
                          <strong>Occupancy:</strong> {selectedItem.data.current_occupancy} / {selectedItem.data.capacity} ({selectedItem.data.occupancy_pct}%)
                        </div>
                        <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--rg-bg-inset)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(100, selectedItem.data.occupancy_pct)}%`,
                              height: '100%',
                              backgroundColor: selectedItem.data.occupancy_pct > 90 ? 'var(--rg-red-light)' : 'var(--rg-cyan-subtle)',
                            }}
                          />
                        </div>
                        <div>
                          <strong>Remaining Capacity:</strong> {selectedItem.data.remaining_capacity} persons
                        </div>
                        <div>
                          <strong>Manager:</strong> {selectedItem.data.contact_person} ({selectedItem.data.contact_phone})
                        </div>
                      </div>

                      <button
                        className="rg-btn rg-btn-primary"
                        onClick={() => handleCenterOnSelected(selectedItem)}
                      >
                        Focus on Map
                      </button>
                    </>
                  )}

                  {selectedItem.type === 'team' && (
                    <>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-amber-light)' }}>
                            {selectedItem.data.unit_type}
                          </span>
                          <span className={`rg-pill rg-pill-${selectedItem.data.current_status === 'available' ? 'nominal' : 'warning'}`}>
                            {selectedItem.data.current_status.toUpperCase()}
                          </span>
                        </div>
                        <h4 style={{ fontSize: '16px', fontWeight: 700, margin: '6px 0 8px 0' }}>
                          {selectedItem.data.team_callsign}
                        </h4>
                        <p style={{ fontSize: '12px', color: 'var(--rg-text-secondary)' }}>
                          Base: {selectedItem.data.base_location}
                        </p>
                      </div>

                      <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px', border: '1px solid var(--rg-border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '12px' }}>
                        <div>
                          <strong>Personnel:</strong> {selectedItem.data.personnel_count} responders
                        </div>
                        <div>
                          <strong>Commander:</strong> {selectedItem.data.commander_name}
                        </div>
                        <div>
                          <strong>Comms Channel:</strong> <span style={{ fontFamily: 'var(--rg-font-mono)' }}>{selectedItem.data.contact_channel}</span>
                        </div>
                        <div>
                          <strong>Active Task Load:</strong> {selectedItem.data.active_tasks_count || 0} missions
                        </div>
                      </div>

                      <button
                        className="rg-btn rg-btn-primary"
                        onClick={() => handleCenterOnSelected(selectedItem)}
                      >
                        Focus on Map
                      </button>
                    </>
                  )}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 10px', color: 'var(--rg-text-muted)' }}>
                  Click any map pin or select an incident below to inspect telemetry.
                </div>
              )}
            </div>
          </div>

          {/* Accompanying List: Incidents Lacking Coordinates */}
          <div className="rg-panel">
            <div
              className="rg-panel-header"
              style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onClick={() => setShowUnmapped(!showUnmapped)}
            >
              <h3 style={{ fontSize: '13px' }}>
                ⚠️ Unmapped Incidents ({unmappedIncidents.length})
              </h3>
              <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                {showUnmapped ? '▲ Collapse' : '▼ Expand'}
              </span>
            </div>
            {showUnmapped && (
              <div className="rg-panel-body" style={{ maxHeight: '180px', overflowY: 'auto', padding: '8px' }}>
                {unmappedIncidents.length === 0 ? (
                  <div style={{ fontSize: '12px', color: 'var(--rg-text-muted)', textAlign: 'center', padding: '10px' }}>
                    All incidents have valid coordinates. No unmapped entries.
                  </div>
                ) : (
                  unmappedIncidents.map((u) => (
                    <div
                      key={u.id}
                      onClick={() => setSelectedItem({ type: 'incident', data: u })}
                      style={{
                        padding: '8px 10px',
                        backgroundColor: 'var(--rg-bg-card)',
                        borderRadius: '4px',
                        marginBottom: '6px',
                        cursor: 'pointer',
                        border: '1px solid var(--rg-border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                        <span style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{u.title}</span>
                        <span className="rg-pill rg-pill-critical" style={{ fontSize: '9px' }}>
                          NO COORDS
                        </span>
                      </div>
                      <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', marginTop: '2px' }}>
                        📍 {u.location_description || 'Unspecified'} • {u.category}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
