import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, EmptyState, LoadingState, ErrorState, ModalDialog } from './StateComponents';

const CATEGORIES = [
  { id: 'all', label: 'All Hazards' },
  { id: 'flood', label: 'Flood' },
  { id: 'severe_weather', label: 'Severe Weather' },
  { id: 'wildfire', label: 'Wildfire' },
  { id: 'earthquake', label: 'Earthquake' },
  { id: 'landslide', label: 'Landslide' },
  { id: 'industrial_accident', label: 'Industrial' },
  { id: 'other', label: 'Other' },
];

const SEVERITIES = [
  { id: 'all', label: 'All Severities' },
  { id: 'critical', label: 'Critical' },
  { id: 'high', label: 'High' },
  { id: 'medium', label: 'Medium' },
  { id: 'low', label: 'Low' },
];

const STATUSES = [
  { id: 'all', label: 'All Statuses' },
  { id: 'reported', label: 'Reported' },
  { id: 'under_assessment', label: 'Under Assessment' },
  { id: 'confirmed', label: 'Confirmed' },
  { id: 'response_active', label: 'Response Active' },
  { id: 'contained', label: 'Contained' },
  { id: 'resolved', label: 'Resolved' },
  { id: 'closed', label: 'Closed' },
];

const DEFAULT_DEV_HEADERS = {
  'Content-Type': 'application/json',
  'X-Rakshagrid-Dev-Role': 'operator',
  'X-Rakshagrid-Dev-User': 'operator-ops-01',
};

const ADMIN_DEV_HEADERS = {
  'Content-Type': 'application/json',
  'X-Rakshagrid-Dev-Role': 'admin',
  'X-Rakshagrid-Dev-User': 'admin-chief-01',
};

