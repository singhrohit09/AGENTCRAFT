import React, { useState, useEffect, useCallback } from 'react';
import { LoadingState, ModalDialog } from './StateComponents';

const STATUS_PILLS = {
  open: 'nominal',
  full: 'critical',
  closed: 'muted',
};

export default function RakshaShelters() {
  const [shelters, setShelters] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [shelterTypeFilter, setShelterTypeFilter] = useState('');
  const [availableOnly, setAvailableOnly] = useState(false);
  const [search, setSearch] = useState('');

  // Modals
  const [createModal, setCreateModal] = useState(false);
  const [editShelter, setEditShelter] = useState(null);
  const [admitShelter, setAdmitShelter] = useState(null);
  const [dischargeShelter, setDischargeShelter] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Forms
  const [formData, setFormData] = useState({
    name: '',
    shelter_type: 'Cyclone Shelter',
    capacity: 500,
    current_occupancy: 0,
    address: '',
    contact_person: '',
    contact_phone: '',
    supplies_status: 'adequate',
    power_backup: true,
    medical_station: true,
    status: 'open',
    latitude: '',
    longitude: '',
  });

  const [admissionCount, setAdmissionCount] = useState(1);
  const [dischargeCount, setDischargeCount] = useState(1);

  const fetchShelters = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (shelterTypeFilter) params.append('shelter_type', shelterTypeFilter);
      if (availableOnly) params.append('available_only', 'true');
      if (search) params.append('search', search);

      const res = await fetch(`/api/v1/shelters?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch shelters`);
      const data = await res.json();
      setShelters(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Shelters fetch error:', err);
      setError(err.message || 'Failed to query shelters.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, shelterTypeFilter, availableOnly, search]);

  useEffect(() => {
    fetchShelters();
  }, [fetchShelters]);

  const handleSaveShelter = async (e) => {
    e.preventDefault();
    setActionError(null);

    const payload = {
      name: formData.name.trim(),
      shelter_type: formData.shelter_type.trim(),
      capacity: parseInt(formData.capacity, 10) || 1,
      current_occupancy: parseInt(formData.current_occupancy, 10) || 0,
      address: formData.address.trim(),
      contact_person: formData.contact_person.trim() || 'Shelter Manager',
      contact_phone: formData.contact_phone.trim() || 'N/A',
      supplies_status: formData.supplies_status,
      power_backup: formData.power_backup,
      medical_station: formData.medical_station,
      status: formData.status,
      latitude: formData.latitude ? parseFloat(formData.latitude) : null,
      longitude: formData.longitude ? parseFloat(formData.longitude) : null,
    };

    try {
      const url = editShelter ? `/api/v1/shelters/${editShelter.id}` : '/api/v1/shelters';
      const method = editShelter ? 'PATCH' : 'POST';

      const res = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned status ${res.status}`);
      }

      setCreateModal(false);
      setEditShelter(null);
      fetchShelters();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleAdmit = async (e) => {
    e.preventDefault();
    if (!admitShelter) return;
    setActionError(null);

    try {
      const res = await fetch(`/api/v1/shelters/${admitShelter.id}/admit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify({ count: parseInt(admissionCount, 10) }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Admission error (${res.status})`);
      }

      setAdmitShelter(null);
      fetchShelters();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleDischarge = async (e) => {
    e.preventDefault();
    if (!dischargeShelter) return;
    setActionError(null);

    try {
      const res = await fetch(`/api/v1/shelters/${dischargeShelter.id}/discharge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify({ count: parseInt(dischargeCount, 10) }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Discharge error (${res.status})`);
      }

      setDischargeShelter(null);
      fetchShelters();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setActionError(null);

    try {
      const res = await fetch(`/api/v1/shelters/${deleteConfirm.id}`, {
        method: 'DELETE',
        headers: { 'X-Rakshagrid-Dev-Role': 'admin' },
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Deletion error (${res.status})`);
      }

      setDeleteConfirm(null);
      fetchShelters();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const openCreateModal = () => {
    setEditShelter(null);
    setFormData({
      name: '',
      shelter_type: 'Cyclone Shelter',
      capacity: 500,
      current_occupancy: 0,
      address: '',
      contact_person: '',
      contact_phone: '',
      supplies_status: 'adequate',
      power_backup: true,
      medical_station: true,
      status: 'open',
      latitude: '',
      longitude: '',
    });
    setActionError(null);
    setCreateModal(true);
  };

  const openEditModal = (sh) => {
    setEditShelter(sh);
    setFormData({
      name: sh.name,
      shelter_type: sh.shelter_type,
      capacity: sh.capacity,
      current_occupancy: sh.current_occupancy,
      address: sh.address,
      contact_person: sh.contact_person,
      contact_phone: sh.contact_phone,
      supplies_status: sh.supplies_status,
      power_backup: sh.power_backup,
      medical_station: sh.medical_station,
      status: sh.status,
      latitude: sh.latitude !== null ? sh.latitude : '',
      longitude: sh.longitude !== null ? sh.longitude : '',
    });
    setActionError(null);
    setCreateModal(true);
  };

  const totalCapacity = shelters.reduce((acc, s) => acc + (s.capacity || 0), 0);
  const totalOccupancy = shelters.reduce((acc, s) => acc + (s.current_occupancy || 0), 0);
  const overallPct = totalCapacity > 0 ? Math.round((totalOccupancy / totalCapacity) * 100) : 0;
  const openCount = shelters.filter((s) => s.status === 'open').length;

  return (
    <>
      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Evacuation Shelters & Relief Camps</h2>
          <p>Real-time occupancy tracking, capacity buffers, generator backups, and medical triage facilities</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={openCreateModal}>
            + Add Relief Shelter
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="rg-kpi-grid" style={{ marginBottom: '20px' }}>
        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">Sheltered Population</div>
          <div className="rg-kpi-value">{totalOccupancy.toLocaleString()}</div>
          <div className="rg-kpi-subtext">Across {total} designated facilities</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Total Safe Capacity</div>
          <div className="rg-kpi-value">{totalCapacity.toLocaleString()}</div>
          <div className="rg-kpi-subtext">Verified structural occupancy limit</div>
        </div>
        <div className="rg-kpi-card warning">
          <div className="rg-kpi-header">Buffer Utilization</div>
          <div className="rg-kpi-value">{overallPct}%</div>
          <div className="rg-kpi-subtext">{Math.max(0, totalCapacity - totalOccupancy).toLocaleString()} spaces remaining</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Active Facilities</div>
          <div className="rg-kpi-value">{openCount} Open</div>
          <div className="rg-kpi-subtext">Ready for immediate intake</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
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
          <input
            type="text"
            className="rg-input"
            placeholder="Search shelter name, location, manager..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '260px' }}
          />

          <select
            className="rg-input"
            style={{ width: '150px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="full">Full</option>
            <option value="closed">Closed</option>
          </select>

          <input
            type="text"
            className="rg-input"
            placeholder="Filter shelter type..."
            value={shelterTypeFilter}
            onChange={(e) => setShelterTypeFilter(e.target.value)}
            style={{ width: '180px' }}
          />

          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer', marginLeft: '6px' }}>
            <input
              type="checkbox"
              checked={availableOnly}
              onChange={(e) => setAvailableOnly(e.target.checked)}
            />
            <span style={{ color: 'var(--rg-cyan-subtle)' }}>Available Only</span>
          </label>
        </div>

        <button className="rg-btn rg-btn-outline" onClick={fetchShelters}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="rg-alert-banner" style={{ backgroundColor: '#751a1a', color: '#f87171', marginBottom: '16px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Designated Relief Facilities Table */}
      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Designated Relief Facilities</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            RECORDS: {shelters.length}
          </span>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Querying shelter occupancy..." />
          ) : shelters.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--rg-text-muted)' }}>
              No relief facilities match the filter criteria.
            </div>
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
                    <th>Remaining Space</th>
                    <th>Support Facilities</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {shelters.map((s) => (
                    <tr key={s.id}>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{s.name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', marginTop: '2px' }}>
                          📍 {s.address}
                        </div>
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--rg-text-secondary)' }}>{s.shelter_type}</td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{s.capacity.toLocaleString()}</td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700 }}>
                        {s.current_occupancy.toLocaleString()}
                      </td>
                      <td style={{ width: '130px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', fontFamily: 'var(--rg-font-mono)', marginBottom: '3px' }}>
                          <span>{s.occupancy_pct}%</span>
                        </div>
                        <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--rg-bg-inset)', borderRadius: '3px', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.min(100, s.occupancy_pct)}%`,
                              height: '100%',
                              backgroundColor: s.occupancy_pct > 90 ? 'var(--rg-red-light)' : s.occupancy_pct > 70 ? 'var(--rg-amber-light)' : 'var(--rg-cyan-subtle)',
                            }}
                          />
                        </div>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', textAlign: 'center' }}>
                        <span style={{ color: s.remaining_capacity > 0 ? 'var(--rg-olive-light)' : 'var(--rg-red-light)', fontWeight: 700 }}>
                          {s.remaining_capacity.toLocaleString()}
                        </span>
                      </td>
                      <td style={{ fontSize: '11px' }}>
                        {s.power_backup && <span title="Backup Power Generator">⚡ </span>}
                        {s.medical_station && <span title="On-site Medical Triage Point">🏥 </span>}
                        <span style={{ color: 'var(--rg-text-muted)' }}>{s.supplies_status}</span>
                      </td>
                      <td>
                        <span className={`rg-pill rg-pill-${STATUS_PILLS[s.status] || 'minor'}`}>
                          {s.status.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '5px' }}>
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '3px 7px', fontSize: '11px', color: 'var(--rg-cyan-subtle)', borderColor: 'var(--rg-border-subtle)' }}
                            disabled={s.status === 'closed' || s.remaining_capacity <= 0}
                            onClick={() => {
                              setActionError(null);
                              setAdmissionCount(1);
                              setAdmitShelter(s);
                            }}
                          >
                            + Admit
                          </button>
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '3px 7px', fontSize: '11px' }}
                            disabled={s.current_occupancy <= 0}
                            onClick={() => {
                              setActionError(null);
                              setDischargeCount(1);
                              setDischargeShelter(s);
                            }}
                          >
                            - Discharge
                          </button>
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '3px 7px', fontSize: '11px' }}
                            onClick={() => openEditModal(s)}
                          >
                            Edit
                          </button>
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '3px 7px', fontSize: '11px', color: 'var(--rg-red-light)', borderColor: 'var(--rg-border-subtle)' }}
                            onClick={() => {
                              setActionError(null);
                              setDeleteConfirm(s);
                            }}
                          >
                            Del
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add / Edit Shelter Modal */}
      {createModal && (
        <ModalDialog
          title={editShelter ? `Edit Shelter: ${editShelter.name}` : 'Register Evacuation Shelter'}
          onClose={() => setCreateModal(false)}
        >
          <form onSubmit={handleSaveShelter}>
            {actionError && (
              <div style={{ backgroundColor: 'var(--rg-red-muted)', color: 'var(--rg-red-light)', padding: '8px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
                ⚠️ {actionError}
              </div>
            )}

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Facility Name *
              </label>
              <input
                type="text"
                required
                className="rg-input"
                style={{ width: '100%' }}
                placeholder="e.g. Puri Coastal Multi-Purpose Cyclone Shelter"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Shelter Type *
                </label>
                <input
                  type="text"
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. Cyclone Shelter, School Hall, Stadium"
                  value={formData.shelter_type}
                  onChange={(e) => setFormData({ ...formData, shelter_type: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Operating Status
                </label>
                <select
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="open">Open (Accepting Admissions)</option>
                  <option value="full">Full (At Max Capacity)</option>
                  <option value="closed">Closed (Decommissioned)</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Max Capacity *
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Current Headcount Occupancy
                </label>
                <input
                  type="number"
                  min="0"
                  max={formData.capacity}
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.current_occupancy}
                  onChange={(e) => setFormData({ ...formData, current_occupancy: e.target.value })}
                />
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Physical Address / Staging Location *
              </label>
              <textarea
                required
                rows={2}
                className="rg-input"
                style={{ width: '100%', resize: 'vertical' }}
                placeholder="Physical landmark, sector, or street address..."
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Manager / Contact Person
                </label>
                <input
                  type="text"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="Officer name"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Emergency Phone
                </label>
                <input
                  type="text"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="Phone or hotline"
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Latitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. 19.805"
                  value={formData.latitude}
                  onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Longitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. 85.818"
                  value={formData.longitude}
                  onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '20px', marginBottom: '18px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.power_backup}
                  onChange={(e) => setFormData({ ...formData, power_backup: e.target.checked })}
                />
                <span>⚡ Generator Backup Active</span>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={formData.medical_station}
                  onChange={(e) => setFormData({ ...formData, medical_station: e.target.checked })}
                />
                <span>🏥 Medical Triage Post Active</span>
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" className="rg-btn rg-btn-outline" onClick={() => setCreateModal(false)}>
                Cancel
              </button>
              <button type="submit" className="rg-btn rg-btn-primary">
                {editShelter ? 'Save Modifications' : 'Register Shelter'}
              </button>
            </div>
          </form>
        </ModalDialog>
      )}

      {/* Admit Occupants Modal */}
      {admitShelter && (
        <ModalDialog
          title={`Admit Evacuees: ${admitShelter.name}`}
          onClose={() => setAdmitShelter(null)}
        >
          <form onSubmit={handleAdmit}>
            {actionError && (
              <div style={{ backgroundColor: 'var(--rg-red-muted)', color: 'var(--rg-red-light)', padding: '8px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
                ⚠️ {actionError}
              </div>
            )}

            <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
              <div>Current Occupancy: <strong>{admitShelter.current_occupancy}</strong> / {admitShelter.capacity}</div>
              <div>Available Spaces Remaining: <strong style={{ color: 'var(--rg-cyan-subtle)' }}>{admitShelter.remaining_capacity}</strong></div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Number of Persons to Admit *
              </label>
              <input
                type="number"
                min="1"
                max={admitShelter.remaining_capacity}
                required
                className="rg-input"
                style={{ width: '100%' }}
                value={admissionCount}
                onChange={(e) => setAdmissionCount(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" className="rg-btn rg-btn-outline" onClick={() => setAdmitShelter(null)}>
                Cancel
              </button>
              <button type="submit" className="rg-btn rg-btn-primary">
                Confirm Intake ({admissionCount})
              </button>
            </div>
          </form>
        </ModalDialog>
      )}

      {/* Discharge Occupants Modal */}
      {dischargeShelter && (
        <ModalDialog
          title={`Discharge Evacuees: ${dischargeShelter.name}`}
          onClose={() => setDischargeShelter(null)}
        >
          <form onSubmit={handleDischarge}>
            {actionError && (
              <div style={{ backgroundColor: 'var(--rg-red-muted)', color: 'var(--rg-red-light)', padding: '8px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
                ⚠️ {actionError}
              </div>
            )}

            <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
              <div>Current Occupancy: <strong>{dischargeShelter.current_occupancy}</strong></div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Number of Persons to Discharge *
              </label>
              <input
                type="number"
                min="1"
                max={dischargeShelter.current_occupancy}
                required
                className="rg-input"
                style={{ width: '100%' }}
                value={dischargeCount}
                onChange={(e) => setDischargeCount(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" className="rg-btn rg-btn-outline" onClick={() => setDischargeShelter(null)}>
                Cancel
              </button>
              <button type="submit" className="rg-btn rg-btn-primary">
                Confirm Discharge ({dischargeCount})
              </button>
            </div>
          </form>
        </ModalDialog>
      )}

      {/* Delete Shelter Confirmation Modal */}
      {deleteConfirm && (
        <ModalDialog title={`Confirm Deletion: ${deleteConfirm.name}`} onClose={() => setDeleteConfirm(null)}>
          <div style={{ fontSize: '13px', lineHeight: 1.5, marginBottom: '14px' }}>
            Are you sure you want to delete facility <strong>{deleteConfirm.name}</strong>?
            Shelters with active occupants cannot be deleted.
          </div>

          {actionError && (
            <div style={{ backgroundColor: 'var(--rg-red-muted)', color: 'var(--rg-red-light)', padding: '8px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
              ⚠️ {actionError}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button className="rg-btn rg-btn-outline" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </button>
            <button
              className="rg-btn rg-btn-primary"
              style={{ backgroundColor: 'var(--rg-red-base)', borderColor: 'var(--rg-red-base)' }}
              onClick={handleDelete}
            >
              Permanently Delete Shelter
            </button>
          </div>
        </ModalDialog>
      )}
    </>
  );
}
