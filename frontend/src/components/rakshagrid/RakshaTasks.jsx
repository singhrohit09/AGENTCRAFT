import React, { useState, useEffect, useCallback } from 'react';
import { LoadingState, ModalDialog } from './StateComponents';

const PRIORITY_PILLS = {
  critical: 'critical',
  high: 'severe',
  medium: 'minor',
  low: 'nominal',
};

const STATUS_PILLS = {
  pending: 'minor',
  in_progress: 'warning',
  completed: 'nominal',
  cancelled: 'muted',
};

export default function RakshaTasks() {
  const [tasks, setTasks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Incidents and Teams options for dropdowns
  const [incidents, setIncidents] = useState([]);
  const [teams, setTeams] = useState([]);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [incidentFilter, setIncidentFilter] = useState('');
  const [search, setSearch] = useState('');

  // Modals
  const [createModal, setCreateModal] = useState(false);
  const [editTask, setEditTask] = useState(null);
  const [actionError, setActionError] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    incident_id: '',
    title: '',
    description: '',
    priority: 'high',
    assigned_team_id: '',
    target_latitude: '',
    target_longitude: '',
    due_at: '',
  });

  const fetchDropdownData = useCallback(async () => {
    try {
      const [incRes, tmRes] = await Promise.all([
        fetch('/api/v1/incidents?page_size=100'),
        fetch('/api/v1/teams?page_size=100'),
      ]);
      if (incRes.ok) {
        const d = await incRes.json();
        setIncidents(d.items || []);
      }
      if (tmRes.ok) {
        const d = await tmRes.json();
        setTeams(d.items || []);
      }
    } catch (e) {
      console.warn('Failed to load dropdown options:', e);
    }
  }, []);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (priorityFilter) params.append('priority', priorityFilter);
      if (incidentFilter) params.append('incident_id', incidentFilter);
      if (search) params.append('search', search);

      const res = await fetch(`/api/v1/tasks?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch response tasks`);
      const data = await res.json();
      setTasks(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Tasks fetch error:', err);
      setError(err.message || 'Failed to load task roster.');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, priorityFilter, incidentFilter, search]);

  useEffect(() => {
    fetchTasks();
    fetchDropdownData();
  }, [fetchTasks, fetchDropdownData]);

  const handleSaveTask = async (e) => {
    e.preventDefault();
    setActionError(null);

    const payload = {
      incident_id: formData.incident_id,
      title: formData.title.trim(),
      description: formData.description.trim(),
      priority: formData.priority,
      assigned_team_id: formData.assigned_team_id || null,
      target_latitude: formData.target_latitude ? parseFloat(formData.target_latitude) : null,
      target_longitude: formData.target_longitude ? parseFloat(formData.target_longitude) : null,
    };

    try {
      const url = editTask ? `/api/v1/tasks/${editTask.id}` : '/api/v1/tasks';
      const method = editTask ? 'PATCH' : 'POST';

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
        throw new Error(errJson.detail || `Server returned error (${res.status})`);
      }

      setCreateModal(false);
      setEditTask(null);
      fetchTasks();
    } catch (err) {
      setActionError(err.message);
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: {
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
      });
      if (res.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error('Failed to complete task:', e);
    }
  };

  const handleQuickStatusChange = async (taskId, newStatus) => {
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error('Failed to update status:', e);
    }
  };

  const openCreateModal = () => {
    setEditTask(null);
    setFormData({
      incident_id: incidents.length > 0 ? incidents[0].id : '',
      title: '',
      description: '',
      priority: 'high',
      assigned_team_id: '',
      target_latitude: '',
      target_longitude: '',
      due_at: '',
    });
    setActionError(null);
    setCreateModal(true);
  };

  const openEditModal = (t) => {
    setEditTask(t);
    setFormData({
      incident_id: t.incident_id,
      title: t.title,
      description: t.description,
      priority: t.priority,
      assigned_team_id: t.assigned_team_id || '',
      target_latitude: t.target_latitude !== null ? t.target_latitude : '',
      target_longitude: t.target_longitude !== null ? t.target_longitude : '',
      due_at: t.due_at || '',
    });
    setActionError(null);
    setCreateModal(true);
  };

  const inProgressCount = tasks.filter((t) => t.status === 'in_progress').length;
  const criticalCount = tasks.filter((t) => t.priority === 'critical' && t.status !== 'completed').length;
  const completedCount = tasks.filter((t) => t.status === 'completed').length;

  return (
    <>
      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Operational Response Tasks</h2>
          <p>Prioritized mission directives, emergency team allocations, and real-time execution status</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={openCreateModal}>
            + Dispatch Mission Task
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="rg-kpi-grid" style={{ marginBottom: '20px' }}>
        <div className="rg-kpi-card warning">
          <div className="rg-kpi-header">In Progress</div>
          <div className="rg-kpi-value">{inProgressCount} Missions</div>
          <div className="rg-kpi-subtext">Actively deployed in the field</div>
        </div>
        <div className="rg-kpi-card critical">
          <div className="rg-kpi-header">Critical Urgency</div>
          <div className="rg-kpi-value">{criticalCount} Tasks</div>
          <div className="rg-kpi-subtext">Highest dispatch priority</div>
        </div>
        <div className="rg-kpi-card nominal">
          <div className="rg-kpi-header">Completed Tasks</div>
          <div className="rg-kpi-value">{completedCount} Missions</div>
          <div className="rg-kpi-subtext">Audited and closed</div>
        </div>
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">Total Task Log</div>
          <div className="rg-kpi-value">{total} Entries</div>
          <div className="rg-kpi-subtext">Relational dispatch engine</div>
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
            placeholder="Search task title, description..."
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
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <select
            className="rg-input"
            style={{ width: '140px' }}
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            className="rg-input"
            style={{ width: '200px' }}
            value={incidentFilter}
            onChange={(e) => setIncidentFilter(e.target.value)}
          >
            <option value="">All Linked Incidents</option>
            {incidents.map((i) => (
              <option key={i.id} value={i.id}>
                {i.incident_code} • {i.title.slice(0, 26)}...
              </option>
            ))}
          </select>
        </div>

        <button className="rg-btn rg-btn-outline" onClick={fetchTasks}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="rg-alert-banner" style={{ backgroundColor: '#751a1a', color: '#f87171', marginBottom: '16px' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Task Dispatch Board Table */}
      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Task Dispatch Board</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            RECORDS: {tasks.length}
          </span>
        </div>
        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Querying task dispatch state..." />
          ) : tasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--rg-text-muted)' }}>
              No response tasks found matching your filter criteria.
            </div>
          ) : (
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Linked Incident</th>
                    <th>Mission Directive</th>
                    <th>Priority</th>
                    <th>Assigned Response Unit</th>
                    <th>Status</th>
                    <th>Coordinates</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((t) => (
                    <tr key={t.id}>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px' }}>
                        <span style={{ color: 'var(--rg-blue-subtle)', fontWeight: 600 }}>
                          {t.incident_code || 'INCIDENT'}
                        </span>
                        <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>
                          {t.incident_title ? t.incident_title.slice(0, 24) + '...' : ''}
                        </div>
                      </td>
                      <td>
                        <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{t.title}</div>
                        <div style={{ fontSize: '11px', color: 'var(--rg-text-secondary)', marginTop: '2px' }}>
                          {t.description.length > 80 ? t.description.slice(0, 80) + '...' : t.description}
                        </div>
                      </td>
                      <td>
                        <span className={`rg-pill rg-pill-${PRIORITY_PILLS[t.priority] || 'minor'}`}>
                          {t.priority.toUpperCase()}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '12px' }}>
                        {t.assigned_team_callsign ? (
                          <span style={{ color: 'var(--rg-amber-light)', fontWeight: 600 }}>
                            🛡️ {t.assigned_team_callsign}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--rg-text-muted)', fontStyle: 'italic' }}>Unassigned</span>
                        )}
                      </td>
                      <td>
                        <select
                          className={`rg-pill rg-pill-${STATUS_PILLS[t.status] || 'minor'}`}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            fontSize: '11px',
                            fontWeight: 600,
                          }}
                          value={t.status}
                          onChange={(e) => handleQuickStatusChange(t.id, e.target.value)}
                        >
                          <option value="pending" style={{ background: '#1b2029', color: '#fff' }}>Pending</option>
                          <option value="in_progress" style={{ background: '#1b2029', color: '#fff' }}>In Progress</option>
                          <option value="completed" style={{ background: '#1b2029', color: '#fff' }}>Completed</option>
                          <option value="cancelled" style={{ background: '#1b2029', color: '#fff' }}>Cancelled</option>
                        </select>
                      </td>
                      <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                        {t.target_latitude !== null && t.target_longitude !== null
                          ? `${t.target_latitude.toFixed(3)}°, ${t.target_longitude.toFixed(3)}°`
                          : '—'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {t.status !== 'completed' && (
                            <button
                              className="rg-btn rg-btn-outline"
                              style={{ padding: '3px 8px', fontSize: '11px', color: 'var(--rg-olive-light)', borderColor: 'var(--rg-olive-base)' }}
                              onClick={() => handleCompleteTask(t.id)}
                            >
                              ✓ Complete
                            </button>
                          )}
                          <button
                            className="rg-btn rg-btn-outline"
                            style={{ padding: '3px 8px', fontSize: '11px' }}
                            onClick={() => openEditModal(t)}
                          >
                            Edit
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

      {/* Dispatch / Edit Task Modal */}
      {createModal && (
        <ModalDialog
          title={editTask ? `Edit Mission Task: ${editTask.title.slice(0, 30)}...` : 'Dispatch New Mission Task'}
          onClose={() => setCreateModal(false)}
        >
          <form onSubmit={handleSaveTask}>
            {actionError && (
              <div style={{ backgroundColor: 'var(--rg-red-muted)', color: 'var(--rg-red-light)', padding: '8px 12px', borderRadius: '4px', marginBottom: '14px', fontSize: '12px' }}>
                ⚠️ {actionError}
              </div>
            )}

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Associated Incident *
              </label>
              <select
                required
                className="rg-input"
                style={{ width: '100%' }}
                value={formData.incident_id}
                onChange={(e) => setFormData({ ...formData, incident_id: e.target.value })}
                disabled={Boolean(editTask)}
              >
                <option value="">Select an active incident...</option>
                {incidents.map((i) => (
                  <option key={i.id} value={i.id}>
                    [{i.incident_code}] {i.title} ({i.category})
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Task Headline / Mission Title *
              </label>
              <input
                type="text"
                required
                className="rg-input"
                style={{ width: '100%' }}
                placeholder="e.g. Deploy 6 Inflatable Rescue Boats to Low-Lands"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              />
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Operational Directives & Description *
              </label>
              <textarea
                required
                rows={3}
                className="rg-input"
                style={{ width: '100%', resize: 'vertical' }}
                placeholder="Detailed field directives, staging instructions, and objectives..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Mission Priority
                </label>
                <select
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Assign Response Unit
                </label>
                <select
                  className="rg-input"
                  style={{ width: '100%' }}
                  value={formData.assigned_team_id}
                  onChange={(e) => setFormData({ ...formData, assigned_team_id: e.target.value })}
                >
                  <option value="">None (Unassigned / Pending)</option>
                  {teams.map((tm) => (
                    <option key={tm.id} value={tm.id}>
                      {tm.team_callsign} ({tm.unit_type}) — [{tm.current_status}]
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '18px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Target Latitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. 26.185"
                  value={formData.target_latitude}
                  onChange={(e) => setFormData({ ...formData, target_latitude: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Target Longitude (Optional)
                </label>
                <input
                  type="number"
                  step="any"
                  className="rg-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. 91.748"
                  value={formData.target_longitude}
                  onChange={(e) => setFormData({ ...formData, target_longitude: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button type="button" className="rg-btn rg-btn-outline" onClick={() => setCreateModal(false)}>
                Cancel
              </button>
              <button type="submit" className="rg-btn rg-btn-primary">
                {editTask ? 'Save Modifications' : 'Dispatch Task'}
              </button>
            </div>
          </form>
        </ModalDialog>
      )}
    </>
  );
}
