import React, { useState, useEffect, useCallback } from 'react';
import { LoadingState, ModalDialog } from './StateComponents';

const STATUS_PILLS = {
  available: 'nominal',
  assigned: 'warning',
  busy: 'critical',
  offline: 'minor',
};

export default function RakshaTeams() {
  const [teams, setTeams] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [unitTypeFilter, setUnitTypeFilter] = useState('');
  const [search, setSearch] = useState('');

  // Modals
  const [createModal, setCreateModal] = useState(false);
  const [editTeam, setEditTeam] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    team_callsign: '',
    unit_type: 'NDRF Urban Search & Rescue',
    personnel_count: 10,
    commander_name: '',
    contact_channel: '',
    current_status: 'available',
    base_location: '',
    current_latitude: '',
    current_longitude: '',
  });

  const fetchTeams = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (unitTypeFilter) params.append('unit_type', unitTypeFilter);
      if (search) params.append('search', search);

      const res = await fetch(`/api/v1/teams?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch teams`);
      const data = await res.json();
      setTeams(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Teams fetch error:', err);
      setError(err.message || 'Failed to load teams roster.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, unitTypeFilter, search]);

  useEffect(() => {
    fetchTeams();
  }, [fetchTeams]);

  // Handle Create / Edit Submit
  const handleSaveTeam = async (e) => {
    e.preventDefault();
    setActionError(null);

    const payload = {
      team_callsign: formData.team_callsign.trim(),
      unit_type: formData.unit_type.trim(),
      personnel_count: parseInt(formData.personnel_count, 10) || 1,
      commander_name: formData.commander_name.trim(),
      contact_channel: formData.contact_channel.trim(),
      current_status: formData.current_status,
      base_location: formData.base_location.trim(),
      current_latitude: formData.current_latitude ? parseFloat(formData.current_latitude) : null,
      current_longitude: formData.current_longitude ? parseFloat(formData.current_longitude) : null,
    };

    try {
      const url = editTeam ? `/api/v1/teams/${editTeam.id}` : '/api/v1/teams';
      const method = editTeam ? 'PATCH' : 'POST';

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
      setEditTeam(null);
      fetchTeams();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Quick Status Transition
  const handleQuickStatusChange = async (teamId, newStatus) => {
    try {
      const res = await fetch(`/api/v1/teams/${teamId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify({ current_status: newStatus }),
      });
      if (res.ok) {
        fetchTeams();
      }
    } catch (err) {
      console.error('Quick status update failed:', err);
    }
  };

  // Delete Action
  const handleDeleteTeam = async () => {
    if (!deleteConfirm) return;
    setActionError(null);
    try {
      const res = await fetch(`/api/v1/teams/${deleteConfirm.id}`, {
        method: 'DELETE',
        headers: {
          'X-Rakshagrid-Dev-Role': 'admin',
        },
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Failed to delete team (${res.status})`);
      }

      setDeleteConfirm(null);
      fetchTeams();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const openCreateModal = () => {
    setEditTeam(null);
    setFormData({
      team_callsign: '',
      unit_type: 'NDRF Urban Search & Rescue',
      personnel_count: 10,
      commander_name: '',
      contact_channel: 'VHF CH-16',
      current_status: 'available',
      base_location: '',
      current_latitude: '',
      current_longitude: '',
    });
    setActionError(null);
    setCreateModal(true);
  };

  const openEditModal = (t) => {
    setEditTeam(t);
    setFormData({
      team_callsign: t.team_callsign,
      unit_type: t.unit_type,
      personnel_count: t.personnel_count,
      commander_name: t.commander_name,
      contact_channel: t.contact_channel,
      current_status: t.current_status,
      base_location: t.base_location,
      current_latitude: t.current_latitude !== null ? t.current_latitude : '',
      current_longitude: t.current_longitude !== null ? t.current_longitude : '',
    });
    setActionError(null);
    setCreateModal(true);
  };

  const totalPersonnel = teams.reduce((acc, t) => acc + (t.personnel_count || 0), 0);
  const activeTeams = teams.filter((t) => t.current_status === 'assigned' || t.current_status === 'busy').length;
  const availableTeams = teams.filter((t) => t.current_status === 'available').length;

  return (
    <>
      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Emergency Response Units & Personnel</h2>
          <p>Personnel mobilization, communications channels, and tactical field staging</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={openCreateModal}>
            + Register Unit
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="rg-kpi-grid" style={{ marginBottom: '20px' }}>
        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">Total Responders</div>
          <div className="rg-kpi-value">{totalPersonnel}</div>
          <div className="rg-kpi-subtext">Across {total} registered units</div>
        </div>
        <div className="rg-kpi-card warning">
          <div className="rg-kpi-header">Active in Field</div>
          <div className="rg-kpi-value">{activeTeams} Units</div>
          <div className="rg-kpi-subtext">Assigned to active missions</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Available Reserve</div>
          <div className="rg-kpi-value">{availableTeams} Units</div>
          <div className="rg-kpi-subtext">Ready for immediate dispatch</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Roster Readiness</div>
          <div className="rg-kpi-value">
            {total > 0 ? Math.round(((total - teams.filter((t) => t.current_status === 'offline').length) / total) * 100) : 100}%
          </div>
          <div className="rg-kpi-subtext">Operational capability score</div>
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
            placeholder="Search callsign, commander, base..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: '260px' }}
          />

          <select
            className="rg-input"
            style={{ width: '160px' }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="available">Available</option>
            <option value="assigned">Assigned</option>
            <option value="busy">Busy</option>
            <option value="offline">Offline</option>
          </select>

          <input
            type="text"
            className="rg-input"
            placeholder="Filter unit type..."
            value={unitTypeFilter}
            onChange={(e) => setUnitTypeFilter(e.target.value)}
            style={{ width: '180px' }}
          />
        </div>

        <button className="rg-btn rg-btn-outline" onClick={fetchTeams}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="rg-alert-banner" style={{ backgroundColor: '#751a1a', color: '#f87171', marginBottom: '16px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Unit Roster Table */}
      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Unit Roster & Telemetry</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            RECORDS: {teams.length}
          </span>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Querying team telemetry..." />
          ) : teams.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--rg-text-muted)' }}>
              No response units match the current criteria.
            </div>
          ) : (
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Callsign</th>
                    <th>Type / Specialization</th>
                    <th>Personnel</th>
                    <th>Commander</th>
                    <th>Comms Frequency</th>
                    <th>Base Staging</th>
                    <th>Status</th>
                    <th>Active Missions</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {teams.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600, color: 'var(--rg-text-primary)' }}>
                        {t.team_callsign}
                      </td>
                      <td style={{ color: 'var(--rg-text-secondary)', fontSize: '12px' }}>{t.unit_type}</td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{t.personnel_count}</td>
                      <td>{t.commander_name}</td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-blue-subtle)' }}>
                        {t.contact_channel}
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--rg-text-secondary)' }}>{t.base_location}</td>
                      <td>
                        <select
                          className={`rg-pill rg-pill-${STATUS_PILLS[t.current_status] || 'minor'}`}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '11px',
                            fontWeight: 600,
                          }}
                          value={t.current_status}
                          onChange={(e) => handleQuickStatusChange(t.id, e.target.value)}
                        >
                          <option value="available" style={{ background: '#1b2029', color: '#fff' }}>Available</option>
                          <option value="assigned" style={{ background: '#1b2029', color: '#fff' }}>Assigned</option>
                          <option value="busy" style={{ background: '#1b2029', color: '#fff' }}>Busy</option>
                          <option value="offline" style={{ background: '#1b2029', color: '#fff' }}>Offline</option>
                        </select>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', textAlign: 'center' }}>
                        {t.active_tasks_count > 0 ? (
                          <span style={{ color: 'var(--rg-amber-light)', fontWeight: 700 }}>
                            {t.active_tasks_count} active
                          </span>
                        ) : (
                          <span style={{ color: 'var(--rg-text-muted)' }}>0</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '4px 8px', fontSize: '11px' }}
                            onClick={() => openEditModal(t)}
                          >
                            Edit
                          </button>
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '4px 8px', fontSize: '11px', color: 'var(--rg-red-light)', borderColor: 'var(--rg-border-subtle)' }}
                            onClick={() => {
                              setActionError(null);
                              setDeleteConfirm(t);
                            }}
                          >
                            Delete
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

      {/* Create / Edit Team Modal */}
      {createModal && (
        <ModalDialog
          title={editTeam ? `Edit Unit: ${editTeam.team_callsign}` : 'Register New Response Unit'}
          onClose={() => setCreateModal(false)}
        >
          <form onSubmit={handleSaveTeam}>
            {actionError && (
              <div style={{ backgroundColor: 'var(--rg-red-muted)', color: 'var(--rg-red-light)', padding: '8px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
                ⚠️ {actionError}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Team Callsign *
                </label>
                <input
                  type="text"
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. NDRF-12-BRAVO"
                  value={formData.team_callsign}
                  onChange={(e) => setFormData({ ...formData, team_callsign: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Unit Specialization *
                </label>
                <input
                  type="text"
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. NDRF Urban Search & Rescue"
                  value={formData.unit_type}
                  onChange={(e) => setFormData({ ...formData, unit_type: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Personnel Count *
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.personnel_count}
                  onChange={(e) => setFormData({ ...formData, personnel_count: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Lead Commander *
                </label>
                <input
                  type="text"
                  required
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="Officer name"
                  value={formData.commander_name}
                  onChange={(e) => setFormData({ ...formData, commander_name: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Current Status
                </label>
                <select
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.current_status}
                  onChange={(e) => setFormData({ ...formData, current_status: e.target.value })}
                >
                  <option value="available">Available</option>
                  <option value="assigned">Assigned</option>
                  <option value="busy">Busy</option>
                  <option value="offline">Offline</option>
                </select>
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Contact / Radio Frequency *
              </label>
              <input
                type="text"
                required
                className="rg-input"
                style={{ width: '100%' }}
                placeholder="e.g. VHF CH-16 (156.800 MHz)"
                value={formData.contact_channel}
                onChange={(e) => setFormData({ ...formData, contact_channel: e.target.value })}
              />
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Base Staging Location *
              </label>
              <input
                type="text"
                required
                className="rg-input"
                style={{ width: '100%' }}
                placeholder="e.g. Guwahati Riverfront Staging Base"
                value={formData.base_location}
                onChange={(e) => setFormData({ ...formData, base_location: e.target.value })}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Current Latitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. 26.182"
                  value={formData.current_latitude}
                  onChange={(e) => setFormData({ ...formData, current_latitude: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Current Longitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. 91.745"
                  value={formData.current_longitude}
                  onChange={(e) => setFormData({ ...formData, current_longitude: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" className="rg-btn rg-btn-outline" onClick={() => setCreateModal(false)}>
                Cancel
              </button>
              <button type="submit" className="rg-btn rg-btn-primary">
                {editTeam ? 'Save Modifications' : 'Register Unit'}
              </button>
            </div>
          </form>
        </ModalDialog>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <ModalDialog title={`Confirm Deletion: ${deleteConfirm.team_callsign}`} onClose={() => setDeleteConfirm(null)}>
          <div style={{ fontSize: '13px', lineHeight: 1.5, marginBottom: '14px' }}>
            Are you sure you want to delete unit <strong>{deleteConfirm.team_callsign}</strong>?
            This will permanently remove the unit record from the active roster.
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
              onClick={handleDeleteTeam}
            >
              Permanently Delete Unit
            </button>
          </div>
        </ModalDialog>
      )}
    </>
  );
}
