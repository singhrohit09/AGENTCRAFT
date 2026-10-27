import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, LoadingState, ModalDialog } from './StateComponents';

export default function RakshaAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState(null);

  // Modals
  const [broadcastModal, setBroadcastModal] = useState(false);
  const [resolveModal, setResolveModal] = useState(false);
  const [selectedAlertForResolve, setSelectedAlertForResolve] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [actionInProgress, setActionInProgress] = useState(false);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      let url = '/api/v1/alerts?limit=50';
      if (statusFilter !== 'all') url += `&status=${statusFilter}`;
      if (severityFilter !== 'all') url += `&severity=${severityFilter}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (e) {
      console.error('Failed to fetch intelligent alerts:', e);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, severityFilter]);

  useEffect(() => {
    let ignore = false;
    fetchAlerts().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [fetchAlerts]);

  const handleEvaluateRules = async () => {
    setEvaluating(true);
    try {
      const res = await fetch('/api/v1/alerts/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-RakshaGrid-User-ID': 'watch-commander-01',
          'X-RakshaGrid-User-Role': 'commander',
        },
      });
      if (res.ok) {
        const data = await res.json();
        setEvalResult(data);
        await fetchAlerts();
      }
    } catch (e) {
      console.error('Alert evaluation failed:', e);
    } finally {
      setEvaluating(false);
    }
  };

  const handleAcknowledge = async (alertId) => {
    setActionInProgress(true);
    try {
      const res = await fetch(`/api/v1/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-RakshaGrid-User-ID': 'watch-commander-01',
          'X-RakshaGrid-User-Role': 'commander',
        },
        body: JSON.stringify({ operator_name: 'Watch Commander (HQ)' }),
      });
      if (res.ok) {
        await fetchAlerts();
      }
    } catch (e) {
      console.error('Failed to acknowledge alert:', e);
    } finally {
      setActionInProgress(false);
    }
  };

  const handleOpenResolve = (alert) => {
    setSelectedAlertForResolve(alert);
    setResolutionNotes('');
    setResolveModal(true);
  };

  const handleConfirmResolve = async () => {
    if (!selectedAlertForResolve || !resolutionNotes.trim()) return;
    setActionInProgress(true);
    try {
      const res = await fetch(`/api/v1/alerts/${selectedAlertForResolve.id}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-RakshaGrid-User-ID': 'watch-commander-01',
          'X-RakshaGrid-User-Role': 'commander',
        },
        body: JSON.stringify({
          resolution_notes: resolutionNotes.trim(),
          operator_name: 'Watch Commander (HQ)',
        }),
      });
      if (res.ok) {
        setResolveModal(false);
        setSelectedAlertForResolve(null);
        await fetchAlerts();
      }
    } catch (e) {
      console.error('Failed to resolve alert:', e);
    } finally {
      setActionInProgress(false);
    }
  };

  return (
    <>
      <DemoNoticeBanner text="AgentCraft Phase 4 Intelligent Alerts Engine. Driven by deterministic threshold rules, duplicate cooldown suppression, and operator verification." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Intelligent Alerts & Operational Warnings</h2>
          <p>Rule-driven incident alerts, meteorological hazard notifications, and traceable operator lifecycle management</p>
        </div>
        <div className="rg-page-controls" style={{ display: 'flex', gap: '10px' }}>
          <button
            className="rg-btn rg-btn-primary"
            onClick={handleEvaluateRules}
            disabled={evaluating}
          >
            {evaluating ? 'Evaluating Rules...' : '⚡ Evaluate Alert Rules'}
          </button>
          <button className="rg-btn rg-btn-danger" onClick={() => setBroadcastModal(true)}>
            📢 Issue CAP Broadcast
          </button>
        </div>
      </div>

      {evalResult && (
        <div
          style={{
            backgroundColor: 'var(--rg-bg-card)',
            border: '1px solid var(--rg-olive-base)',
            borderRadius: 'var(--rg-radius-md)',
            padding: '12px 16px',
            marginBottom: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '13px', color: 'var(--rg-text-primary)' }}>
            <strong>Threshold Evaluation Sweep:</strong> Evaluated {evalResult.incidents_evaluated} incidents, {evalResult.shelters_evaluated} shelters, {evalResult.resources_evaluated} stockpiles.
            Created <span style={{ color: 'var(--rg-amber-light)', fontWeight: 700 }}>{evalResult.alerts_created}</span> new alerts; suppressed <span style={{ color: 'var(--rg-olive-light)', fontWeight: 700 }}>{evalResult.alerts_suppressed_by_cooldown}</span> duplicates via 15m cooldown.
          </div>
          <button
            className="rg-btn rg-btn-secondary"
            style={{ fontSize: '11px', padding: '4px 8px' }}
            onClick={() => setEvalResult(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Filter Bar */}
      <div
        className="rg-panel"
        style={{
          marginBottom: '16px',
          padding: '12px 16px',
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
          flexWrap: 'wrap',
          backgroundColor: 'var(--rg-bg-panel)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', fontWeight: 600 }}>Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--rg-bg-inset)',
              color: 'var(--rg-text-primary)',
              border: '1px solid var(--rg-border-subtle)',
              borderRadius: 'var(--rg-radius-sm)',
              padding: '6px 10px',
              fontSize: '12px',
            }}
          >
            <option value="all">All Statuses</option>
            <option value="active">Active (Unresolved)</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', fontWeight: 600 }}>Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            style={{
              backgroundColor: 'var(--rg-bg-inset)',
              color: 'var(--rg-text-primary)',
              border: '1px solid var(--rg-border-subtle)',
              borderRadius: 'var(--rg-radius-sm)',
              padding: '6px 10px',
              fontSize: '12px',
            }}
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>
          Showing {alerts.length} alerts
        </div>
      </div>

      {/* Alerts List */}
      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Emergency Alerts Queue</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            CAP v1.2 PROTOCOL • TRACEABLE AUDIT TRAIL
          </span>
        </div>
        <div className="rg-panel-body">
          {loading ? (
            <LoadingState message="Retrieving active and historical emergency alerts..." />
          ) : alerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--rg-text-muted)' }}>
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>🛡️</div>
              <p>No alerts matching the selected filter criteria.</p>
              <button className="rg-btn rg-btn-secondary" onClick={handleEvaluateRules}>
                Run Rule Evaluation Sweep
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {alerts.map((alt) => {
                const isCrit = alt.severity === 'critical';
                const isHigh = alt.severity === 'high';
                const borderColor = isCrit ? 'var(--rg-red-base)' : isHigh ? 'var(--rg-amber-base)' : 'var(--rg-border-subtle)';

                return (
                  <div
                    key={alt.id}
                    style={{
                      backgroundColor: 'var(--rg-bg-card)',
                      border: '1px solid var(--rg-border-subtle)',
                      borderLeft: `4px solid ${borderColor}`,
                      borderRadius: 'var(--rg-radius-md)',
                      padding: '16px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                        <span className={`rg-pill ${isCrit ? 'rg-pill-critical' : isHigh ? 'rg-pill-severe' : 'rg-pill-moderate'}`}>
                          {alt.severity.toUpperCase()}
                        </span>
                        <span className={`rg-pill ${alt.broadcast_status === 'active' ? 'rg-pill-critical' : alt.broadcast_status === 'acknowledged' ? 'rg-pill-severe' : 'rg-pill-moderate'}`}>
                          STATUS: {alt.broadcast_status.toUpperCase()}
                        </span>
                        <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                          URGENCY: {alt.urgency.toUpperCase()}
                        </span>
                        {alt.source_type && (
                          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-olive-light)', backgroundColor: 'var(--rg-bg-inset)', padding: '2px 6px', borderRadius: '4px' }}>
                            SRC: {alt.source_type}
                          </span>
                        )}
                      </div>
                      <span style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                        CODE: {alt.alert_code}
                      </span>
                    </div>

                    <h4 style={{ margin: '0 0 6px 0', fontSize: '15px', color: 'var(--rg-text-primary)' }}>{alt.headline}</h4>

                    {alt.trigger_reason && (
                      <div style={{ fontSize: '12px', color: 'var(--rg-amber-light)', marginBottom: '8px' }}>
                        <strong>Trigger Reason:</strong> {alt.trigger_reason}
                      </div>
                    )}

                    <div style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '8px' }}>
                      <strong>Target Zone:</strong> {alt.target_region}
                    </div>

                    <div style={{ backgroundColor: 'var(--rg-bg-inset)', padding: '10px 12px', borderRadius: '4px', fontSize: '12px', color: 'var(--rg-text-primary)', marginBottom: '12px' }}>
                      <strong>Instructions:</strong> {alt.instructions}
                    </div>

                    {/* Operational Lifecycle & Actions */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', paddingTop: '8px', borderTop: '1px solid var(--rg-border-subtle)' }}>
                      <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                        <span>Issued: {new Date(alt.issued_at).toLocaleString()}</span>
                        {alt.acknowledged_at && (
                          <span style={{ marginLeft: '12px', color: 'var(--rg-olive-light)' }}>
                            ✓ Acknowledged by {alt.acknowledged_by} ({new Date(alt.acknowledged_at).toLocaleTimeString()})
                          </span>
                        )}
                        {alt.resolved_at && (
                          <span style={{ marginLeft: '12px', color: 'var(--rg-text-secondary)' }}>
                            ✓ Resolved by {alt.resolved_by} ({new Date(alt.resolved_at).toLocaleTimeString()})
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        {alt.broadcast_status === 'active' && (
                          <button
                            className="rg-btn rg-btn-secondary"
                            style={{ fontSize: '11px', padding: '4px 10px' }}
                            disabled={actionInProgress}
                            onClick={() => handleAcknowledge(alt.id)}
                          >
                            ✓ Acknowledge
                          </button>
                        )}
                        {alt.broadcast_status !== 'resolved' && (
                          <button
                            className="rg-btn rg-btn-primary"
                            style={{ fontSize: '11px', padding: '4px 10px' }}
                            disabled={actionInProgress}
                            onClick={() => handleOpenResolve(alt)}
                          >
                            Resolve Alert
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Resolve Dialog Modal */}
      <ModalDialog isOpen={resolveModal} onClose={() => setResolveModal(false)} title="Operational Alert Resolution">
        <div>
          <p style={{ fontSize: '13px', color: 'var(--rg-text-secondary)', marginBottom: '12px' }}>
            Marking alert <strong>{selectedAlertForResolve?.alert_code}</strong> as resolved.
            Provide on-scene confirmation and actions taken:
          </p>
          <textarea
            rows={4}
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="e.g. Field teams deployed and embankment breach stabilized. Evacuees safely received at Sector 4 shelter."
            style={{
              width: '100%',
              backgroundColor: 'var(--rg-bg-inset)',
              color: 'var(--rg-text-primary)',
              border: '1px solid var(--rg-border-subtle)',
              borderRadius: 'var(--rg-radius-sm)',
              padding: '10px',
              fontSize: '12px',
              fontFamily: 'inherit',
              marginBottom: '16px',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
            <button className="rg-btn rg-btn-secondary" onClick={() => setResolveModal(false)}>
              Cancel
            </button>
            <button
              className="rg-btn rg-btn-primary"
              disabled={actionInProgress || !resolutionNotes.trim()}
              onClick={handleConfirmResolve}
            >
              {actionInProgress ? 'Saving...' : 'Confirm Resolution'}
            </button>
          </div>
        </div>
      </ModalDialog>

      {/* CAP Broadcast Modal */}
      <ModalDialog isOpen={broadcastModal} onClose={() => setBroadcastModal(false)} title="Manual CAP Broadcast Dispatcher">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="rg-pulse-dot warning" />
            <strong style={{ color: 'var(--rg-amber-light)' }}>Human-in-the-Loop Operational Gate</strong>
          </div>
          <p style={{ color: 'var(--rg-text-secondary)', fontSize: '13px' }}>
            Broadcasting public emergency warnings triggers cellular Emergency Alert Systems (EAS) and multi-channel siren networks.
            In compliance with national emergency protocols, manual issuance requires verified field commander authorization.
          </p>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
            <button className="rg-btn rg-btn-secondary" onClick={() => setBroadcastModal(false)}>
              Close
            </button>
          </div>
        </div>
      </ModalDialog>
    </>
  );
}
