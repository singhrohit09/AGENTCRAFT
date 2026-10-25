import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, LoadingState } from './StateComponents';

export default function RakshaShelters() {
  const [shelters, setShelters] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchShelters = useCallback(async () => {
    try {
      const res = await fetch('/api/rakshagrid/shelters');
      if (res.ok) {
        const data = await res.json();
        setShelters(data);
      }
    } catch (e) {
      console.error('Failed to fetch shelters:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    fetchShelters().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [fetchShelters]);

  return (
    <>
      <DemoNoticeBanner text="Evacuation Shelters and Relief Camps Management. Demonstration facilities active." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Evacuation Shelters & Relief Camps</h2>
          <p>Real-time occupancy tracking, capacity buffers, generator backups, and medical triage points</p>
        </div>
      </div>

      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Designated Relief Facilities</h3>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Querying shelter occupancy..." />
          ) : (
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Facility Name</th>
                    <th>Type</th>
                    <th>Capacity</th>
                    <th>Occupancy</th>
                    <th>Utilization</th>
                    <th>Supplies</th>
                    <th>Power Backup</th>
                    <th>Medical Triage</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {shelters.map((s) => (
                    <tr key={s.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{s.name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>{s.location_name}</div>
                      </td>
                      <td>
                        <span style={{ textTransform: 'capitalize', fontSize: '11px' }}>
                          {s.shelter_type.replace('_', ' ')}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{s.capacity.toLocaleString()}</td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{s.current_occupancy.toLocaleString()}</td>
                      <td style={{ width: '140px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div style={{ flex: 1, height: '6px', backgroundColor: 'var(--rg-bg-inset)', borderRadius: '3px', overflow: 'hidden' }}>
                            <div
                              style={{
                                width: `${Math.min(100, s.occupancy_percent)}%`,
                                height: '100%',
                                backgroundColor: s.occupancy_percent >= 90 ? 'var(--rg-red-light)' : s.occupancy_percent >= 75 ? 'var(--rg-amber-light)' : 'var(--rg-olive-light)',
                              }}
                            />
                          </div>
                          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)' }}>{s.occupancy_percent}%</span>
                        </div>
                      </td>
                      <td>
                        <span className={`rg-pill ${s.supplies_status === 'adequate' ? 'rg-pill-moderate' : s.supplies_status === 'low' ? 'rg-pill-severe' : 'rg-pill-critical'}`}>
                          {s.supplies_status}
                        </span>
                      </td>
                      <td>
                        <span style={{ color: s.power_backup ? 'var(--rg-olive-light)' : 'var(--rg-red-light)', fontSize: '12px' }}>
                          {s.power_backup ? '✓ Online' : '✗ Offline'}
                        </span>
                      </td>
                      <td>
                        <span style={{ color: s.medical_station ? 'var(--rg-olive-light)' : 'var(--rg-text-muted)', fontSize: '12px' }}>
                          {s.medical_station ? '✓ Active' : 'None'}
                        </span>
                      </td>
                      <td>
                        <span className="rg-pill rg-pill-active">{s.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
