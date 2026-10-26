import React, { useState, useEffect, useCallback } from 'react';
import { LoadingState, ModalDialog } from './StateComponents';

const CATEGORIES = [
  'Medical',
  'Food & Water',
  'Rescue Equipment',
  'Power & Fuel',
  'Shelter Gear',
  'Communication',
  'Vehicles',
  'Other',
];

const TRANSPORT_MODES = [
  'Road Convoy',
  'Helicopter Airlift',
  'River Craft / Boat',
  'All-Terrain Vehicle',
  'Hand Carry',
  'Commercial Freight',
];

export default function RakshaResources() {
  const [resources, setResources] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Operational Context (for linking allocations)
  const [incidents, setIncidents] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [teams, setTeams] = useState([]);
  const [shelters, setShelters] = useState([]);

  // Filters
  const [categoryFilter, setCategoryFilter] = useState('');
  const [lowStockFilter, setLowStockFilter] = useState(false);
  const [search, setSearch] = useState('');

  // Modals
  const [createModal, setCreateModal] = useState(false);
  const [editResource, setEditResource] = useState(null);
  const [allocateResource, setAllocateResource] = useState(null);
  const [returnResource, setReturnResource] = useState(null);
  const [auditResource, setAuditResource] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [actionSuccess, setActionSuccess] = useState(null);

  // Forms
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    category: 'Medical',
    quantity_total: 100,
    quantity_available: 100,
    unit: 'units',
    storage_location: '',
    shelter_id: '',
    status: 'Adequate',
  });

  const [allocateForm, setAllocateForm] = useState({
    quantity: 1,
    destination: '',
    transport_mode: 'Road Convoy',
    incident_id: '',
    task_id: '',
    team_id: '',
    shelter_id: '',
    notes: '',
  });

  const [returnForm, setReturnForm] = useState({
    quantity: 1,
    source_location: '',
    notes: '',
  });

  // Fetch Resources
  const fetchResources = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (lowStockFilter) params.append('low_stock_only', 'true');
      if (search) params.append('search', search);

      const res = await fetch(`/api/v1/resources?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch resources`);
      const data = await res.json();
      setResources(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Resources fetch error:', err);
      setError(err.message || 'Failed to query emergency resources.');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, lowStockFilter, search]);

  // Fetch context entities for relational linking
  const fetchContextEntities = useCallback(async () => {
    try {
      const [incRes, taskRes, teamRes, sheltRes] = await Promise.all([
        fetch('/api/v1/incidents?page_size=50').catch(() => null),
        fetch('/api/v1/tasks?page_size=50').catch(() => null),
        fetch('/api/v1/teams?page_size=50').catch(() => null),
        fetch('/api/v1/shelters?page_size=50').catch(() => null),
      ]);

      if (incRes && incRes.ok) {
        const d = await incRes.json();
        setIncidents(d.items || []);
      }
      if (taskRes && taskRes.ok) {
        const d = await taskRes.json();
        setTasks(d.items || []);
      }
      if (teamRes && teamRes.ok) {
        const d = await teamRes.json();
        setTeams(d.items || []);
      }
      if (sheltRes && sheltRes.ok) {
        const d = await sheltRes.json();
        setShelters(d.items || []);
      }
    } catch (e) {
      console.warn('Could not prefetch relational context entities:', e);
    }
  }, []);

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  useEffect(() => {
    fetchContextEntities();
  }, [fetchContextEntities]);

  // Flash message helper
  const showFeedback = (msg, isErr = false) => {
    if (isErr) {
      setActionError(msg);
      setActionSuccess(null);
    } else {
      setActionSuccess(msg);
      setActionError(null);
      setTimeout(() => setActionSuccess(null), 4000);
    }
  };

  // Open Create
  const handleOpenCreate = () => {
    const nextNum = Math.floor(10 + Math.random() * 90);
    setFormData({
      code: `RES-LOG-${nextNum}`,
      name: '',
      category: 'Medical',
      quantity_total: 100,
      quantity_available: 100,
      unit: 'units',
      storage_location: 'Central Relief Depot',
      shelter_id: '',
      status: 'Adequate',
    });
    setEditResource(null);
    setActionError(null);
    setCreateModal(true);
  };

  // Open Edit
  const handleOpenEdit = (resItem) => {
    setFormData({
      code: resItem.code,
      name: resItem.name,
      category: resItem.category || 'Medical',
      quantity_total: resItem.quantity_total,
      quantity_available: resItem.quantity_available,
      unit: resItem.unit || 'units',
      storage_location: resItem.storage_location || '',
      shelter_id: resItem.shelter_id || '',
      status: resItem.status || 'Adequate',
    });
    setEditResource(resItem);
    setActionError(null);
    setCreateModal(true);
  };

  // Save (Create or Edit)
  const handleSaveResource = async (e) => {
    e.preventDefault();
    setActionError(null);

    const payload = {
      name: formData.name.trim(),
      category: formData.category,
      quantity_total: parseFloat(formData.quantity_total) || 0,
      quantity_available: parseFloat(formData.quantity_available) || 0,
      unit: formData.unit.trim() || 'units',
      storage_location: formData.storage_location.trim(),
      shelter_id: formData.shelter_id || null,
      status: formData.status,
    };

    if (!editResource) {
      payload.code = formData.code.trim().toUpperCase();
    }

    try {
      const url = editResource ? `/api/v1/resources/${editResource.id}` : '/api/v1/resources';
      const method = editResource ? 'PATCH' : 'POST';

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
      setEditResource(null);
      showFeedback(editResource ? 'Resource stockpile updated successfully.' : 'New emergency resource registered.');
      fetchResources();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Open Allocate Modal
  const handleOpenAllocate = (r) => {
    setAllocateResource(r);
    setAllocateForm({
      quantity: 1,
      destination: r.storage_location ? `Forward Staging ex-${r.storage_location}` : 'Emergency Forward Camp',
      transport_mode: 'Road Convoy',
      incident_id: incidents[0]?.id || '',
      task_id: '',
      team_id: '',
      shelter_id: '',
      notes: `Immediate mission dispatch of ${r.name}`,
    });
    setActionError(null);
  };

  // Execute Allocation
  const handleExecuteAllocate = async (e) => {
    e.preventDefault();
    if (!allocateResource) return;
    setActionError(null);

    const qty = parseFloat(allocateForm.quantity);
    if (!qty || qty <= 0) {
      setActionError('Allocation quantity must be greater than zero.');
      return;
    }
    if (qty > allocateResource.quantity_available) {
      setActionError(`Cannot allocate ${qty} ${allocateResource.unit}. Only ${allocateResource.quantity_available} available.`);
      return;
    }

    const payload = {
      quantity: qty,
      destination: allocateForm.destination.trim(),
      transport_mode: allocateForm.transport_mode,
      incident_id: allocateForm.incident_id || null,
      task_id: allocateForm.task_id || null,
      team_id: allocateForm.team_id || null,
      shelter_id: allocateForm.shelter_id || null,
      notes: allocateForm.notes.trim(),
    };

    try {
      const res = await fetch(`/api/v1/resources/${allocateResource.id}/allocate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Allocation failed (${res.status})`);
      }

      setAllocateResource(null);
      showFeedback(`Successfully dispatched ${qty} ${allocateResource.unit} to ${payload.destination}.`);
      fetchResources();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Open Return Modal
  const handleOpenReturn = (r) => {
    const allocated = r.quantity_allocated || Math.max(0, r.quantity_total - r.quantity_available);
    setReturnResource(r);
    setReturnForm({
      quantity: Math.min(allocated, 1),
      source_location: 'Mission De-escalation Base',
      notes: `Restock return from mission completion`,
    });
    setActionError(null);
  };

  // Execute Return
  const handleExecuteReturn = async (e) => {
    e.preventDefault();
    if (!returnResource) return;
    setActionError(null);

    const qty = parseFloat(returnForm.quantity);
    if (!qty || qty <= 0) {
      setActionError('Return quantity must be greater than zero.');
      return;
    }

    const payload = {
      quantity: qty,
      source_location: returnForm.source_location.trim(),
      notes: returnForm.notes.trim(),
    };

    try {
      const res = await fetch(`/api/v1/resources/${returnResource.id}/return`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Rakshagrid-Dev-Role': 'field_commander',
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Return failed (${res.status})`);
      }

      setReturnResource(null);
      showFeedback(`Successfully returned ${qty} ${returnResource.unit} to stockpile.`);
      fetchResources();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Open Audit Drawer / Refresh Resource with Audit Logs
  const handleOpenAudit = async (r) => {
    setActionError(null);
    try {
      const res = await fetch(`/api/v1/resources/${r.id}`);
      if (res.ok) {
        const full = await res.json();
        setAuditResource(full);
      } else {
        setAuditResource(r);
      }
    } catch {
      setAuditResource(r);
    }
  };

  // Delete Resource
  const handleDeleteResource = async () => {
    if (!deleteConfirm) return;
    setActionError(null);

    try {
      const res = await fetch(`/api/v1/resources/${deleteConfirm.id}`, {
        method: 'DELETE',
        headers: {
          'X-Rakshagrid-Dev-Role': 'admin',
        },
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Delete failed (${res.status})`);
      }

      setDeleteConfirm(null);
      showFeedback(`Resource stockpile ${deleteConfirm.code} deleted.`);
      fetchResources();
    } catch (err) {
      setActionError(err.message);
    }
  };

  // Aggregate Metrics
  const _totalStockSum = resources.reduce((acc, r) => acc + (r.quantity_total || 0), 0);
  const totalAvailSum = resources.reduce((acc, r) => acc + (r.quantity_available || 0), 0);
  const totalAllocSum = resources.reduce((acc, r) => acc + (r.quantity_allocated || Math.max(0, r.quantity_total - r.quantity_available)), 0);
  const lowStockCount = resources.filter(
    (r) => r.quantity_total > 0 && r.quantity_available / r.quantity_total <= 0.25
  ).length;

  return (
    <>
      {/* Page Header */}
      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Emergency Logistics & Resource Stockpiles</h2>
          <p>Inventory reserves, medical kits, water purification, rescue gear, dispatches, and chain-of-custody audits</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-primary" onClick={handleOpenCreate}>
            + Add Resource Stockpile
          </button>
        </div>
      </div>

      {/* Operational Feedback Notifications */}
      {actionSuccess && (
        <div
          style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid var(--rg-teal)',
            color: 'var(--rg-teal)',
            padding: '10px 16px',
            borderRadius: '6px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
          }}
        >
          <span>✓</span>
          <span>{actionSuccess}</span>
        </div>
      )}

      {actionError && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid var(--rg-red-light)',
            color: 'var(--rg-red-light)',
            padding: '10px 16px',
            borderRadius: '6px',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '13px',
          }}
        >
          <span>⚠</span>
          <span>{actionError}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="rg-kpi-grid">
        <div className="rg-kpi-card">
          <div className="rg-kpi-header">
            <span className="rg-kpi-label">Stockpile SKUs</span>
            <span className="rg-pulse-dot online" />
          </div>
          <div className="rg-kpi-value">{total}</div>
          <div className="rg-kpi-sub">Managed inventory categories</div>
        </div>

        <div className="rg-kpi-card">
          <div className="rg-kpi-header">
            <span className="rg-kpi-label">Available Units</span>
            <span className="rg-pulse-dot online" />
          </div>
          <div className="rg-kpi-value" style={{ color: 'var(--rg-teal)' }}>
            {Math.round(totalAvailSum).toLocaleString()}
          </div>
          <div className="rg-kpi-sub">Ready for immediate dispatch</div>
        </div>

        <div className="rg-kpi-card">
          <div className="rg-kpi-header">
            <span className="rg-kpi-label">Deployed / In-Field</span>
            <span className="rg-pulse-dot warning" />
          </div>
          <div className="rg-kpi-value" style={{ color: 'var(--rg-amber-light)' }}>
            {Math.round(totalAllocSum).toLocaleString()}
          </div>
          <div className="rg-kpi-sub">Allocated to missions & camps</div>
        </div>

        <div className="rg-kpi-card">
          <div className="rg-kpi-header">
            <span className="rg-kpi-label">Critical Stock Alerts</span>
            <span className={`rg-pulse-dot ${lowStockCount > 0 ? 'error' : 'online'}`} />
          </div>
          <div className="rg-kpi-value" style={{ color: lowStockCount > 0 ? 'var(--rg-red-light)' : 'var(--rg-text-primary)' }}>
            {lowStockCount}
          </div>
          <div className="rg-kpi-sub">&le; 25% remaining reserves</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rg-filter-bar">
        <div className="rg-search-box">
          <input
            type="text"
            placeholder="Search resources by code, name, staging depot..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className="rg-filter-select"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <label className="rg-checkbox-label">
          <input
            type="checkbox"
            checked={lowStockFilter}
            onChange={(e) => setLowStockFilter(e.target.checked)}
          />
          <span>Low Stock Reserves Only</span>
        </label>

        {(categoryFilter || lowStockFilter || search) && (
          <button
            className="rg-btn rg-btn-outline rg-btn-sm"
            onClick={() => {
              setCategoryFilter('');
              setLowStockFilter(false);
              setSearch('');
            }}
          >
            Clear Filters
          </button>
        )}

        <button className="rg-btn rg-btn-outline rg-btn-sm" onClick={fetchResources}>
          Refresh
        </button>
      </div>

      {/* Main Stockpile Table */}
      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Emergency Logistics Reserves</h3>
          <span style={{ fontSize: '12px', color: 'var(--rg-text-muted)' }}>
            Showing {resources.length} of {total} registered stockpiles
          </span>
        </div>

        <div className="rg-panel-body" style={{ padding: 0 }}>
          {loading ? (
            <div style={{ padding: '40px' }}>
              <LoadingState message="Querying emergency resource telemetry..." />
            </div>
          ) : error ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--rg-red-light)' }}>
              <p>Failed to load emergency resources: {error}</p>
              <button className="rg-btn rg-btn-outline rg-btn-sm" onClick={fetchResources} style={{ marginTop: '10px' }}>
                Retry
              </button>
            </div>
          ) : resources.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--rg-text-muted)' }}>
              No emergency resource stockpiles match your search criteria.
            </div>
          ) : (
            <div className="rg-table-wrapper">
              <table className="rg-table">
                <thead>
                  <tr>
                    <th>Stock Code</th>
                    <th>Resource Name & Category</th>
                    <th>Availability Status</th>
                    <th>Available / Total</th>
                    <th>Staging Depot</th>
                    <th>Readiness</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {resources.map((r) => {
                    const pctAvailable = r.quantity_total > 0
                      ? Math.min(100, Math.round((r.quantity_available / r.quantity_total) * 100))
                      : 0;

                    let barColor = 'var(--rg-teal)';
                    if (pctAvailable <= 25) barColor = 'var(--rg-red-light)';
                    else if (pctAvailable <= 50) barColor = 'var(--rg-amber-light)';

                    return (
                      <tr key={r.id}>
                        <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>
                          <span
                            style={{
                              background: 'rgba(255,255,255,0.05)',
                              padding: '3px 7px',
                              borderRadius: '4px',
                              border: '1px solid rgba(255,255,255,0.1)',
                            }}
                          >
                            {r.code}
                          </span>
                        </td>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{r.name}</div>
                          <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', marginTop: '2px' }}>
                            <span className="rg-pill rg-pill-minor" style={{ fontSize: '10px' }}>
                              {r.category}
                            </span>
                          </div>
                        </td>
                        <td style={{ minWidth: '140px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '3px' }}>
                            <span>{pctAvailable}% Ready</span>
                            <span style={{ color: 'var(--rg-text-muted)' }}>
                              {(r.quantity_allocated || 0)} {r.unit} allocated
                            </span>
                          </div>
                          <div
                            style={{
                              width: '100%',
                              height: '6px',
                              background: 'rgba(255,255,255,0.1)',
                              borderRadius: '3px',
                              overflow: 'hidden',
                            }}
                          >
                            <div
                              style={{
                                width: `${pctAvailable}%`,
                                height: '100%',
                                background: barColor,
                                transition: 'width 0.3s ease',
                              }}
                            />
                          </div>
                        </td>
                        <td style={{ fontFamily: 'var(--rg-font-mono)' }}>
                          <span style={{ fontWeight: 700, color: 'var(--rg-text-primary)' }}>
                            {r.quantity_available.toLocaleString()}
                          </span>
                          <span style={{ color: 'var(--rg-text-muted)', margin: '0 4px' }}>/</span>
                          <span style={{ color: 'var(--rg-text-secondary)' }}>
                            {r.quantity_total.toLocaleString()} {r.unit}
                          </span>
                        </td>
                        <td>
                          <div style={{ fontSize: '13px', color: 'var(--rg-text-primary)' }}>
                            {r.storage_location || 'Central Depot'}
                          </div>
                          {r.shelter_name && (
                            <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                              Shelter: {r.shelter_name}
                            </div>
                          )}
                        </td>
                        <td>
                          <span
                            className={`rg-pill ${
                              r.status === 'Adequate'
                                ? 'rg-pill-moderate'
                                : r.status === 'High Utilization'
                                ? 'rg-pill-severe'
                                : 'rg-pill-critical'
                            }`}
                          >
                            {r.status || 'Adequate'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end', flexWrap: 'nowrap' }}>
                            <button
                              className="rg-btn rg-btn-primary rg-btn-sm"
                              onClick={() => handleOpenAllocate(r)}
                              title="Allocate supplies to incident or team"
                              disabled={r.quantity_available <= 0}
                            >
                              Dispatch
                            </button>
                            <button
                              className="rg-btn rg-btn-outline rg-btn-sm"
                              onClick={() => handleOpenReturn(r)}
                              title="Return unused inventory to stockpile"
                              disabled={(r.quantity_allocated || 0) <= 0 && r.quantity_available >= r.quantity_total}
                            >
                              Return
                            </button>
                            <button
                              className="rg-btn rg-btn-outline rg-btn-sm"
                              onClick={() => handleOpenAudit(r)}
                              title="View chain-of-custody movement log"
                            >
                              Audit
                            </button>
                            <button
                              className="rg-btn rg-btn-outline rg-btn-sm"
                              onClick={() => handleOpenEdit(r)}
                              title="Edit stockpile details"
                            >
                              Edit
                            </button>
                            <button
                              className="rg-btn rg-btn-danger rg-btn-sm"
                              onClick={() => {
                                setActionError(null);
                                setDeleteConfirm(r);
                              }}
                              title="Delete resource"
                            >
                              ✕
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* CREATE / EDIT MODAL */}
      <ModalDialog
        isOpen={createModal}
        onClose={() => setCreateModal(false)}
        title={editResource ? `Edit Stockpile: ${editResource.code}` : 'Register Emergency Resource Stockpile'}
        actions={
          <>
            <button className="rg-btn rg-btn-outline" onClick={() => setCreateModal(false)}>
              Cancel
            </button>
            <button className="rg-btn rg-btn-primary" onClick={handleSaveResource}>
              {editResource ? 'Save Modifications' : 'Create Stockpile'}
            </button>
          </>
        }
      >
        <form onSubmit={handleSaveResource} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {actionError && (
            <div style={{ color: 'var(--rg-red-light)', fontSize: '12px' }}>{actionError}</div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Stock Code
              </label>
              <input
                type="text"
                disabled={!!editResource}
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                  fontFamily: 'var(--rg-font-mono)',
                }}
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Resource / Supply Name
              </label>
              <input
                type="text"
                placeholder="e.g. Inflatable Flood Rescue Rafts"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Category
              </label>
              <select
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Unit of Measurement
              </label>
              <input
                type="text"
                placeholder="e.g. kits, craft, units, packs"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Total Stock In Inventory
              </label>
              <input
                type="number"
                min="0"
                step="any"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                  fontFamily: 'var(--rg-font-mono)',
                }}
                value={formData.quantity_total}
                onChange={(e) => {
                  const val = parseFloat(e.target.value) || 0;
                  setFormData({
                    ...formData,
                    quantity_total: val,
                    quantity_available: editResource ? formData.quantity_available : val,
                  });
                }}
                required
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Available (Unallocated) Quantity
              </label>
              <input
                type="number"
                min="0"
                step="any"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                  fontFamily: 'var(--rg-font-mono)',
                }}
                value={formData.quantity_available}
                onChange={(e) => setFormData({ ...formData, quantity_available: parseFloat(e.target.value) || 0 })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Storage Location / Depot
              </label>
              <input
                type="text"
                placeholder="e.g. Guwahati Forward Logistics Base"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={formData.storage_location}
                onChange={(e) => setFormData({ ...formData, storage_location: e.target.value })}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Linked Shelter Depot (Optional)
              </label>
              <select
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={formData.shelter_id}
                onChange={(e) => setFormData({ ...formData, shelter_id: e.target.value })}
              >
                <option value="">-- No Shelter Link --</option>
                {shelters.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.shelter_type})</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
              Readiness Status
            </label>
            <select
              style={{
                width: '100%',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.15)',
                color: 'var(--rg-text-primary)',
                padding: '7px 10px',
                borderRadius: '4px',
              }}
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
            >
              <option value="Adequate">Adequate</option>
              <option value="High Utilization">High Utilization</option>
              <option value="Critical Reserve">Critical Reserve</option>
              <option value="Depleted">Depleted</option>
            </select>
          </div>
        </form>
      </ModalDialog>

      {/* DISPATCH / ALLOCATE MODAL */}
      <ModalDialog
        isOpen={!!allocateResource}
        onClose={() => setAllocateResource(null)}
        title={allocateResource ? `Dispatch Supplies: ${allocateResource.name} (${allocateResource.code})` : 'Allocate Resource'}
        actions={
          <>
            <button className="rg-btn rg-btn-outline" onClick={() => setAllocateResource(null)}>
              Cancel
            </button>
            <button className="rg-btn rg-btn-primary" onClick={handleExecuteAllocate}>
              Confirm Dispatch
            </button>
          </>
        }
      >
        {allocateResource && (
          <form onSubmit={handleExecuteAllocate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '10px 14px',
                borderRadius: '6px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>Available in Stockpile:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--rg-teal)' }}>
                  {allocateResource.quantity_available.toLocaleString()} {allocateResource.unit}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>Origin Staging:</span>
                <div style={{ fontSize: '13px', color: 'var(--rg-text-primary)' }}>
                  {allocateResource.storage_location || 'Central Depot'}
                </div>
              </div>
            </div>

            {actionError && (
              <div style={{ color: 'var(--rg-red-light)', fontSize: '12px' }}>{actionError}</div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Quantity to Allocate ({allocateResource.unit}) *
                </label>
                <input
                  type="number"
                  min="0.1"
                  max={allocateResource.quantity_available}
                  step="any"
                  style={{
                    width: '100%',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    color: 'var(--rg-text-primary)',
                    padding: '7px 10px',
                    borderRadius: '4px',
                    fontFamily: 'var(--rg-font-mono)',
                  }}
                  value={allocateForm.quantity}
                  onChange={(e) => setAllocateForm({ ...allocateForm, quantity: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                  Transport Mode
                </label>
                <select
                  style={{
                    width: '100%',
                    background: 'rgba(255,255,255,0.05)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    color: 'var(--rg-text-primary)',
                    padding: '7px 10px',
                    borderRadius: '4px',
                  }}
                  value={allocateForm.transport_mode}
                  onChange={(e) => setAllocateForm({ ...allocateForm, transport_mode: e.target.value })}
                >
                  {TRANSPORT_MODES.map((m) => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Destination Forward Location *
              </label>
              <input
                type="text"
                placeholder="e.g. Brahmaputra Sector 3 Field Clinic"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={allocateForm.destination}
                onChange={(e) => setAllocateForm({ ...allocateForm, destination: e.target.value })}
                required
              />
            </div>

            {/* Relational Mission Links */}
            <div
              style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.08)',
                padding: '12px',
                borderRadius: '6px',
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--rg-amber-light)', marginBottom: '10px' }}>
                OPTIONAL MISSION LINKAGES
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '10px', color: 'var(--rg-text-muted)', marginBottom: '3px' }}>
                    Linked Disaster Incident
                  </label>
                  <select
                    style={{
                      width: '100%',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'var(--rg-text-primary)',
                      padding: '6px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                    value={allocateForm.incident_id}
                    onChange={(e) => setAllocateForm({ ...allocateForm, incident_id: e.target.value })}
                  >
                    <option value="">-- No Incident Link --</option>
                    {incidents.map((inc) => (
                      <option key={inc.id} value={inc.id}>
                        {inc.title} ({inc.severity})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '10px', color: 'var(--rg-text-muted)', marginBottom: '3px' }}>
                    Linked Response Task
                  </label>
                  <select
                    style={{
                      width: '100%',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'var(--rg-text-primary)',
                      padding: '6px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                    value={allocateForm.task_id}
                    onChange={(e) => setAllocateForm({ ...allocateForm, task_id: e.target.value })}
                  >
                    <option value="">-- No Task Link --</option>
                    {tasks.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.title} ({t.status})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '10px', color: 'var(--rg-text-muted)', marginBottom: '3px' }}>
                    Custody Response Team
                  </label>
                  <select
                    style={{
                      width: '100%',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'var(--rg-text-primary)',
                      padding: '6px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                    value={allocateForm.team_id}
                    onChange={(e) => setAllocateForm({ ...allocateForm, team_id: e.target.value })}
                  >
                    <option value="">-- No Team Link --</option>
                    {teams.map((tm) => (
                      <option key={tm.id} value={tm.id}>
                        {tm.name} ({tm.specialization || tm.team_type})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '10px', color: 'var(--rg-text-muted)', marginBottom: '3px' }}>
                    Destination Shelter
                  </label>
                  <select
                    style={{
                      width: '100%',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      color: 'var(--rg-text-primary)',
                      padding: '6px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}
                    value={allocateForm.shelter_id}
                    onChange={(e) => setAllocateForm({ ...allocateForm, shelter_id: e.target.value })}
                  >
                    <option value="">-- No Shelter Link --</option>
                    {shelters.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name} ({s.shelter_type})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Dispatch Notes / Authorization Order
              </label>
              <textarea
                rows="2"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={allocateForm.notes}
                onChange={(e) => setAllocateForm({ ...allocateForm, notes: e.target.value })}
              />
            </div>
          </form>
        )}
      </ModalDialog>

      {/* RETURN INVENTORY MODAL */}
      <ModalDialog
        isOpen={!!returnResource}
        onClose={() => setReturnResource(null)}
        title={returnResource ? `Return Supplies: ${returnResource.name}` : 'Return Resource'}
        actions={
          <>
            <button className="rg-btn rg-btn-outline" onClick={() => setReturnResource(null)}>
              Cancel
            </button>
            <button className="rg-btn rg-btn-primary" onClick={handleExecuteReturn}>
              Acknowledge Return
            </button>
          </>
        }
      >
        {returnResource && (
          <form onSubmit={handleExecuteReturn} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div
              style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                padding: '10px 14px',
                borderRadius: '6px',
              }}
            >
              <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>Currently Allocated in Field:</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--rg-amber-light)' }}>
                {(returnResource.quantity_allocated || Math.max(0, returnResource.quantity_total - returnResource.quantity_available)).toLocaleString()} {returnResource.unit}
              </div>
            </div>

            {actionError && (
              <div style={{ color: 'var(--rg-red-light)', fontSize: '12px' }}>{actionError}</div>
            )}

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Quantity to Restock / Return ({returnResource.unit}) *
              </label>
              <input
                type="number"
                min="0.1"
                step="any"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                  fontFamily: 'var(--rg-font-mono)',
                }}
                value={returnForm.quantity}
                onChange={(e) => setReturnForm({ ...returnForm, quantity: e.target.value })}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Source Location / Origin *
              </label>
              <input
                type="text"
                placeholder="e.g. Returned from Field Camp B"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={returnForm.source_location}
                onChange={(e) => setReturnForm({ ...returnForm, source_location: e.target.value })}
                required
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--rg-text-muted)', marginBottom: '4px' }}>
                Return Condition & Notes
              </label>
              <textarea
                rows="2"
                style={{
                  width: '100%',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: 'var(--rg-text-primary)',
                  padding: '7px 10px',
                  borderRadius: '4px',
                }}
                value={returnForm.notes}
                onChange={(e) => setReturnForm({ ...returnForm, notes: e.target.value })}
              />
            </div>
          </form>
        )}
      </ModalDialog>

      {/* CHAIN-OF-CUSTODY AUDIT DRAWER MODAL */}
      <ModalDialog
        isOpen={!!auditResource}
        onClose={() => setAuditResource(null)}
        title={auditResource ? `Movement Audit: ${auditResource.code} — ${auditResource.name}` : 'Movement Audit'}
        actions={
          <button className="rg-btn rg-btn-primary" onClick={() => setAuditResource(null)}>
            Close Audit Log
          </button>
        }
      >
        {auditResource && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: '8px',
                background: 'rgba(255,255,255,0.03)',
                padding: '10px',
                borderRadius: '6px',
                border: '1px solid rgba(255,255,255,0.08)',
              }}
            >
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>CATEGORY</div>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{auditResource.category}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>TOTAL STOCK</div>
                <div style={{ fontSize: '12px', fontWeight: 600, fontFamily: 'var(--rg-font-mono)' }}>
                  {auditResource.quantity_total} {auditResource.unit}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>AVAILABLE</div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--rg-teal)', fontFamily: 'var(--rg-font-mono)' }}>
                  {auditResource.quantity_available} {auditResource.unit}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: 'var(--rg-text-muted)' }}>DEPOT STAGING</div>
                <div style={{ fontSize: '12px', fontWeight: 600 }}>{auditResource.storage_location || 'Central Depot'}</div>
              </div>
            </div>

            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--rg-text-primary)' }}>
              Chain-of-Custody Dispatches & Restocks ({auditResource.recent_movements?.length || 0})
            </div>

            {(!auditResource.recent_movements || auditResource.recent_movements.length === 0) ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--rg-text-muted)', fontSize: '12px' }}>
                No movement dispatches or transfers recorded yet for this stockpile.
              </div>
            ) : (
              <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
                <table className="rg-table" style={{ fontSize: '12px' }}>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Type</th>
                      <th>Quantity</th>
                      <th>Route / Destination</th>
                      <th>Transport</th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditResource.recent_movements.map((m) => (
                      <tr key={m.id}>
                        <td style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', whiteSpace: 'nowrap' }}>
                          {m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                        </td>
                        <td>
                          <span
                            className={`rg-pill ${
                              m.movement_type === 'allocation'
                                ? 'rg-pill-severe'
                                : m.movement_type === 'return'
                                ? 'rg-pill-moderate'
                                : 'rg-pill-minor'
                            }`}
                            style={{ fontSize: '10px', textTransform: 'uppercase' }}
                          >
                            {m.movement_type}
                          </span>
                        </td>
                        <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 600 }}>
                          {m.quantity} {auditResource.unit}
                        </td>
                        <td>
                          <div style={{ fontSize: '11px' }}>
                            {m.source_location ? `${m.source_location} → ` : ''}
                            <strong>{m.destination_location || 'Forward Unit'}</strong>
                          </div>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                          {m.transport_mode || 'Convoy'}
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--rg-text-muted)', maxWidth: '140px' }}>
                          {m.notes || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </ModalDialog>

      {/* DELETE CONFIRMATION MODAL */}
      <ModalDialog
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        title="Confirm Stockpile Deletion"
        actions={
          <>
            <button className="rg-btn rg-btn-outline" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </button>
            <button className="rg-btn rg-btn-danger" onClick={handleDeleteResource}>
              Confirm Decommission
            </button>
          </>
        }
      >
        {deleteConfirm && (
          <div>
            <p style={{ color: 'var(--rg-text-secondary)', marginBottom: '10px' }}>
              Are you sure you want to decommission and remove the stockpile for:
            </p>
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '6px', marginBottom: '12px' }}>
              <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{deleteConfirm.name}</div>
              <div style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                Code: {deleteConfirm.code} | Stock: {deleteConfirm.quantity_available} / {deleteConfirm.quantity_total} {deleteConfirm.unit}
              </div>
            </div>
            {actionError && (
              <div style={{ color: 'var(--rg-red-light)', fontSize: '12px', marginBottom: '8px' }}>
                {actionError}
              </div>
            )}
            <p style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
              Note: If this resource has active allocations in the field, deletion will be blocked by referential integrity safeguards to preserve chain-of-custody.
            </p>
          </div>
        )}
      </ModalDialog>
    </>
  );
}
