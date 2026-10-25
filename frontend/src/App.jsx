import React, { useState, useEffect, useRef, useCallback } from 'react';
import RakshaGridShell from './components/rakshagrid/RakshaGridShell';

const PRESET_GOALS = [
  {
    label: 'Data Outlier Pipeline',
    goal: 'Analyze dataset of agents, detect latency outliers, and generate summary report',
  },
  {
    label: 'Algorithmic Invariant Check',
    goal: 'Compute mathematical fibonacci sequence and verify output',
  },
  {
    label: 'Domain Research & Acceptance',
    goal: 'Retrieve domain knowledge for AgentCraft architecture and verify acceptance gates',
  },
];

export default function App() {
  const [platformMode, setPlatformMode] = useState('rakshagrid'); // 'rakshagrid' | 'agentcraft'
  const [goal, setGoal] = useState(PRESET_GOALS[0].goal);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('terminal'); // 'terminal' | 'trace' | 'memory' | 'benchmark' | 'tools'
  const [systemHealth, setSystemHealth] = useState(null);
  const [session, setSession] = useState(null);
  const [plan, setPlan] = useState([]);
  const [logs, setLogs] = useState([]);
  const [executionTrace, setExecutionTrace] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [_memory, setMemory] = useState({});
  const [metrics, setMetrics] = useState({
    total_steps: 0,
    completed_steps: 0,
    tool_calls: 0,
    retries: 0,
    verifications_passed: 0,
    verifications_failed: 0,
    total_duration_ms: 0,
  });
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [registeredTools, setRegisteredTools] = useState([]);
  const [stepModeActive, setStepModeActive] = useState(false);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  const terminalRef = useRef(null);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      }
    } catch {
      setSystemHealth({ status: 'offline', message: 'Backend unreachable on port 8000' });
    }
  }, []);

  const fetchTools = useCallback(async () => {
    try {
      const res = await fetch('/api/agent/tools');
      if (res.ok) {
        const data = await res.json();
        setRegisteredTools(data.tools || []);
      }
    } catch (e) {
      console.error('Failed to fetch tools:', e);
    }
  }, []);

  // Poll backend health on startup and fetch tools
  useEffect(() => {
    fetchHealth();
    fetchTools();
  }, [fetchHealth, fetchTools]);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const handleRunAutonomous = async () => {
    if (!goal.trim() || isRunning) return;

    setIsRunning(true);
    setStepModeActive(false);
    setLogs((prev) => [...prev, `[INIT] Dispatching autonomous run for goal: "${goal}"`]);

    try {
      const res = await fetch('/api/agent/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      setSession(data);
      setPlan(data.plan || []);
      setExecutionTrace(data.execution_trace || []);
      setLogs(data.logs || []);
      setArtifacts(data.artifacts || []);
      setMetrics(data.metrics || {});
      if (data.final_output) {
        setLogs((prev) => [...prev, `[SUCCESS] ${data.final_output.summary}`]);
      }
    } catch (err) {
      setLogs((prev) => [...prev, `[ERROR] Execution failed: ${err.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStartStepMode = async () => {
    if (!goal.trim() || isRunning) return;

    setIsRunning(true);
    try {
      // 1. Create session
      const createRes = await fetch('/api/agent/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal }),
      });
      const sessionData = await createRes.json();
      const sId = sessionData.session_id;

      // 2. Generate plan
      const planRes = await fetch(`/api/agent/sessions/${sId}/plan`, { method: 'POST' });
      const planData = await planRes.json();

      setSession({ session_id: sId, goal, status: 'planning' });
      setPlan(planData.plan || []);
      setLogs([`[STEP_MODE] Session ${sId} initialized with ${planData.total_steps} planned steps.`]);
      setStepModeActive(true);
      setCurrentStepIdx(0);
    } catch (err) {
      setLogs((prev) => [...prev, `[ERROR] Failed to start step mode: ${err.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleExecuteNextStep = async () => {
    if (!session?.session_id || currentStepIdx >= plan.length || isRunning) return;

    setIsRunning(true);
    try {
      const res = await fetch(`/api/agent/sessions/${session.session_id}/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step_index: currentStepIdx }),
      });

      const data = await res.json();
      const updatedStep = data.step;

      // Update plan step state
      setPlan((prev) =>
        prev.map((s, idx) => (idx === currentStepIdx ? updatedStep : s))
      );

      // Fetch fresh session details
      const detailRes = await fetch(`/api/agent/sessions/${session.session_id}`);
      const freshData = await detailRes.json();
      setExecutionTrace(freshData.execution_trace || []);
      setLogs(freshData.logs || []);
      setArtifacts(freshData.artifacts || []);
      setMetrics(freshData.metrics || {});
      setMemory(freshData.memory || {});

      setCurrentStepIdx((prev) => prev + 1);
    } catch (err) {
      setLogs((prev) => [...prev, `[ERROR] Step execution failed: ${err.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunBenchmark = async () => {
    setIsRunning(true);
    setActiveTab('benchmark');
    try {
      const res = await fetch('/api/agent/benchmark', { method: 'POST' });
      const data = await res.json();
      setBenchmarkResult(data);
      setLogs((prev) => [
        ...prev,
        `[BENCHMARK] Suite Completed: ${data.passed_tasks}/${data.total_tasks} Tasks Passed (${data.completion_rate_pct}%). Status: ${data.system_verdict}`,
      ]);
    } catch (err) {
      setLogs((prev) => [...prev, `[ERROR] Benchmark run failed: ${err.message}`]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleReset = () => {
    setPlan([]);
    setExecutionTrace([]);
    setArtifacts([]);
    setLogs([]);
    setMemory({});
    setSession(null);
    setStepModeActive(false);
    setCurrentStepIdx(0);
    setMetrics({
      total_steps: 0,
      completed_steps: 0,
      tool_calls: 0,
      retries: 0,
      verifications_passed: 0,
      verifications_failed: 0,
      total_duration_ms: 0,
    });
  };

  if (platformMode === 'rakshagrid') {
    return (
      <RakshaGridShell
        activePlatformMode={platformMode}
        setActivePlatformMode={setPlatformMode}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="brand-wrapper">
          <div className="brand-logo-badge">AC</div>
          <div>
            <h1 className="brand-title">AgentCraft</h1>
            <p className="brand-subtitle">AGENTCRAFT 2026 National AI Agent Challenge</p>
          </div>
        </div>

        <div className="header-status-group">
          <button
            className="btn-secondary"
            onClick={() => setPlatformMode('rakshagrid')}
            style={{
              borderColor: 'var(--color-emerald)',
              color: 'var(--color-emerald)',
              fontWeight: 600,
            }}
          >
            ← Switch to RakshaGrid
          </button>
          <div className="status-pill">
            <span className="pulse-dot"></span>
            <span>{systemHealth?.status === 'healthy' ? 'Agent Engine Online' : 'Connecting Engine...'}</span>
          </div>
          <div className="status-pill">
            <span>Mode: {systemHealth?.execution_mode || 'hybrid'}</span>
          </div>
          <button className="btn-secondary" onClick={handleRunBenchmark} disabled={isRunning} id="run-benchmarks-header-btn">
            Run Benchmark Suite
          </button>
        </div>
      </header>

      {/* Metrics Row */}
      <section className="metrics-grid">
        <div className="metric-card">
          <span className="metric-title">Completed Steps</span>
          <span className="metric-value cyan">
            {metrics.completed_steps} / {metrics.total_steps || plan.length}
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-title">Tool Calls</span>
          <span className="metric-value purple">{metrics.tool_calls}</span>
        </div>
        <div className="metric-card">
          <span className="metric-title">Verifications Passed</span>
          <span className="metric-value emerald">{metrics.verifications_passed}</span>
        </div>
        <div className="metric-card">
          <span className="metric-title">Recovery Retries</span>
          <span className="metric-value amber">{metrics.retries}</span>
        </div>
        <div className="metric-card">
          <span className="metric-title">Execution Latency</span>
          <span className="metric-value">{Math.round(metrics.total_duration_ms)} ms</span>
        </div>
      </section>

      {/* Goal & Mission Control */}
      <section className="control-card">
        <div className="section-header">
          <h2 className="section-title">Mission Control & Goal Specification</h2>
          <div className="preset-chips">
            {PRESET_GOALS.map((p, i) => (
              <button
                key={i}
                className="chip-btn"
                onClick={() => setGoal(p.goal)}
                disabled={isRunning}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        <div className="input-group">
          <input
            type="text"
            className="goal-input"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Specify autonomous agent task or workflow goal..."
            disabled={isRunning}
            id="agent-goal-input"
          />
          <button
            className="btn-primary"
            onClick={handleRunAutonomous}
            disabled={isRunning || !goal.trim()}
            id="run-autonomous-btn"
          >
            {isRunning && !stepModeActive ? 'Executing Plan...' : 'Run Autonomous Agent'}
          </button>
          {!stepModeActive ? (
            <button
              className="btn-secondary"
              onClick={handleStartStepMode}
              disabled={isRunning || !goal.trim()}
              id="start-step-mode-btn"
            >
              Step Mode
            </button>
          ) : (
            <button
              className="btn-primary"
              onClick={handleExecuteNextStep}
              disabled={isRunning || currentStepIdx >= plan.length}
              id="next-step-btn"
            >
              Execute Next Step ({currentStepIdx + 1}/{plan.length})
            </button>
          )}
          <button className="btn-secondary" onClick={handleReset} disabled={isRunning} id="reset-btn">
            Reset
          </button>
        </div>
      </section>

      {/* Main Workspace Layout */}
      <main className="workspace-grid">
        {/* Left Column: Multi-Step Plan Timeline */}
        <section className="control-card">
          <div className="section-header">
            <h3 className="section-title">Execution Plan ({plan.length} Steps)</h3>
            {session?.session_id && (
              <span className="tool-tag">Session: {session.session_id}</span>
            )}
          </div>

          <div className="plan-timeline">
            {plan.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', padding: '24px 0', textAlign: 'center' }}>
                No active execution plan. Enter a goal above and click "Run Autonomous Agent" or "Step Mode".
              </p>
            ) : (
              plan.map((step, idx) => (
                <div key={idx} className={`step-card ${step.status}`}>
                  <div className="step-header">
                    <div className="step-index-title">
                      <div className="step-badge">{step.step_id}</div>
                      <span className="step-title">{step.title}</span>
                    </div>
                    <div className="step-meta">
                      <span className="tool-tag">{step.tool_name}</span>
                      <span
                        style={{
                          textTransform: 'uppercase',
                          fontWeight: 700,
                          fontSize: '11px',
                          color:
                            step.status === 'succeeded'
                              ? 'var(--color-emerald)'
                              : step.status === 'running'
                              ? 'var(--color-cyan)'
                              : step.status === 'failed'
                              ? 'var(--color-rose)'
                              : 'var(--text-muted)',
                        }}
                      >
                        {step.status}
                      </span>
                    </div>
                  </div>

                  <p className="step-description">{step.description}</p>

                  {step.verification && (
                    <div style={{ fontSize: '12px', color: 'var(--color-emerald)', marginTop: '4px' }}>
                      ✓ Verified: {step.verification.passed_count}/{step.verification.total_assertions} assertions passed
                    </div>
                  )}

                  {step.error && (
                    <div style={{ fontSize: '12px', color: 'var(--color-rose)', marginTop: '4px' }}>
                      Error: {step.error} (Retries: {step.retries})
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </section>

        {/* Right Column: Inspector & Telemetry */}
        <section className="control-card">
          <div className="tabs-nav">
            <button
              className={`tab-btn ${activeTab === 'terminal' ? 'active' : ''}`}
              onClick={() => setActiveTab('terminal')}
              id="tab-terminal-btn"
            >
              Terminal Stream ({logs.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'trace' ? 'active' : ''}`}
              onClick={() => setActiveTab('trace')}
              id="tab-trace-btn"
            >
              Audit Trace ({executionTrace.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'artifacts' ? 'active' : ''}`}
              onClick={() => setActiveTab('artifacts')}
              id="tab-artifacts-btn"
            >
              Artifacts ({artifacts.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
              onClick={() => setActiveTab('benchmark')}
              id="tab-benchmark-btn"
            >
              Benchmark Suite
            </button>
            <button
              className={`tab-btn ${activeTab === 'tools' ? 'active' : ''}`}
              onClick={() => setActiveTab('tools')}
              id="tab-tools-btn"
            >
              Registered Tools ({registeredTools.length})
            </button>
          </div>

          {/* Terminal Window */}
          {activeTab === 'terminal' && (
            <div className="terminal-window" ref={terminalRef} id="agent-terminal-window">
              {logs.length === 0 ? (
                <div style={{ color: 'var(--text-muted)' }}>
                  Terminal standby. Execution logs, tool calls, and verifications will appear here in real-time.
                </div>
              ) : (
                logs.map((line, i) => {
                  let cls = 'log-line';
                  if (line.includes('[ERROR]') || line.includes('failed')) cls += ' error';
                  else if (line.includes('[SUCCESS]') || line.includes('successfully') || line.includes('verified'))
                    cls += ' success';
                  else if (line.includes('[INIT]') || line.includes('Executing')) cls += ' warning';
                  return (
                    <div key={i} className={cls}>
                      {line}
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* Audit Trace Tab */}
          {activeTab === 'trace' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '440px', overflowY: 'auto' }}>
              {executionTrace.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No execution trace records recorded yet.</p>
              ) : (
                executionTrace.map((rec, i) => (
                  <div key={i} style={{ background: 'var(--bg-terminal)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <strong style={{ color: 'var(--color-cyan)' }}>
                        Step {rec.step_id}: {rec.step_title}
                      </strong>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{Math.round(rec.duration_ms)} ms</span>
                    </div>
                    <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      <div>Tool: <code>{rec.tool_name}</code></div>
                      <div>Success: <span style={{ color: rec.success ? 'var(--color-emerald)' : 'var(--color-rose)' }}>{String(rec.success)}</span></div>
                      {rec.verification_details && (
                        <div style={{ marginTop: '4px' }}>
                          Verification: {rec.verification_details.passed_count}/{rec.verification_details.total_assertions} passed
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Artifacts Tab */}
          {activeTab === 'artifacts' && (
            <div className="artifacts-list">
              {artifacts.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No persistent artifacts produced in current run.</p>
              ) : (
                artifacts.map((art, i) => (
                  <div key={i} className="artifact-item">
                    <div>
                      <div className="artifact-name">{art.path}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Produced by Step {art.step_id}: {art.title}</div>
                    </div>
                    <span className="tool-tag">{art.type}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Benchmark Tab */}
          {activeTab === 'benchmark' && (
            <div>
              {!benchmarkResult ? (
                <div style={{ textAlign: 'center', padding: '32px 0' }}>
                  <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
                    Evaluate AgentCraft against standardized AGENTCRAFT 2026 Challenge test tasks.
                  </p>
                  <button className="btn-primary" onClick={handleRunBenchmark} disabled={isRunning} id="run-benchmarks-tab-btn">
                    Execute Evaluation Benchmark
                  </button>
                </div>
              ) : (
                <div className="benchmark-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ fontSize: '18px', fontWeight: 700 }}>{benchmarkResult.suite_name}</h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        Tested {benchmarkResult.total_tasks} benchmark tasks in {benchmarkResult.suite_duration_ms} ms
                      </p>
                    </div>
                    <div className="benchmark-badge-large">{benchmarkResult.system_verdict}</div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '12px' }}>
                    <div style={{ background: 'var(--bg-input)', padding: '10px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>COMPLETION RATE</div>
                      <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-cyan)' }}>
                        {benchmarkResult.completion_rate_pct}%
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-input)', padding: '10px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>VERIFIED CHECKS</div>
                      <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-emerald)' }}>
                        {benchmarkResult.total_verifications_passed}
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-input)', padding: '10px', borderRadius: '6px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>STEPS EXECUTED</div>
                      <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-purple)' }}>
                        {benchmarkResult.total_steps_executed}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '12px' }}>
                    <h5 style={{ fontSize: '13px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
                      Individual Task Results
                    </h5>
                    {benchmarkResult.tasks.map((t, idx) => (
                      <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '13px' }}>
                        <span>{t.title}</span>
                        <span style={{ color: t.passed ? 'var(--color-emerald)' : 'var(--color-rose)', fontWeight: 600 }}>
                          {t.passed ? 'PASSED' : 'FAILED'} ({t.duration_ms} ms)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Registered Tools Tab */}
          {activeTab === 'tools' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '440px', overflowY: 'auto' }}>
              {registeredTools.map((t, idx) => (
                <div key={idx} style={{ background: 'var(--bg-terminal)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span className="tool-tag">{t.name}</span>
                    <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{t.description}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    Parameters: {Object.keys(t.parameters?.properties || {}).join(', ') || 'None'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
