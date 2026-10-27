import React, { useState, useEffect, useCallback } from 'react';
import { DemoNoticeBanner, LoadingState, ModalDialog } from './StateComponents';

const SCENARIO_PRESETS = [
  {
    id: 'heavy_rainfall',
    name: 'Heavy Rainfall & Flash Flood Inundation',
    desc: 'Simulates 50-200mm rainfall storm surge, river discharge elevation, and shelter intake demand.',
    defaultParams: { rainfall_mm: 120, duration_hours: 6 },
  },
  {
    id: 'multi_incident',
    name: 'Multi-Incident Catastrophic Concurrency',
    desc: 'Simulates simultaneous compound disasters (flood + landslide + seismic) stressing ready rescue teams.',
    defaultParams: { concurrent_incidents_count: 5, severity: 'critical' },
  },
  {
    id: 'team_unavailability',
    name: 'Response Team Unavailability & Isolation',
    desc: 'Simulates rescue units being cut off or stranded, evaluating operational coverage deficits.',
    defaultParams: { withdrawn_teams_count: 2, unit_type: 'NDRF' },
  },
  {
    id: 'shelter_surge',
    name: 'Mass Evacuee Shelter Surge',
    desc: 'Simulates sudden influx of displaced populations exceeding regional shelter capacity limits.',
    defaultParams: { incoming_evacuees: 2500 },
  },
  {
    id: 'supply_shortage',
    name: 'Relief Stockpile Depletion & Disruption',
    desc: 'Simulates accelerated supply burn rate and models days until critical stockout.',
    defaultParams: { burn_rate_multiplier: 3.0, duration_days: 4 },
  },
  {
    id: 'cascade_compound',
    name: 'Compound Cascade Stress-Test',
    desc: 'Compound multi-variable emergency: extreme storm surge + team outages + shelter saturation.',
    defaultParams: { rainfall_mm: 150, concurrent_incidents_count: 4, incoming_evacuees: 3000 },
  },
];

