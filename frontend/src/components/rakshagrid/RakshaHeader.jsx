import React, { useState, useEffect } from 'react';

export default function RakshaHeader({
  healthData,
  activePlatformMode,
  setActivePlatformMode,
  onRefresh,
}) {
  const [utcTime, setUtcTime] = useState('');
  const [localTime, setLocalTime] = useState('');

  useEffect(() => {
    const updateClocks = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().slice(17, 25) + ' UTC');
      setLocalTime(now.toLocaleTimeString());
    };
    updateClocks();
    const interval = setInterval(updateClocks, 1000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = healthData && healthData.status === 'operational';
  const isFallback = healthData && healthData.status === 'operational_demo_fallback';
  const defconLevel = healthData ? healthData.defcon_level : 2;

  return (
    <>
      {/* Top Telemetry Bar */}
      <div className="rg-system-bar">
        <div className="rg-system-bar-left">
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className={`rg-pulse-dot ${isHealthy ? 'online' : isFallback ? 'warning' : 'error'}`} />
            SYSTEM: {healthData ? healthData.status.toUpperCase() : 'INITIALIZING'}
          </span>
          <span>•</span>
          <span>DISASTER DEFCON: {defconLevel}</span>
          <span>•</span>
          <span>ENV: {healthData?.environment?.toUpperCase() || 'DEVELOPMENT'}</span>
        </div>
        <div className="rg-system-bar-right">
          <span>LOCAL: {localTime}</span>
          <span>•</span>
          <span style={{ color: 'var(--rg-text-primary)' }}>{utcTime}</span>
          <span>•</span>
          <button
            onClick={onRefresh}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--rg-text-secondary)',
              cursor: 'pointer',
              fontSize: '11px',
              textDecoration: 'underline',
              fontFamily: 'var(--rg-font-mono)',
            }}
          >
            REFRESH
          </button>
        </div>
      </div>

      {/* Main Command Header */}
      <header className="rg-header">
        <div className="rg-brand">
          <div className="rg-logo-mark">RG</div>
          <div className="rg-brand-text">
            <h1>
              RakshaGrid
              <span className="rg-phase-tag">Phase 1 Foundation</span>
            </h1>
            <p>Disaster Intelligence and Response</p>
          </div>
        </div>

        <div className="rg-header-actions">
          {/* DEFCON Badge */}
          <div className={`rg-defcon-badge level-${defconLevel}`}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'currentColor' }} />
            DEFCON {defconLevel} — HIGH SEVERITY
          </div>

          {/* Platform Switcher */}
          <div className="rg-platform-switch">
            <button
              className={`rg-switch-btn ${activePlatformMode === 'rakshagrid' ? 'active' : ''}`}
              onClick={() => setActivePlatformMode('rakshagrid')}
            >
              RakshaGrid Ops
            </button>
            <button
              className={`rg-switch-btn ${activePlatformMode === 'agentcraft' ? 'active' : ''}`}
              onClick={() => setActivePlatformMode('agentcraft')}
            >
              AgentCraft AI Engine
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
