import React from 'react';

export function DemoNoticeBanner({ text }) {
  return (
    <div className="rg-demo-banner">
      <div className="rg-demo-banner-content">
        <span className="rg-demo-tag">DEMO ENVIRONMENT</span>
        <span>{text || 'Showing simulated disaster incident telemetry for Phase 1 architectural evaluation. Live sensors & external GIS feeds are deferred to Phase 2.'}</span>
      </div>
      <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
        PHASE 1 FOUNDATION
      </span>
    </div>
  );
}

export function LoadingState({ message = 'Loading disaster telemetry...' }) {
  return (
    <div className="rg-state-box">
      <div className="rg-pulse-dot online" style={{ width: '16px', height: '16px', marginBottom: '8px' }} />
      <div className="rg-state-title">{message}</div>
      <div className="rg-state-desc">Synchronizing with emergency response backend services...</div>
    </div>
  );
}

export function EmptyState({ title = 'No records located', description = 'There are no items matching the selected operational filters.' }) {
  return (
    <div className="rg-state-box">
      <svg className="rg-state-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <div className="rg-state-title">{title}</div>
      <div className="rg-state-desc">{description}</div>
    </div>
  );
}

export function ErrorState({ title = 'Telemetry Stream Degraded', message, onRetry }) {
  return (
    <div className="rg-state-box">
      <div className="rg-pulse-dot error" style={{ width: '16px', height: '16px', marginBottom: '8px' }} />
      <div className="rg-state-title" style={{ color: 'var(--rg-red-light)' }}>{title}</div>
      <div className="rg-state-desc">{message || 'Unable to establish secure telemetry handshake with backend services.'}</div>
      {onRetry && (
        <button className="rg-btn rg-btn-outline rg-btn-sm" onClick={onRetry} style={{ marginTop: '10px' }}>
          Retry Telemetry Query
        </button>
      )}
    </div>
  );
}

export function ModalDialog({ isOpen, onClose, title, children, actions }) {
  if (!isOpen) return null;

  return (
    <div className="rg-modal-backdrop" onClick={onClose}>
      <div className="rg-modal-window" onClick={(e) => e.stopPropagation()}>
        <div className="rg-modal-header">
          <h3>{title}</h3>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--rg-text-muted)',
              fontSize: '18px',
              cursor: 'pointer',
            }}
          >
            ×
          </button>
        </div>
        <div className="rg-modal-body">{children}</div>
        <div className="rg-modal-footer">
          {actions || (
            <button className="rg-btn rg-btn-primary" onClick={onClose}>
              Acknowledge
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