export default function RakshaRiskAnalysis() {
  const [activeTab, setActiveTab] = useState('risk_engine'); // 'risk_engine' | 'ai_agent' | 'simulations' | 'external_data'

  // Incidents data
  const [incidents, setIncidents] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState('');
  const [assessingRisk, setAssessingRisk] = useState(false);
  const [riskResult, setRiskResult] = useState(null);
  const [riskHistory, setRiskHistory] = useState([]);

  // AI Agent data
  const [runningAgent, setRunningAgent] = useState(false);
  const [agentAnalysis, setAgentAnalysis] = useState(null);
  const [approvalModal, setApprovalModal] = useState(false);
  const [approvalNotes, setApprovalNotes] = useState('');
  const [approvalDecision, setApprovalDecision] = useState(true);
  const [approvalSaving, setApprovalSaving] = useState(false);

  // Simulations data
  const [selectedScenario, setSelectedScenario] = useState(SCENARIO_PRESETS[0]);
  const [simParams, setSimParams] = useState(SCENARIO_PRESETS[0].defaultParams);
  const [runningSim, setRunningSim] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simHistory, setSimHistory] = useState([]);

  // External Data Health & Inspector
  const [inspectLat, setInspectLat] = useState('26.185');
  const [inspectLon, setInspectLon] = useState('91.748');
  const [inspectingTelemetry, setInspectingTelemetry] = useState(false);
  const [inspectResult, setInspectResult] = useState(null);
  const [externalHealth, setExternalHealth] = useState(null);

  // Initial load
  const loadInitialData = useCallback(async () => {
    try {
      const [incRes, histRes, simHistRes, healthRes] = await Promise.all([
        fetch('/api/v1/incidents?page_size=25').catch(() => null),
        fetch('/api/v1/intelligence/risk/assessments?limit=10').catch(() => null),
        fetch('/api/v1/intelligence/simulations/history?limit=10').catch(() => null),
        fetch('/api/v1/intelligence/external-data/health').catch(() => null),
      ]);

      if (incRes && incRes.ok) {
        const data = await incRes.json();
        const items = data.items || [];
        setIncidents(items);
        if (items.length > 0 && !selectedIncidentId) {
          setSelectedIncidentId(items[0].id);
        }
      }
      if (histRes && histRes.ok) {
        const data = await histRes.json();
        setRiskHistory(data.assessments || []);
      }
      if (simHistRes && simHistRes.ok) {
        const data = await simHistRes.json();
        setSimHistory(data.simulations || []);
      }
      if (healthRes && healthRes.ok) {
        setExternalHealth(await healthRes.json());
      }
    } catch (e) {
      console.error('Failed to load intelligence initial data:', e);
    }
  }, [selectedIncidentId]);

  useEffect(() => {
    let ignore = false;
    loadInitialData().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [loadInitialData]);

  // Actions
  const handleAssessRisk = async () => {
    if (!selectedIncidentId) return;
    setAssessingRisk(true);
    try {
      const res = await fetch(`/api/v1/intelligence/risk/assess/${selectedIncidentId}`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setRiskResult(data);
        // Refresh history
        const hRes = await fetch('/api/v1/intelligence/risk/assessments?limit=10');
        if (hRes.ok) {
          const hData = await hRes.json();
          setRiskHistory(hData.assessments || []);
        }
      }
    } catch (e) {
      console.error('Risk assessment failed:', e);
    } finally {
      setAssessingRisk(false);
    }
  };

  const handleRunAgentAnalysis = async () => {
    setRunningAgent(true);
    try {
      const res = await fetch('/api/v1/intelligence/agent/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ incident_id: selectedIncidentId || null }),
      });
      if (res.ok) {
        const data = await res.json();
        setAgentAnalysis(data);
      }
    } catch (e) {
      console.error('Agent analysis failed:', e);
    } finally {
      setRunningAgent(false);
    }
  };

  const handleOpenApproval = (decision) => {
    setApprovalDecision(decision);
    setApprovalNotes('');
    setApprovalModal(true);
  };

  const handleConfirmApproval = async () => {
    if (!agentAnalysis?.analysis_id) return;
    setApprovalSaving(true);
    try {
      const res = await fetch('/api/v1/intelligence/agent/plan/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-RakshaGrid-User-ID': 'commander-01',
          'X-RakshaGrid-User-Role': 'commander',
        },
        body: JSON.stringify({
          analysis_id: agentAnalysis.analysis_id,
          approve: approvalDecision,
          notes: approvalNotes.trim() || (approvalDecision ? 'Approved for tactical staging' : 'Rejected by commander'),
        }),
      });
      if (res.ok) {
        const updated = await res.json();
        setAgentAnalysis((prev) => ({
          ...prev,
          decision_gate: {
            ...prev.decision_gate,
            approval_status: updated.approval_status,
            approved_by: updated.approved_by,
            approved_at: updated.approved_at,
          },
        }));
        setApprovalModal(false);
      }
    } catch (e) {
      console.error('Failed to submit approval:', e);
    } finally {
      setApprovalSaving(false);
    }
  };

  const handleRunSimulation = async () => {
    setRunningSim(true);
    try {
      const res = await fetch('/api/v1/intelligence/simulations/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_type: selectedScenario.id,
          scenario_name: selectedScenario.name,
          parameters: simParams,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSimResult(data);
        // Refresh simulation history
        const hRes = await fetch('/api/v1/intelligence/simulations/history?limit=10');
        if (hRes.ok) {
          const hData = await hRes.json();
          setSimHistory(hData.simulations || []);
        }
      }
    } catch (e) {
      console.error('Simulation execution failed:', e);
    } finally {
      setRunningSim(false);
    }
  };

  const handleInspectTelemetry = async () => {
    setInspectingTelemetry(true);
    try {
      const res = await fetch(`/api/v1/intelligence/external-data/weather?latitude=${inspectLat}&longitude=${inspectLon}&force_refresh=true`);
      if (res.ok) {
        setInspectResult(await res.json());
      }
    } catch (e) {
      console.error('Telemetry query failed:', e);
    } finally {
      setInspectingTelemetry(false);
    }
  };

  return (
    <>
      <DemoNoticeBanner text="AgentCraft Phase 4 Disaster Intelligence & Response Engine. Powered by deterministic risk heuristics, live Open-Meteo telemetry, AI agent decision-support, and state-isolated stress simulations." />

      <div className="rg-page-header">
        <div className="rg-page-title">
          <h2>Disaster Intelligence & Scenario Simulation Mission Control</h2>
          <p>Compound hazard modeling, explainable risk calculations, tool-using AI decision support, and hypothetical scenario stress-testing</p>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid var(--rg-border-subtle)',
          marginBottom: '20px',
        }}
      >
        <button
          onClick={() => setActiveTab('risk_engine')}
          style={{
            padding: '10px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'risk_engine' ? '2px solid var(--rg-olive-light)' : '2px solid transparent',
            color: activeTab === 'risk_engine' ? 'var(--rg-text-primary)' : 'var(--rg-text-secondary)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          📊 Explainable Risk Engine
        </button>
        <button
          onClick={() => setActiveTab('ai_agent')}
          style={{
            padding: '10px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'ai_agent' ? '2px solid var(--rg-olive-light)' : '2px solid transparent',
            color: activeTab === 'ai_agent' ? 'var(--rg-text-primary)' : 'var(--rg-text-secondary)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          🤖 AI Disaster Intelligence Agent
        </button>
        <button
          onClick={() => setActiveTab('simulations')}
          style={{
            padding: '10px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'simulations' ? '2px solid var(--rg-olive-light)' : '2px solid transparent',
            color: activeTab === 'simulations' ? 'var(--rg-text-primary)' : 'var(--rg-text-secondary)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          ⚡ Scenario Simulations
        </button>
        <button
          onClick={() => setActiveTab('external_data')}
          style={{
            padding: '10px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'external_data' ? '2px solid var(--rg-olive-light)' : '2px solid transparent',
            color: activeTab === 'external_data' ? 'var(--rg-text-primary)' : 'var(--rg-text-secondary)',
            fontWeight: 600,
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          📡 External Telemetry & Health
        </button>
      </div>

      {/* ============================================================================== */}
      {/* TAB 1: Explainable Disaster Risk Assessment Engine                             */}
      {/* ============================================================================== */}
      {activeTab === 'risk_engine' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Controls Card */}
          <div className="rg-panel" style={{ padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--rg-text-secondary)' }}>
                  Select Target Incident:
                </label>
                <select
                  value={selectedIncidentId}
                  onChange={(e) => setSelectedIncidentId(e.target.value)}
                  style={{
                    backgroundColor: 'var(--rg-bg-inset)',
                    color: 'var(--rg-text-primary)',
                    border: '1px solid var(--rg-border-subtle)',
                    borderRadius: 'var(--rg-radius-sm)',
                    padding: '8px 12px',
                    fontSize: '13px',
                    minWidth: '320px',
                  }}
                >
                  {incidents.map((inc) => (
                    <option key={inc.id} value={inc.id}>
                      [{inc.incident_code}] {inc.title} ({inc.category} • {inc.severity})
                    </option>
                  ))}
                </select>
              </div>

              <button
                className="rg-btn rg-btn-primary"
                onClick={handleAssessRisk}
                disabled={assessingRisk || !selectedIncidentId}
              >
                {assessingRisk ? 'Calculating Score...' : 'Assess Environmental Risk'}
              </button>
            </div>
          </div>

          {/* Assessment Result View */}
          {assessingRisk ? (
            <LoadingState message="Querying meteorological telemetry and calculating explainable risk breakdown..." />
          ) : riskResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Score & Category Callout Card */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '16px',
                }}
              >
                <div className="rg-card" style={{ padding: '20px', textAlign: 'center', backgroundColor: 'var(--rg-bg-card)', border: '1px solid var(--rg-border-subtle)', borderRadius: 'var(--rg-radius-md)' }}>
                  <div style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '6px' }}>CALCULATED RISK SCORE</div>
                  <div style={{ fontSize: '42px', fontWeight: 800, fontFamily: 'var(--rg-font-mono)', color: riskResult.risk_level === 'Critical' ? 'var(--rg-red-light)' : riskResult.risk_level === 'High' ? 'var(--rg-amber-light)' : 'var(--rg-olive-light)' }}>
                    {riskResult.calculated_risk_score} <span style={{ fontSize: '18px', color: 'var(--rg-text-muted)' }}>/ 100</span>
                  </div>
                  <div style={{ marginTop: '8px' }}>
                    <span className={`rg-pill ${riskResult.risk_level === 'Critical' ? 'rg-pill-critical' : riskResult.risk_level === 'High' ? 'rg-pill-severe' : 'rg-pill-moderate'}`}>
                      {riskResult.risk_level.toUpperCase()} HAZARD LEVEL
                    </span>
                  </div>
                </div>

                <div className="rg-card" style={{ padding: '20px', backgroundColor: 'var(--rg-bg-card)', border: '1px solid var(--rg-border-subtle)', borderRadius: 'var(--rg-radius-md)' }}>
                  <div style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '8px' }}>OPERATIONAL CONTEXT</div>
                  <div style={{ fontSize: '13px', marginBottom: '4px' }}>
                    <strong>Reported Field Severity:</strong> <span style={{ textTransform: 'capitalize' }}>{riskResult.reported_severity}</span>
                  </div>
                  <div style={{ fontSize: '13px', marginBottom: '4px' }}>
                    <strong>Lifecycle Status:</strong> <span style={{ textTransform: 'capitalize' }}>{riskResult.operational_status}</span>
                  </div>
                  <div style={{ fontSize: '13px', marginBottom: '4px' }}>
                    <strong>Confidence Metric:</strong> {Math.round(riskResult.confidence_score * 100)}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', marginTop: '8px' }}>
                    Assessed at: {new Date(riskResult.assessed_at).toLocaleString()}
                  </div>
                </div>

                <div className="rg-card" style={{ padding: '20px', backgroundColor: 'var(--rg-bg-card)', border: '1px solid var(--rg-border-subtle)', borderRadius: 'var(--rg-radius-md)' }}>
                  <div style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '8px' }}>DATA SOURCES & FRESHNESS</div>
                  {riskResult.data_sources && riskResult.data_sources.length > 0 ? (
                    riskResult.data_sources.map((src, i) => (
                      <div key={i} style={{ fontSize: '12px', marginBottom: '6px' }}>
                        <span style={{ color: 'var(--rg-olive-light)' }}>●</span> {src.source}:{' '}
                        <span className="rg-pill rg-pill-active" style={{ fontSize: '10px' }}>
                          {src.status.toUpperCase()}
                        </span>
                        {src.freshness_seconds !== null && (
                          <span style={{ marginLeft: '6px', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                            ({src.freshness_seconds}s age)
                          </span>
                        )}
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: '12px', color: 'var(--rg-text-muted)' }}>Using internal incident metadata</div>
                  )}
                </div>
              </div>

              {/* Factors Breakdown Table */}
              <div className="rg-panel">
                <div className="rg-panel-header">
                  <h3>Explainable Factor Contribution Breakdown</h3>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                    DETERMINISTIC WEIGHTING MATRIX
                  </span>
                </div>
                <div className="rg-panel-body" style={{ padding: 0 }}>
                  <div className="rg-table-wrapper">
                    <table className="rg-table">
                      <thead>
                        <tr>
                          <th>Dimension Factor</th>
                          <th>Points Contribution</th>
                          <th>Max Weight</th>
                          <th>Detailed Diagnostic Description</th>
                          <th>Impact Class</th>
                        </tr>
                      </thead>
                      <tbody>
                        {riskResult.scoring_breakdown.map((row, idx) => (
                          <tr key={idx}>
                            <td style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{row.factor}</td>
                            <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700, color: row.contribution > 0 ? 'var(--rg-text-primary)' : 'var(--rg-olive-light)' }}>
                              {row.contribution > 0 ? `+${row.contribution}` : row.contribution} pts
                            </td>
                            <td style={{ color: 'var(--rg-text-muted)', fontFamily: 'var(--rg-font-mono)' }}>
                              {row.max_possible} pts
                            </td>
                            <td style={{ fontSize: '12px', color: 'var(--rg-text-secondary)' }}>{row.description}</td>
                            <td>
                              <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', backgroundColor: 'var(--rg-bg-inset)', padding: '2px 6px', borderRadius: '4px' }}>
                                {row.impact}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Data Gaps and Interventions */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="rg-panel">
                  <div className="rg-panel-header">
                    <h4>Identified Data Gaps & Uncertainty</h4>
                  </div>
                  <div className="rg-panel-body">
                    {riskResult.data_gaps && riskResult.data_gaps.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: 'var(--rg-amber-light)' }}>
                        {riskResult.data_gaps.map((gap, i) => (
                          <li key={i} style={{ marginBottom: '6px' }}>
                            {gap}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div style={{ fontSize: '12px', color: 'var(--rg-olive-light)' }}>
                        ✓ Zero significant telemetry or validation gaps identified.
                      </div>
                    )}
                  </div>
                </div>

                <div className="rg-panel">
                  <div className="rg-panel-header">
                    <h4>Recommended Tactical Interventions</h4>
                  </div>
                  <div className="rg-panel-body">
                    <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px', color: 'var(--rg-text-primary)' }}>
                      {riskResult.recommended_interventions.map((action, i) => (
                        <li key={i} style={{ marginBottom: '6px' }}>
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Disclaimer */}
              <div style={{ backgroundColor: 'var(--rg-bg-inset)', padding: '10px 14px', borderRadius: 'var(--rg-radius-sm)', border: '1px solid var(--rg-border-subtle)', fontSize: '11px', color: 'var(--rg-text-muted)' }}>
                ℹ️ <strong>Scientific Heuristic Disclaimer:</strong> {riskResult.scientific_limitation_disclaimer}
              </div>
            </div>
          ) : (
            <div className="rg-panel" style={{ padding: '30px', textAlign: 'center', color: 'var(--rg-text-muted)' }}>
              Select an incident above and click "Assess Environmental Risk" to inspect explainable factors.
            </div>
          )}

          {/* Historical Assessments Log */}
          {riskHistory.length > 0 && (
            <div className="rg-panel">
              <div className="rg-panel-header">
                <h3>Chronological Assessment History</h3>
              </div>
              <div className="rg-panel-body" style={{ padding: 0 }}>
                <div className="rg-table-wrapper">
                  <table className="rg-table">
                    <thead>
                      <tr>
                        <th>Target Area</th>
                        <th>Hazard Category</th>
                        <th>Risk Score</th>
                        <th>Risk Level</th>
                        <th>Confidence</th>
                        <th>Assessed At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {riskHistory.map((h) => (
                        <tr key={h.id}>
                          <td>{h.target_area}</td>
                          <td>{h.hazard_type}</td>
                          <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700 }}>{h.calculated_risk_score} / 100</td>
                          <td>
                            <span className={`rg-pill ${h.risk_level === 'Critical' ? 'rg-pill-critical' : h.risk_level === 'High' ? 'rg-pill-severe' : 'rg-pill-moderate'}`}>
                              {h.risk_level}
                            </span>
                          </td>
                          <td>{Math.round(h.confidence_score * 100)}%</td>
                          <td style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>{new Date(h.assessed_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================================== */}
      {/* TAB 2: AI Disaster Intelligence Agent                                          */}
      {/* ============================================================================== */}
      {activeTab === 'ai_agent' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Action Header */}
          <div className="rg-panel" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ margin: '0 0 4px 0' }}>AgentCraft Autonomous Disaster Reasoning</h3>
              <p style={{ margin: 0, fontSize: '12px', color: 'var(--rg-text-secondary)' }}>
                Inspects real incidents, readiness rosters, shelter saturation, and generates actionable response proposals.
              </p>
            </div>
            <button
              className="rg-btn rg-btn-primary"
              onClick={handleRunAgentAnalysis}
              disabled={runningAgent}
            >
              {runningAgent ? 'Synthesizing Situation...' : '⚡ Run Situational Intelligence Analysis'}
            </button>
          </div>

          {runningAgent ? (
            <LoadingState message="Dispatching tool queries across incidents, teams, shelters, and supplies..." />
          ) : agentAnalysis ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Provider Info Pill */}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                <span className="rg-pill rg-pill-active">PROVIDER: {agentAnalysis.ai_provider.provider.toUpperCase()}</span>
                <span style={{ fontSize: '12px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                  MODEL: {agentAnalysis.ai_provider.model}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--rg-text-muted)', marginLeft: 'auto' }}>
                  Analysis ID: {agentAnalysis.analysis_id}
                </span>
              </div>

              {/* Situation Summary Card */}
              <div className="rg-panel" style={{ padding: '16px', borderLeft: '4px solid var(--rg-olive-light)' }}>
                <h4 style={{ margin: '0 0 8px 0', color: 'var(--rg-olive-light)' }}>AI Evidence-Based Situation Summary</h4>
                <p style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--rg-text-primary)', margin: 0 }}>
                  {agentAnalysis.situation_summary}
                </p>
              </div>

              {/* Priority Incidents Ranking */}
              <div className="rg-panel">
                <div className="rg-panel-header">
                  <h3>Ranked Incident Priority Triage</h3>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                    SORTED BY COMPOUND ENVIRONMENTAL RISK SCORE
                  </span>
                </div>
                <div className="rg-panel-body" style={{ padding: 0 }}>
                  <div className="rg-table-wrapper">
                    <table className="rg-table">
                      <thead>
                        <tr>
                          <th>Rank</th>
                          <th>Incident Code</th>
                          <th>Title</th>
                          <th>Hazard Category</th>
                          <th>Calculated Risk</th>
                          <th>Hazard Level</th>
                          <th>Reported Severity</th>
                          <th>Affected Pop</th>
                        </tr>
                      </thead>
                      <tbody>
                        {agentAnalysis.priority_incidents_ranked.map((inc, index) => (
                          <tr key={inc.id || index}>
                            <td style={{ fontWeight: 800, fontFamily: 'var(--rg-font-mono)' }}>#{index + 1}</td>
                            <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{inc.incident_code}</td>
                            <td style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{inc.title}</td>
                            <td>{inc.category}</td>
                            <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700 }}>{inc.calculated_risk_score} / 100</td>
                            <td>
                              <span className={`rg-pill ${inc.risk_level === 'Critical' ? 'rg-pill-critical' : inc.risk_level === 'High' ? 'rg-pill-severe' : 'rg-pill-moderate'}`}>
                                {inc.risk_level}
                              </span>
                            </td>
                            <td>{inc.reported_severity}</td>
                            <td>{(inc.affected_population || 0).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Shortages and Bottlenecks */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                <div className="rg-panel">
                  <div className="rg-panel-header">
                    <h4>Stockpile Resource Shortages</h4>
                  </div>
                  <div className="rg-panel-body">
                    {agentAnalysis.resource_shortages && agentAnalysis.resource_shortages.length > 0 ? (
                      agentAnalysis.resource_shortages.map((item, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '12px', borderBottom: '1px solid var(--rg-border-subtle)', paddingBottom: '6px' }}>
                          <span style={{ fontWeight: 600 }}>{item.name}</span>
                          <span style={{ color: 'var(--rg-red-light)', fontFamily: 'var(--rg-font-mono)' }}>
                            {item.available} {item.unit} ({item.availability_pct}% left)
                          </span>
                        </div>
                      ))
                    ) : (
                      <div style={{ fontSize: '12px', color: 'var(--rg-olive-light)' }}>✓ Stockpile inventories currently above 25% threshold.</div>
                    )}
                  </div>
                </div>

                <div className="rg-panel">
                  <div className="rg-panel-header">
                    <h4>Coordination & Capacity Constraints</h4>
                  </div>
                  <div className="rg-panel-body" style={{ fontSize: '13px' }}>
                    <div style={{ marginBottom: '6px' }}>
                      <strong>Available Response Teams:</strong> {agentAnalysis.coordination_constraints.available_teams_count} units ready
                    </div>
                    <div style={{ marginBottom: '6px' }}>
                      <strong>Unassigned Pending Tasks:</strong> {agentAnalysis.coordination_constraints.unassigned_tasks_count} tasks awaiting units
                    </div>
                    <div style={{ marginBottom: '6px' }}>
                      <strong>Shelters &gt;= 80% Occupancy:</strong> {agentAnalysis.coordination_constraints.crowded_shelters.length > 0 ? agentAnalysis.coordination_constraints.crowded_shelters.join(', ') : 'None (capacities nominal)'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommended Response Plan & Human Approval Gate */}
              <div className="rg-panel" style={{ border: '1px solid var(--rg-amber-base)' }}>
                <div className="rg-panel-header" style={{ backgroundColor: 'var(--rg-bg-surface)' }}>
                  <h3 style={{ color: 'var(--rg-amber-light)' }}>Recommended Response Plan (Decision Gate)</h3>
                  <span className={`rg-pill ${agentAnalysis.decision_gate.approval_status === 'approved' ? 'rg-pill-active' : agentAnalysis.decision_gate.approval_status === 'rejected' ? 'rg-pill-critical' : 'rg-pill-severe'}`}>
                    GATE: {agentAnalysis.decision_gate.approval_status.toUpperCase()}
                  </span>
                </div>
                <div className="rg-panel-body">
                  <div style={{ backgroundColor: 'var(--rg-bg-inset)', padding: '12px', borderRadius: '4px', marginBottom: '16px', fontSize: '13px', lineHeight: '1.5' }}>
                    <strong>Strategic Rationale:</strong> {agentAnalysis.recommended_response_plan.rationale}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <h4 style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '6px' }}>RECOMMENDED TEAMS TO DISPATCH:</h4>
                      <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px' }}>
                        {agentAnalysis.recommended_response_plan.recommended_teams.map((t, idx) => (
                          <li key={idx} style={{ marginBottom: '4px', fontWeight: 600, color: 'var(--rg-text-primary)' }}>{t}</li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '6px' }}>ACTIONABLE TASKS:</h4>
                      <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px' }}>
                        {agentAnalysis.recommended_response_plan.recommended_tasks.map((tk, idx) => (
                          <li key={idx} style={{ marginBottom: '4px' }}>
                            {tk.title} <span className="rg-pill rg-pill-moderate" style={{ fontSize: '10px' }}>{tk.priority}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', marginBottom: '6px' }}>SHELTER DIRECTIVES:</h4>
                      <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '12px' }}>
                        {agentAnalysis.recommended_response_plan.shelter_actions.map((act, idx) => (
                          <li key={idx} style={{ marginBottom: '4px' }}>{act}</li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Operational Decision Gate Controls */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--rg-border-subtle)', flexWrap: 'wrap', gap: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)', maxWidth: '600px' }}>
                      ⚠️ <strong>AGENTCRAFT 2026 Directive:</strong> {agentAnalysis.decision_gate.disclaimer}
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        className="rg-btn rg-btn-secondary"
                        onClick={() => handleOpenApproval(false)}
                        disabled={agentAnalysis.decision_gate.approval_status === 'approved'}
                      >
                        Reject Proposal
                      </button>
                      <button
                        className="rg-btn rg-btn-primary"
                        onClick={() => handleOpenApproval(true)}
                        disabled={agentAnalysis.decision_gate.approval_status === 'approved'}
                      >
                        {agentAnalysis.decision_gate.approval_status === 'approved' ? '✓ Plan Approved' : 'Approve Plan & Authorize'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rg-panel" style={{ padding: '30px', textAlign: 'center', color: 'var(--rg-text-muted)' }}>
              Click "Run Situational Intelligence Analysis" to synthesize operational recommendations.
            </div>
          )}
        </div>
      )}

      {/* ============================================================================== */}
      {/* TAB 3: Disaster Scenario Simulations                                           */}
      {/* ============================================================================== */}
      {activeTab === 'simulations' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Preset Selector */}
          <div className="rg-panel" style={{ padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px 0' }}>Select Hypothetical Emergency Scenario</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
              {SCENARIO_PRESETS.map((preset) => (
                <div
                  key={preset.id}
                  onClick={() => {
                    setSelectedScenario(preset);
                    setSimParams(preset.defaultParams);
                  }}
                  style={{
                    padding: '12px',
                    borderRadius: 'var(--rg-radius-md)',
                    border: selectedScenario.id === preset.id ? '2px solid var(--rg-olive-light)' : '1px solid var(--rg-border-subtle)',
                    backgroundColor: selectedScenario.id === preset.id ? 'var(--rg-bg-hover)' : 'var(--rg-bg-inset)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontWeight: 600, color: 'var(--rg-text-primary)', marginBottom: '4px' }}>{preset.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-secondary)', lineHeight: '1.4' }}>{preset.desc}</div>
                </div>
              ))}
            </div>

            {/* Parameter Adjustment Controls */}
            <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--rg-border-subtle)', display: 'flex', gap: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
              {selectedScenario.id === 'heavy_rainfall' && (
                <>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', display: 'block', marginBottom: '4px' }}>
                      Rainfall Intensity (mm): {simParams.rainfall_mm}mm
                    </label>
                    <input
                      type="range"
                      min="20"
                      max="250"
                      step="10"
                      value={simParams.rainfall_mm || 120}
                      onChange={(e) => setSimParams((p) => ({ ...p, rainfall_mm: Number(e.target.value) }))}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', display: 'block', marginBottom: '4px' }}>
                      Duration (Hours): {simParams.duration_hours}h
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="24"
                      value={simParams.duration_hours || 6}
                      onChange={(e) => setSimParams((p) => ({ ...p, duration_hours: Number(e.target.value) }))}
                    />
                  </div>
                </>
              )}

              {selectedScenario.id === 'multi_incident' && (
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', display: 'block', marginBottom: '4px' }}>
                    Concurrent Incidents Count: {simParams.concurrent_incidents_count}
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="10"
                    value={simParams.concurrent_incidents_count || 5}
                    onChange={(e) => setSimParams((p) => ({ ...p, concurrent_incidents_count: Number(e.target.value) }))}
                  />
                </div>
              )}

              {selectedScenario.id === 'shelter_surge' && (
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--rg-text-secondary)', display: 'block', marginBottom: '4px' }}>
                    Incoming Displaced Evacuees: {simParams.incoming_evacuees?.toLocaleString()}
                  </label>
                  <input
                    type="range"
                    min="500"
                    max="6000"
                    step="250"
                    value={simParams.incoming_evacuees || 2500}
                    onChange={(e) => setSimParams((p) => ({ ...p, incoming_evacuees: Number(e.target.value) }))}
                  />
                </div>
              )}

              <button
                className="rg-btn rg-btn-primary"
                style={{ marginLeft: 'auto' }}
                onClick={handleRunSimulation}
                disabled={runningSim}
              >
                {runningSim ? 'Running Simulation...' : '⚡ Execute Scenario Simulation'}
              </button>
            </div>
          </div>

          {/* Simulation Output Card */}
          {runningSim ? (
            <LoadingState message="Modeling hydraulic stress and operational elasticity curves..." />
          ) : simResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ backgroundColor: 'var(--rg-amber-muted)', border: '1px solid var(--rg-amber-base)', padding: '10px 14px', borderRadius: 'var(--rg-radius-sm)', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="rg-pulse-dot warning" />
                <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--rg-amber-light)' }}>
                  [SIMULATION RUN REPORT — STRICT STATE ISOLATION ENFORCED: ZERO REAL-WORLD DISPATCHES]
                </span>
                <button
                  className="rg-btn rg-btn-secondary"
                  style={{ marginLeft: 'auto', fontSize: '11px', padding: '3px 8px' }}
                  onClick={() => setSimResult(null)}
                >
                  Reset Results
                </button>
              </div>

              {/* Simulation Metrics & Bottlenecks */}
              <div className="rg-panel">
                <div className="rg-panel-header">
                  <h3>Projected Impacts & Identified Bottlenecks</h3>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-text-muted)' }}>
                    {simResult.scenario_name}
                  </span>
                </div>
                <div className="rg-panel-body">
                  <div style={{ marginBottom: '16px' }}>
                    <h4 style={{ fontSize: '13px', color: 'var(--rg-red-light)', marginBottom: '8px' }}>
                      Identified Operational Constraints & Shortfalls:
                    </h4>
                    <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--rg-text-primary)' }}>
                      {(simResult.projected_impact.bottlenecks || []).map((b, i) => (
                        <li key={i} style={{ marginBottom: '6px' }}>{b}</li>
                      ))}
                    </ul>
                  </div>

                  {simResult.projected_impact.impacted_sectors && (
                    <div className="rg-table-wrapper" style={{ marginTop: '16px' }}>
                      <table className="rg-table">
                        <thead>
                          <tr>
                            <th>Incident Sector</th>
                            <th>Baseline Score</th>
                            <th>Simulated Score</th>
                            <th>Risk Delta</th>
                            <th>Simulated Level</th>
                            <th>Evacuation Demand</th>
                          </tr>
                        </thead>
                        <tbody>
                          {simResult.projected_impact.impacted_sectors.map((sec, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600 }}>{sec.title}</td>
                              <td style={{ fontFamily: 'var(--rg-font-mono)' }}>{sec.baseline_risk_score}</td>
                              <td style={{ fontFamily: 'var(--rg-font-mono)', fontWeight: 700, color: 'var(--rg-red-light)' }}>
                                {sec.projected_risk_score}
                              </td>
                              <td style={{ fontFamily: 'var(--rg-font-mono)', color: 'var(--rg-amber-light)' }}>
                                +{sec.risk_delta}
                              </td>
                              <td>
                                <span className="rg-pill rg-pill-critical">{sec.projected_risk_level}</span>
                              </td>
                              <td>{sec.projected_evacuation_demand.toLocaleString()} residents</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {simResult.projected_impact.shelter_breakdown && (
                    <div className="rg-table-wrapper" style={{ marginTop: '16px' }}>
                      <table className="rg-table">
                        <thead>
                          <tr>
                            <th>Shelter Name</th>
                            <th>Capacity</th>
                            <th>Current Occupancy</th>
                            <th>Projected Occupancy</th>
                            <th>Projected %</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {simResult.projected_impact.shelter_breakdown.map((sh, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600 }}>{sh.shelter_name}</td>
                              <td>{sh.nominal_capacity}</td>
                              <td>{sh.current_occupancy}</td>
                              <td style={{ fontWeight: 700 }}>{sh.projected_occupancy}</td>
                              <td>{sh.projected_occupancy_pct}%</td>
                              <td>
                                <span className={`rg-pill ${sh.status === 'at_capacity' ? 'rg-pill-critical' : 'rg-pill-moderate'}`}>
                                  {sh.status.toUpperCase()}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="rg-panel" style={{ padding: '30px', textAlign: 'center', color: 'var(--rg-text-muted)' }}>
              Select a scenario preset above and click "Execute Scenario Simulation" to model stress responses.
            </div>
          )}

          {/* Historical Simulation Runs Table */}
          {simHistory.length > 0 && (
            <div className="rg-panel">
              <div className="rg-panel-header">
                <h3>Historical Simulation Audit Log</h3>
              </div>
              <div className="rg-panel-body" style={{ padding: 0 }}>
                <div className="rg-table-wrapper">
                  <table className="rg-table">
                    <thead>
                      <tr>
                        <th>Scenario Name</th>
                        <th>Type</th>
                        <th>Run By</th>
                        <th>Simulated Timestamp</th>
                      </tr>
                    </thead>
                    <tbody>
                      {simHistory.map((s) => (
                        <tr key={s.id}>
                          <td style={{ fontWeight: 600, color: 'var(--rg-text-primary)' }}>{s.scenario_name}</td>
                          <td>
                            <span className="rg-pill rg-pill-moderate">{s.scenario_type}</span>
                          </td>
                          <td style={{ fontSize: '12px' }}>{s.created_by}</td>
                          <td style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>{new Date(s.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ============================================================================== */}
      {/* TAB 4: External Integrations & Telemetry Health                                */}
      {/* ============================================================================== */}
      {activeTab === 'external_data' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Health Diagnostics Panel */}
          <div className="rg-panel" style={{ padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px 0' }}>External Provider Connectivity Status</h3>
            {externalHealth ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: 'var(--rg-radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>PROVIDER CLASS</div>
                  <div style={{ fontWeight: 700, fontSize: '14px', marginTop: '4px' }}>{externalHealth.provider_type}</div>
                </div>
                <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: 'var(--rg-radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>NETWORK ACCESS</div>
                  <div style={{ fontWeight: 700, fontSize: '14px', marginTop: '4px', color: externalHealth.network_enabled ? 'var(--rg-olive-light)' : 'var(--rg-amber-light)' }}>
                    {externalHealth.network_enabled ? 'ONLINE (Live Fetch Enabled)' : 'OFFLINE (Fallback Adapter)'}
                  </div>
                </div>
                <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: 'var(--rg-radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>CACHE TTL / CAPACITY</div>
                  <div style={{ fontWeight: 700, fontSize: '14px', marginTop: '4px' }}>
                    {externalHealth.cache_ttl_seconds}s TTL ({externalHealth.cached_entries_count} entries)
                  </div>
                </div>
                <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '12px', borderRadius: 'var(--rg-radius-sm)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--rg-text-muted)' }}>STATUS</div>
                  <div style={{ fontWeight: 700, fontSize: '14px', marginTop: '4px', color: 'var(--rg-olive-light)' }}>
                    {externalHealth.status.toUpperCase()}
                  </div>
                </div>
              </div>
            ) : (
              <LoadingState message="Querying provider telemetry..." />
            )}
          </div>

          {/* Coordinates Telemetry Inspector */}
          <div className="rg-panel" style={{ padding: '16px' }}>
            <h3 style={{ margin: '0 0 12px 0' }}>Live Coordinates Meteorological & Flood Inspector</h3>
            <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '16px' }}>
              <div>
                <label style={{ fontSize: '11px', color: 'var(--rg-text-muted)', display: 'block', marginBottom: '4px' }}>Latitude:</label>
                <input
                  type="text"
                  value={inspectLat}
                  onChange={(e) => setInspectLat(e.target.value)}
                  style={{
                    backgroundColor: 'var(--rg-bg-inset)',
                    color: 'var(--rg-text-primary)',
                    border: '1px solid var(--rg-border-subtle)',
                    padding: '8px 12px',
                    borderRadius: 'var(--rg-radius-sm)',
                    fontSize: '13px',
                    width: '120px',
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--rg-text-muted)', display: 'block', marginBottom: '4px' }}>Longitude:</label>
                <input
                  type="text"
                  value={inspectLon}
                  onChange={(e) => setInspectLon(e.target.value)}
                  style={{
                    backgroundColor: 'var(--rg-bg-inset)',
                    color: 'var(--rg-text-primary)',
                    border: '1px solid var(--rg-border-subtle)',
                    padding: '8px 12px',
                    borderRadius: 'var(--rg-radius-sm)',
                    fontSize: '13px',
                    width: '120px',
                  }}
                />
              </div>

              <button
                className="rg-btn rg-btn-primary"
                style={{ marginTop: '16px' }}
                onClick={handleInspectTelemetry}
                disabled={inspectingTelemetry}
              >
                {inspectingTelemetry ? 'Querying Open-Meteo...' : 'Fetch Live Observations'}
              </button>
            </div>

            {inspectResult && (
              <div style={{ backgroundColor: 'var(--rg-bg-card)', padding: '16px', borderRadius: 'var(--rg-radius-md)', border: '1px solid var(--rg-border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span className="rg-pill rg-pill-active">
                    STATUS: {inspectResult.weather?.status?.toUpperCase()}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--rg-text-muted)' }}>
                    Retrieved: {new Date(inspectResult.weather?.retrieval_time).toLocaleString()}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', fontSize: '13px' }}>
                  <div><strong>Condition:</strong> {inspectResult.weather?.weather_description}</div>
                  <div><strong>Temperature:</strong> {inspectResult.weather?.temperature_c} °C</div>
                  <div><strong>Precipitation:</strong> {inspectResult.weather?.precipitation_mm} mm</div>
                  <div><strong>Wind Speed:</strong> {inspectResult.weather?.wind_speed_kmh} km/h</div>
                  <div><strong>River Discharge:</strong> {inspectResult.flood?.river_discharge_m3s ?? 'N/A'} m³/s</div>
                  <div><strong>Flood Risk Level:</strong> <span style={{ textTransform: 'capitalize' }}>{inspectResult.flood?.flood_risk_level ?? 'N/A'}</span></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Human Approval Decision Gate Modal */}
      <ModalDialog isOpen={approvalModal} onClose={() => setApprovalModal(false)} title="Operational Decision Gate — Response Plan Confirmation">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span className={`rg-pulse-dot ${approvalDecision ? 'nominal' : 'warning'}`} />
            <strong style={{ color: approvalDecision ? 'var(--rg-olive-light)' : 'var(--rg-red-light)' }}>
              {approvalDecision ? 'Confirming Tactical Plan Authorization' : 'Recording Tactical Plan Rejection'}
            </strong>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--rg-text-secondary)', marginBottom: '12px' }}>
            {approvalDecision
              ? 'Authorizing this plan logs commander sign-off on recommended teams, task staging, and shelter directives.'
              : 'Rejecting this plan marks it as rejected in the traceable audit log and notifies dispatchers.'}
          </p>
          <textarea
            rows={3}
            value={approvalNotes}
            onChange={(e) => setApprovalNotes(e.target.value)}
            placeholder="Operational justification or commander notes..."
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
            <button className="rg-btn rg-btn-secondary" onClick={() => setApprovalModal(false)}>
              Cancel
            </button>
            <button
              className={`rg-btn ${approvalDecision ? 'rg-btn-primary' : 'rg-btn-danger'}`}
              disabled={approvalSaving}
              onClick={handleConfirmApproval}
            >
              {approvalSaving ? 'Submitting...' : approvalDecision ? 'Authorize Plan' : 'Confirm Rejection'}
            </button>
          </div>
        </div>
      </ModalDialog>
    </>
  );
}
