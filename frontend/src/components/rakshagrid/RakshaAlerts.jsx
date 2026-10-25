import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, LoadingState, ModalDialog } from './StateComponents';

export default function RakshaAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [broadcastModal, setBroadcastModal] = useState(false);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch('/api/rakshagrid/alerts');
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (e) {
      console.error('Failed to fetch alerts:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    fetchAlerts().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [fetchAlerts]);

  return (
    <>
      <DemoNoticeBanner text="Emergency Alert Broadcast Console conforming to Common Alerting Protocol (CAP v1.2) standards." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Emergency Alert Broadcast Console</h2>
          <p>Public warnings, evacuation orders, and multi-channel cellular emergency broadcasts</p>
        </div>
        <div className="rg-page-controls">
          <button className="rg-btn rg-btn-danger" onClick={() => setBroadcastModal(true)}>
            📢 Issue CAP Broadcast
          </button>
        </div>
      </div>

      <div className="rg-panel">
        <div className="rg-panel-header">
          <h3>Active Emergency Broadcasts</h3>
          <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
            CAP v1.2 STANDARD
          </span>
        </div>
        <div className="rg-panel-body">
          {loading ? (
            <LoadingState message="Retrieving active broadcast queue..." />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {alerts.map((alt) => (
                <div
                  key={alt.id}
                  style={{
                    backgroundColor: 'var(--rg-bg-card)',
                    border: '1px solid var(--rg-border-subtle)',
                    borderLeft: `4px solid ${alt.severity === 'extreme' ? 'var(--rg-red-base)' : 'var(--rg-amber-base)'}`,
                    borderRadius: 'var(--rg-radius-md)',
                    padding: '16px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <span className={`rg-pill rg-pill-${alt.severity === 'extreme' ? 'critical' : 'severe'}`}>
                        {alt.severity}
                      </span>
                      <span className="rg-pill rg-pill-active">{alt.broadcast_status}</span>
                      <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                        URGENCY: {alt.urgency.toUpperCase()}
                      </span>
                    </div>
                    <span style={{ fontFamily: 'var(--rg-font-mono)', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                      CODE: {alt.alert_code}
                    </span>
                  </div>

                  <h4 style={{ margin: '0 0 6px 0', fontSize: '15px', color: 'var(--rg-text-primary)' }}>{alt.headline}</h4>

                  <div style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '8px' }}>
                    <strong>Target Zone:</strong> {alt.target_region}
                  </div>

                  <div style={{ backgroundColor: 'var(--rg-bg-inset)', padding: '10px 12px', borderRadius: '4px', fontSize: '12px', color: 'var(--rg-text-primary)', marginBottom: '8px' }}>
                    <strong>Instructions:</strong> {alt.instructions}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                    <span>Issued: {new Date(alt.issued_at).toLocaleString()}</span>
                    {alt.evacuation_recommended && (
                      <span style={{ color: 'var(--rg-red-light)', fontWeight: 700 }}>
                        ⚠️ Evacuation Order Active
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ModalDialog isOpen={broadcastModal} onClose={() => setBroadcastModal(false)} title="CAP Broadcast Dispatcher">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span className="rg-pulse-dot warning" />
            <strong style={{ color: 'var(--rg-amber-light)' }}>Phase 1 Foundation Scope</strong>
          </div>
          <p style={{ color: 'var(--rg-text-secondary)' }}>
            The <code>alerts</code> table schema is fully established with CAP v1.2 attributes (<code>headline</code>, <code>urgency</code>, <code>severity</code>, <code>certainty</code>, <code>instructions</code>). In Phase 2, live multi-carrier broadcast channels (Cell Broadcast Service, SMS Gateway, VHF Radio synthesizers) will be connected.
          </p>
        </div>
      </ModalDialog>
    </>
  );
}