export default function RakshaIncidents() {
  // Incident collection state
  const [incidents, setIncidents] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSeverity, setSelectedSeverity] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Modals & Active State
  const [activeModalIncident, setActiveModalIncident] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'timeline' | 'edit'
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [confirmSeedOpen, setConfirmSeedOpen] = useState(false);

  // Timeline updates inside Detail Modal
  const [timelineUpdates, setTimelineUpdates] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [sitrepText, setSitrepText] = useState('');
  const [sitrepType, setSitrepType] = useState('situation_report');
  const [sitrepSubmitting, setSitrepSubmitting] = useState(false);

  // Edit / Status transition form state
  const [editForm, setEditForm] = useState({
    title: '',
    description: '',
    status: '',
    severity: '',
    category: '',
    location_description: '',
    assigned_commander: '',
    affected_population: '',
    update_note: '',
  });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState(null);

  // Create form state
  const [createForm, setCreateForm] = useState({
    title: '',
    description: '',
    category: 'flood',
    severity: 'medium',
    status: 'reported',
    location_description: '',
    latitude: '',
    longitude: '',
    affected_population: '0',
    verification_status: 'unverified',
    source_type: 'operator_report',
    assigned_commander: '',
  });
  const [createErrors, setCreateErrors] = useState({});
  const [createSubmitting, setCreateSubmitting] = useState(false);

  // Notifications
  const [toast, setToast] = useState(null);

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => {
      setToast(null);
    }, 5000);
  };

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Query PostgreSQL API
  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (selectedSeverity !== 'all') params.append('severity', selectedSeverity);
      if (selectedStatus !== 'all') params.append('status', selectedStatus);
      if (debouncedSearch) params.append('search', debouncedSearch);

      const res = await fetch(`/api/v1/incidents?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setIncidents(data.items || []);
      setTotalCount(data.total_count || 0);
      setTotalPages(data.total_pages || 1);
    } catch (e) {
      console.error('Failed to query incidents from PostgreSQL backend:', e);
      setError(e.message || 'Unable to establish database connection with incident services.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, selectedCategory, selectedSeverity, selectedStatus, debouncedSearch]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  // Fetch timeline updates for an incident
  const fetchTimeline = useCallback(async (incidentId) => {
    setTimelineLoading(true);
    try {
      const res = await fetch(`/api/v1/incidents/${incidentId}/updates`);
      if (res.ok) {
        const data = await res.json();
        setTimelineUpdates(data || []);
      }
    } catch (e) {
      console.error('Failed to fetch timeline:', e);
    } finally {
      setTimelineLoading(false);
    }
  }, []);

  const openIncidentDetails = (incident) => {
    setActiveModalIncident(incident);
    setActiveTab('overview');
    setEditError(null);
    setEditForm({
      title: incident.title || '',
      description: incident.description || '',
      status: incident.status || 'reported',
      severity: incident.severity || 'medium',
      category: incident.category || 'other',
      location_description: incident.location_description || '',
      assigned_commander: incident.assigned_commander || '',
      affected_population: incident.affected_population != null ? String(incident.affected_population) : '0',
      update_note: '',
    });
    fetchTimeline(incident.id);
  };

  // Submit new timeline sitrep update
  const handleAddSitrep = async (e) => {
    e.preventDefault();
    if (!sitrepText.trim() || !activeModalIncident) return;
    setSitrepSubmitting(true);
    try {
      const res = await fetch(`/api/v1/incidents/${activeModalIncident.id}/updates`, {
        method: 'POST',
        headers: DEFAULT_DEV_HEADERS,
        body: JSON.stringify({
          update_message: sitrepText.trim(),
          update_type: sitrepType,
          metadata_payload: { client: 'RakshaGrid-Web', logged_via: 'tactical_console' },
        }),
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }
      setSitrepText('');
      showToast('success', 'Situation report appended to incident timeline.');
      await fetchTimeline(activeModalIncident.id);
    } catch (err) {
      showToast('error', `Failed to log situation report: ${err.message}`);
    } finally {
      setSitrepSubmitting(false);
    }
  };

  // Submit incident edit / status transition
  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!activeModalIncident) return;
    setEditSaving(true);
    setEditError(null);

    const payload = {};
    if (editForm.title !== activeModalIncident.title) payload.title = editForm.title.trim();
    if (editForm.description !== activeModalIncident.description) payload.description = editForm.description.trim();
    if (editForm.status !== activeModalIncident.status) payload.status = editForm.status;
    if (editForm.severity !== activeModalIncident.severity) payload.severity = editForm.severity;
    if (editForm.category !== activeModalIncident.category) payload.category = editForm.category;
    if (editForm.location_description !== activeModalIncident.location_description) {
      payload.location_description = editForm.location_description.trim();
    }
    if (editForm.assigned_commander !== (activeModalIncident.assigned_commander || '')) {
      payload.assigned_commander = editForm.assigned_commander.trim();
    }
    const pop = parseInt(editForm.affected_population, 10);
    if (!isNaN(pop) && pop !== activeModalIncident.affected_population) {
      payload.affected_population = pop;
    }
    if (editForm.update_note?.trim()) {
      payload.update_note = editForm.update_note.trim();
    }

    try {
      const res = await fetch(`/api/v1/incidents/${activeModalIncident.id}`, {
        method: 'PATCH',
        headers: DEFAULT_DEV_HEADERS,
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const updated = await res.json();
      setActiveModalIncident(updated);
      showToast('success', `Incident ${updated.incident_code || updated.title} updated successfully.`);
      await fetchTimeline(updated.id);
      await fetchIncidents();
      setActiveTab('overview');
    } catch (err) {
      setEditError(err.message);
    } finally {
      setEditSaving(false);
    }
  };

  // Validate Create Incident Form
  const validateCreateForm = () => {
    const errors = {};
    if (!createForm.title || createForm.title.trim().length < 5) {
      errors.title = 'Title must contain at least 5 characters.';
    }
    if (createForm.latitude !== '') {
      const lat = parseFloat(createForm.latitude);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        errors.latitude = 'Latitude must be between -90 and 90.';
      }
    }
    if (createForm.longitude !== '') {
      const lon = parseFloat(createForm.longitude);
      if (isNaN(lon) || lon < -180 || lon > 180) {
        errors.longitude = 'Longitude must be between -180 and 180.';
      }
    }
    if (createForm.affected_population !== '') {
      const pop = parseInt(createForm.affected_population, 10);
      if (isNaN(pop) || pop < 0) {
        errors.affected_population = 'Affected population cannot be negative.';
      }
    }
    setCreateErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Submit Create Incident
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!validateCreateForm()) return;
    setCreateSubmitting(true);

    const payload = {
      title: createForm.title.trim(),
      description: createForm.description.trim() || undefined,
      category: createForm.category,
      severity: createForm.severity,
      status: createForm.status,
      location_description: createForm.location_description.trim() || undefined,
      verification_status: createForm.verification_status,
      source_type: createForm.source_type,
      assigned_commander: createForm.assigned_commander.trim() || undefined,
    };

    if (createForm.latitude !== '') payload.latitude = parseFloat(createForm.latitude);
    if (createForm.longitude !== '') payload.longitude = parseFloat(createForm.longitude);
    if (createForm.affected_population !== '') payload.affected_population = parseInt(createForm.affected_population, 10);

    try {
      const res = await fetch('/api/v1/incidents', {
        method: 'POST',
        headers: DEFAULT_DEV_HEADERS,
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      const created = await res.json();
      showToast('success', `Incident '${created.title}' (${created.incident_code}) logged and persisted to database.`);
      setCreateModalOpen(false);
      setCreateForm({
        title: '',
        description: '',
        category: 'flood',
        severity: 'medium',
        status: 'reported',
        location_description: '',
        latitude: '',
        longitude: '',
        affected_population: '0',
        verification_status: 'unverified',
        source_type: 'operator_report',
        assigned_commander: '',
      });
      setCreateErrors({});
      await fetchIncidents();
    } catch (err) {
      showToast('error', `Failed to log incident: ${err.message}`);
    } finally {
      setCreateSubmitting(false);
    }
  };

  // Consequential Action: Archive or Close Incident
  const handleExecuteArchive = async (incidentId) => {
    try {
      const res = await fetch(`/api/v1/incidents/${incidentId}`, {
        method: 'DELETE',
        headers: ADMIN_DEV_HEADERS,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }

      showToast('success', 'Incident record archived and status set to closed.');
      setConfirmDeleteId(null);
      if (activeModalIncident?.id === incidentId) {
        setActiveModalIncident(null);
      }
      await fetchIncidents();
    } catch (err) {
      showToast('error', `Archive action failed: ${err.message}`);
    }
  };

  // Seed Dev Data
  const handleSeedDevData = async () => {
    try {
      const res = await fetch('/api/v1/incidents/seed', {
        method: 'POST',
        headers: ADMIN_DEV_HEADERS,
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}`);
      }
      const seeded = await res.json();
      showToast('success', `Database seeded: ${seeded.seeded_count} simulated incident records loaded.`);
      setConfirmSeedOpen(false);
      await fetchIncidents();
    } catch (err) {
      showToast('error', `Dev seed failed: ${err.message}`);
    }
  };

  return (
    <>
      <DemoNoticeBanner text="Disaster Incident Registry: Operating on persistent PostgreSQL schema with versioned Alembic migrations. All mutations are transactionally recorded in incident_updates history." />

      {toast && (
        <div className={`rg-toast ${toast.type === 'success' ? 'rg-toast-success' : 'rg-toast-error'}`}>
          <span>{toast.message}</span>
          <button
            onClick={() => setToast(null)}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 'bold' }}
          >
            ✕
          </button>
        </div>
      )}

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Disaster Incident Registry</h2>
          <p>PostgreSQL-backed operational incident intake, audit trail, and multi-agency triage</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-outline" onClick={() => setConfirmSeedOpen(true)}>
            Seed Dev Records
          </button>
          <button className="rg-btn rg-btn-primary" onClick={() => setCreateModalOpen(true)}>
            + Log Incident
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rg-panel">
        <div className="rg-filter-bar">
          <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase', fontFamily: 'var(--rg-font-mono)' }}>
            Hazard:
          </span>
          <select
            className="rg-form-control"
            style={{ width: 'auto', padding: '4px 8px', fontSize: '12px' }}
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
          >
            {CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>

          <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase', fontFamily: 'var(--rg-font-mono)', marginLeft: '8px' }}>
            Severity:
          </span>
          <select
            className="rg-form-control"
            style={{ width: 'auto', padding: '4px 8px', fontSize: '12px' }}
            value={selectedSeverity}
            onChange={(e) => {
              setSelectedSeverity(e.target.value);
              setPage(1);
            }}
          >
            {SEVERITIES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>

          <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)', textTransform: 'uppercase', fontFamily: 'var(--rg-font-mono)', marginLeft: '8px' }}>
            Status:
          </span>
          <select
            className="rg-form-control"
            style={{ width: 'auto', padding: '4px 8px', fontSize: '12px' }}
            value={selectedStatus}
            onChange={(e) => {
              setSelectedStatus(e.target.value);
              setPage(1);
            }}
          >
            {STATUSES.map((st) => (
              <option key={st.id} value={st.id}>
                {st.label}
              </option>
            ))}
          </select>

          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="text"
              placeholder="Search title, code, region..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="rg-form-control"
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                width: '210px',
              }}
            />
          </div>
        </div>

        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <LoadingState message="Synchronizing with PostgreSQL incident repository..." />
          ) : error ? (
            <ErrorState
              title="Database Connection Unavailable"
              message={error}
              onRetry={fetchIncidents}
            />
          ) : incidents.length === 0 ? (
            <EmptyState
              title="No Incidents Located"
              description="No database records match the selected operational filters. Adjust criteria or seed development records."
            />
          ) : (
            <>
              <div className="rg-table-wrapper">
                <table className="rg-table">
                  <thead>
                    <tr>
                      <th>Incident Code</th>
                      <th>Title & Location</th>
                      <th>Category</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Coordinates</th>
                      <th>Affected Pop.</th>
                      <th>Reported At</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.map((i) => (
                      <tr key={i.id}>
                        <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>
                          <div>{i.incident_code || 'RG-INC'}</div>
                          {i.source_type === 'simulation' && (
                            <span className="rg-pill rg-pill-simulation" style={{ fontSize: '9px', marginTop: '2px' }}>
                              SIMULATION
                            </span>
                          )}
                        </td>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{i.title}</div>
                          <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                            {i.location_description || i.location_name || 'Unspecified Sector'}
                          </div>
                        </td>
                        <td>
                          <span style={{ textTransform: 'capitalize', fontSize: '11px', fontFamily: 'var(--rg-font-mono)' }}>
                            {i.category.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <span className={`rg-pill rg-pill-${i.severity}`}>{i.severity}</span>
                        </td>
                        <td>
                          <span className={`rg-pill rg-pill-${i.status}`}>{i.status.replace('_', ' ')}</span>
                        </td>
                        <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px' }}>
                          {i.latitude != null && i.longitude != null
                            ? `${Number(i.latitude).toFixed(3)}°, ${Number(i.longitude).toFixed(3)}°`
                            : '—'}
                        </td>
                        <td style={{ fontFamily: 'var(--rg-font-mono)' }}>
                          {i.affected_population != null ? Number(i.affected_population).toLocaleString() : '—'}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                          {new Date(i.reported_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                        </td>
                        <td>
                          <button
                            className="rg-btn rg-btn-outline rg-btn-sm"
                            onClick={() => openIncidentDetails(i)}
                          >
                            Manage
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination controls */}
              <div className="rg-pagination">
                <div className="rg-pagination-info">
                  Showing page {page} of {totalPages} ({totalCount} total incidents recorded)
                </div>
                <div className="rg-pagination-controls">
                  <select
                    className="rg-form-control"
                    style={{ width: 'auto', padding: '2px 6px', fontSize: '11px' }}
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                  >
                    <option value={10}>10 / page</option>
                    <option value={20}>20 / page</option>
                    <option value={50}>50 / page</option>
                  </select>
                  <button
                    className="rg-pagination-btn"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    ← Previous
                  </button>
                  <button
                    className="rg-pagination-btn"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    Next →
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Incident Detail / Timeline / Edit Modal */}
      <ModalDialog
        isOpen={Boolean(activeModalIncident)}
        onClose={() => setActiveModalIncident(null)}
        title={activeModalIncident ? `${activeModalIncident.incident_code || 'RG-INC'} — ${activeModalIncident.title}` : ''}
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              className="rg-btn rg-btn-danger rg-btn-sm"
              onClick={() => setConfirmDeleteId(activeModalIncident.id)}
            >
              Archive Incident
            </button>
            <button className="rg-btn rg-btn-outline rg-btn-sm" onClick={() => setActiveModalIncident(null)}>
              Close
            </button>
          </div>
        }
      >
        {activeModalIncident && (
          <div>
            {/* Modal Navigation Tabs */}
            <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--rg-border-subtle)', marginBottom: '14px', paddingBottom: '8px' }}>
              <button
                className={`rg-filter-chip ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                Overview
              </button>
              <button
                className={`rg-filter-chip ${activeTab === 'timeline' ? 'active' : ''}`}
                onClick={() => setActiveTab('timeline')}
              >
                Timeline & History ({timelineUpdates.length})
              </button>
              <button
                className={`rg-filter-chip ${activeTab === 'edit' ? 'active' : ''}`}
                onClick={() => setActiveTab('edit')}
              >
                Modify / Transition Status
              </button>
            </div>

            {/* TAB 1: OVERVIEW */}
            {activeTab === 'overview' && (
              <div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
                  <span className={`rg-pill rg-pill-${activeModalIncident.severity}`}>{activeModalIncident.severity}</span>
                  <span className={`rg-pill rg-pill-${activeModalIncident.status}`}>
                    {activeModalIncident.status.replace('_', ' ')}
                  </span>
                  <span className="rg-pill rg-pill-minor">{activeModalIncident.category.replace('_', ' ')}</span>
                  <span className="rg-pill rg-pill-minor">
                    Verification: {activeModalIncident.verification_status}
                  </span>
                  {activeModalIncident.source_type === 'simulation' && (
                    <span className="rg-pill rg-pill-simulation">SIMULATION RECORD</span>
                  )}
                </div>

                <p style={{ color: 'var(--rg-text-secondary)', marginBottom: '16px', lineHeight: '1.6' }}>
                  {activeModalIncident.description || 'No detailed incident description filed.'}
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', backgroundColor: 'var(--rg-bg-card)', padding: '14px', borderRadius: '4px' }}>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>LOCATION</div>
                    <div style={{ fontWeight: 600 }}>{activeModalIncident.location_description || activeModalIncident.location_name || 'Unspecified'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>COORDINATES</div>
                    <div style={{ fontFamily: 'var(--rg-font-mono)' }}>
                      {activeModalIncident.latitude != null && activeModalIncident.longitude != null
                        ? `${activeModalIncident.latitude}° N, ${activeModalIncident.longitude}° E`
                        : 'Not GPS Tagged'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>AFFECTED POPULATION</div>
                    <div style={{ fontWeight: 700 }}>
                      {activeModalIncident.affected_population != null ? Number(activeModalIncident.affected_population).toLocaleString() : '0'} Persons
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>ASSIGNED COMMANDER</div>
                    <div>{activeModalIncident.assigned_commander || 'Unassigned (General Triage)'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>REPORTED TIMESTAMP</div>
                    <div style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)' }}>
                      {new Date(activeModalIncident.reported_at).toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>DATABASE RECORD ID</div>
                    <div style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                      {activeModalIncident.id}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: TIMELINE & AUDIT HISTORY */}
            {activeTab === 'timeline' && (
              <div>
                <form onSubmit={handleAddSitrep} style={{ marginBottom: '16px', backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: '4px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--rg-text-secondary)', marginBottom: '8px', textTransform: 'uppercase', fontFamily: 'var(--rg-font-mono)' }}>
                    Add Situation Report / Update
                  </div>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                    <select
                      className="rg-form-control"
                      style={{ width: '180px' }}
                      value={sitrepType}
                      onChange={(e) => setSitrepType(e.target.value)}
                    >
                      <option value="situation_report">Situation Report</option>
                      <option value="operator_note">Operator Note</option>
                      <option value="operational_dispatch">Operational Dispatch</option>
                      <option value="status_change">Manual Audit Tag</option>
                    </select>
                    <input
                      type="text"
                      className="rg-form-control"
                      placeholder="Enter operational sitrep or telemetry update..."
                      value={sitrepText}
                      onChange={(e) => setSitrepText(e.target.value)}
                      required
                    />
                    <button type="submit" className="rg-btn rg-btn-primary" disabled={sitrepSubmitting}>
                      {sitrepSubmitting ? 'Posting...' : 'Post Sitrep'}
                    </button>
                  </div>
                </form>

                {timelineLoading ? (
                  <LoadingState message="Fetching chronological timeline..." />
                ) : timelineUpdates.length === 0 ? (
                  <div style={{ color: 'var(--rg-text-muted)', padding: '12px', textAlign: 'center' }}>
                    No audit records logged for this incident yet.
                  </div>
                ) : (
                  <div className="rg-timeline">
                    {timelineUpdates.map((item) => (
                      <div key={item.id} className="rg-timeline-item">
                        <div className={`rg-timeline-dot ${item.update_type === 'status_change' ? 'transition' : ''}`} />
                        <div className="rg-timeline-content">
                          <div className="rg-timeline-header">
                            <div>
                              <span className="rg-timeline-actor">{item.actor_id || 'System'}</span>
                              <span className="rg-pill rg-pill-minor" style={{ marginLeft: '6px', fontSize: '9px' }}>
                                {item.update_type}
                              </span>
                              {item.previous_status && item.new_status && (
                                <span style={{ marginLeft: '6px', fontSize: '10px', fontFamily: 'var(--rg-font-mono)' }}>
                                  ({item.previous_status} → <strong>{item.new_status}</strong>)
                                </span>
                              )}
                            </div>
                            <span className="rg-timeline-time">
                              {new Date(item.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                            </span>
                          </div>
                          <div className="rg-timeline-message">{item.update_message}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: EDIT & STATUS TRANSITION */}
            {activeTab === 'edit' && (
              <form onSubmit={handleSaveEdit}>
                {editError && (
                  <div className="rg-toast rg-toast-error" style={{ marginBottom: '12px' }}>
                    <span>{editError}</span>
                  </div>
                )}

                <div className="rg-form-grid">
                  <div className="rg-form-group full-width">
                    <label className="rg-form-label">Incident Title</label>
                    <input
                      type="text"
                      className="rg-form-control"
                      value={editForm.title}
                      onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                      required
                    />
                  </div>

                  <div className="rg-form-group">
                    <label className="rg-form-label">Status Progression</label>
                    <select
                      className="rg-form-control"
                      value={editForm.status}
                      onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    >
                      <option value="reported">Reported</option>
                      <option value="under_assessment">Under Assessment</option>
                      <option value="confirmed">Confirmed</option>
                      <option value="response_active">Response Active</option>
                      <option value="contained">Contained</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </select>
                    <div className="rg-form-hint">Enforces state machine progression.</div>
                  </div>

                  <div className="rg-form-group">
                    <label className="rg-form-label">Severity Level</label>
                    <select
                      className="rg-form-control"
                      value={editForm.severity}
                      onChange={(e) => setEditForm({ ...editForm, severity: e.target.value })}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>

                  <div className="rg-form-group">
                    <label className="rg-form-label">Category / Hazard</label>
                    <select
                      className="rg-form-control"
                      value={editForm.category}
                      onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                    >
                      <option value="flood">Flood</option>
                      <option value="severe_weather">Severe Weather</option>
                      <option value="wildfire">Wildfire</option>
                      <option value="earthquake">Earthquake</option>
                      <option value="landslide">Landslide</option>
                      <option value="industrial_accident">Industrial Accident</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="rg-form-group">
                    <label className="rg-form-label">Affected Population Estimate</label>
                    <input
                      type="number"
                      min="0"
                      className="rg-form-control"
                      value={editForm.affected_population}
                      onChange={(e) => setEditForm({ ...editForm, affected_population: e.target.value })}
                    />
                  </div>

                  <div className="rg-form-group full-width">
                    <label className="rg-form-label">Location Description</label>
                    <input
                      type="text"
                      className="rg-form-control"
                      value={editForm.location_description}
                      onChange={(e) => setEditForm({ ...editForm, location_description: e.target.value })}
                    />
                  </div>

                  <div className="rg-form-group full-width">
                    <label className="rg-form-label">Assigned Commander</label>
                    <input
                      type="text"
                      className="rg-form-control"
                      placeholder="e.g. CDR-SHARMA-NDRF"
                      value={editForm.assigned_commander}
                      onChange={(e) => setEditForm({ ...editForm, assigned_commander: e.target.value })}
                    />
                  </div>

                  <div className="rg-form-group full-width">
                    <label className="rg-form-label">Detailed Situation Overview</label>
                    <textarea
                      className="rg-form-control"
                      value={editForm.description}
                      onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    />
                  </div>

                  <div className="rg-form-group full-width">
                    <label className="rg-form-label">Audit Note for History Record</label>
                    <input
                      type="text"
                      className="rg-form-control"
                      placeholder="Reason for modification or status transition..."
                      value={editForm.update_note}
                      onChange={(e) => setEditForm({ ...editForm, update_note: e.target.value })}
                    />
                  </div>
                </div>

                <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <button type="button" className="rg-btn rg-btn-outline" onClick={() => setActiveTab('overview')}>
                    Cancel
                  </button>
                  <button type="submit" className="rg-btn rg-btn-primary" disabled={editSaving}>
                    {editSaving ? 'Committing Changes...' : 'Save & Record Audit'}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </ModalDialog>

      {/* CREATE INCIDENT MODAL */}
      <ModalDialog
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Log New Disaster Incident"
        actions={null}
      >
        <form onSubmit={handleCreateSubmit}>
          <div className="rg-form-grid">
            <div className="rg-form-group full-width">
              <label className="rg-form-label">
                Incident Title <span className="required">*</span>
              </label>
              <input
                type="text"
                className={`rg-form-control ${createErrors.title ? 'error' : ''}`}
                placeholder="e.g. Severe Riverine Inundation in Srinagar Ward 4"
                value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                required
              />
              {createErrors.title && <div className="rg-form-error">{createErrors.title}</div>}
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Hazard Category</label>
              <select
                className="rg-form-control"
                value={createForm.category}
                onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
              >
                <option value="flood">Flood</option>
                <option value="severe_weather">Severe Weather</option>
                <option value="wildfire">Wildfire</option>
                <option value="earthquake">Earthquake</option>
                <option value="landslide">Landslide</option>
                <option value="industrial_accident">Industrial Accident</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Severity Level</label>
              <select
                className="rg-form-control"
                value={createForm.severity}
                onChange={(e) => setCreateForm({ ...createForm, severity: e.target.value })}
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Initial Status</label>
              <select
                className="rg-form-control"
                value={createForm.status}
                onChange={(e) => setCreateForm({ ...createForm, status: e.target.value })}
              >
                <option value="reported">Reported</option>
                <option value="under_assessment">Under Assessment</option>
                <option value="confirmed">Confirmed</option>
                <option value="response_active">Response Active</option>
              </select>
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Verification Status</label>
              <select
                className="rg-form-control"
                value={createForm.verification_status}
                onChange={(e) => setCreateForm({ ...createForm, verification_status: e.target.value })}
              >
                <option value="unverified">Unverified</option>
                <option value="under_review">Under Review</option>
                <option value="verified">Verified</option>
              </select>
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Latitude (-90 to 90)</label>
              <input
                type="number"
                step="any"
                className={`rg-form-control ${createErrors.latitude ? 'error' : ''}`}
                placeholder="e.g. 34.0837"
                value={createForm.latitude}
                onChange={(e) => setCreateForm({ ...createForm, latitude: e.target.value })}
              />
              {createErrors.latitude && <div className="rg-form-error">{createErrors.latitude}</div>}
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Longitude (-180 to 180)</label>
              <input
                type="number"
                step="any"
                className={`rg-form-control ${createErrors.longitude ? 'error' : ''}`}
                placeholder="e.g. 74.7973"
                value={createForm.longitude}
                onChange={(e) => setCreateForm({ ...createForm, longitude: e.target.value })}
              />
              {createErrors.longitude && <div className="rg-form-error">{createErrors.longitude}</div>}
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Affected Population Estimate</label>
              <input
                type="number"
                min="0"
                className={`rg-form-control ${createErrors.affected_population ? 'error' : ''}`}
                value={createForm.affected_population}
                onChange={(e) => setCreateForm({ ...createForm, affected_population: e.target.value })}
              />
              {createErrors.affected_population && (
                <div className="rg-form-error">{createErrors.affected_population}</div>
              )}
            </div>

            <div className="rg-form-group">
              <label className="rg-form-label">Source Type</label>
              <select
                className="rg-form-control"
                value={createForm.source_type}
                onChange={(e) => setCreateForm({ ...createForm, source_type: e.target.value })}
              >
                <option value="operator_report">Operator Report</option>
                <option value="external_source">External Emergency Feeds</option>
                <option value="simulation">Simulation / Drill Record</option>
              </select>
            </div>

            <div className="rg-form-group full-width">
              <label className="rg-form-label">Location / Sector Description</label>
              <input
                type="text"
                className="rg-form-control"
                placeholder="e.g. Sector 4, Rajbagh Bridge Perimeter, Srinagar"
                value={createForm.location_description}
                onChange={(e) => setCreateForm({ ...createForm, location_description: e.target.value })}
              />
            </div>

            <div className="rg-form-group full-width">
              <label className="rg-form-label">Assigned Commander</label>
              <input
                type="text"
                className="rg-form-control"
                placeholder="e.g. CDR-VERMA-NDRF-04"
                value={createForm.assigned_commander}
                onChange={(e) => setCreateForm({ ...createForm, assigned_commander: e.target.value })}
              />
            </div>

            <div className="rg-form-group full-width">
              <label className="rg-form-label">Detailed Situation Overview</label>
              <textarea
                className="rg-form-control"
                placeholder="Initial assessment of hazards, river levels, structural integrity, and evacuation status..."
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              />
            </div>
          </div>

          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <button
              type="button"
              className="rg-btn rg-btn-outline"
              onClick={() => setCreateModalOpen(false)}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rg-btn rg-btn-primary"
              disabled={createSubmitting}
            >
              {createSubmitting ? 'Logging to PostgreSQL...' : 'Persist Incident'}
            </button>
          </div>
        </form>
      </ModalDialog>

      {/* CONFIRM CONVENTIONAL ARCHIVE DIALOG */}
      <ModalDialog
        isOpen={Boolean(confirmDeleteId)}
        onClose={() => setConfirmDeleteId(null)}
        title="Confirm Operational Archive"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="rg-btn rg-btn-outline" onClick={() => setConfirmDeleteId(null)}>
              Cancel
            </button>
            <button
              className="rg-btn rg-btn-danger"
              onClick={() => handleExecuteArchive(confirmDeleteId)}
            >
              Confirm Archive & Close
            </button>
          </div>
        }
      >
        <div>
          <p style={{ color: 'var(--rg-text-secondary)', marginBottom: '10px' }}>
            Are you sure you want to archive and close this incident?
          </p>
          <div style={{ fontSize: '12px', color: 'var(--rg-amber-light)', backgroundColor: 'var(--rg-bg-card)', padding: '10px', borderRadius: '4px' }}>
            Operational integrity rule: Records are permanently preserved in the PostgreSQL audit log with status <code>closed</code> and historical timeline entries remain immutable.
          </div>
        </div>
      </ModalDialog>

      {/* CONFIRM SEED DEV DATA DIALOG */}
      <ModalDialog
        isOpen={confirmSeedOpen}
        onClose={() => setConfirmSeedOpen(false)}
        title="Seed Fictional Development Incidents"
        actions={
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="rg-btn rg-btn-outline" onClick={() => setConfirmSeedOpen(false)}>
              Cancel
            </button>
            <button className="rg-btn rg-btn-primary" onClick={handleSeedDevData}>
              Seed 5 Simulated Records
            </button>
          </div>
        }
      >
        <div>
          <p style={{ color: 'var(--rg-text-secondary)', marginBottom: '10px' }}>
            This action inserts 5 deterministic, clearly labeled fictional incident records into the PostgreSQL database.
          </p>
          <div style={{ fontSize: '12px', color: 'var(--rg-olive-light)', backgroundColor: 'var(--rg-bg-card)', padding: '10px', borderRadius: '4px' }}>
            All seeded records are tagged with <code>source_type: simulation</code> to ensure clear segregation from operational records. Existing seed codes will be safely skipped.
          </div>
        </div>
      </ModalDialog>
    </>
  );
}
