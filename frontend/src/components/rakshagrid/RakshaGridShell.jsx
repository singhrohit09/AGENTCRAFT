import React, { useState, useEffect, useCallback } from 'react';
import '../../rakshagrid.css';
import RakshaHeader from './RakshaHeader';
import RakshaSidebar from './RakshaSidebar';
import RakshaOverview from './RakshaOverview';
import RakshaIncidents from './RakshaIncidents';
import RakshaLiveMap from './RakshaLiveMap';
import RakshaAlerts from './RakshaAlerts';
import RakshaTeams from './RakshaTeams';
import RakshaTasks from './RakshaTasks';
import RakshaShelters from './RakshaShelters';
import RakshaResources from './RakshaResources';
import RakshaRiskAnalysis from './RakshaRiskAnalysis';
import RakshaAnalytics from './RakshaAnalytics';
import RakshaSettings from './RakshaSettings';

export default function RakshaGridShell({ activePlatformMode, setActivePlatformMode }) {
  const [activeSection, setActiveSection] = useState('overview');
  const [healthData, setHealthData] = useState(null);
  const [overviewData, setOverviewData] = useState(null);
  const [dbStatus, setDbStatus] = useState(null);

  const fetchTelemetry = useCallback(async () => {
    try {
      const [hRes, oRes, dbRes] = await Promise.all([
        fetch('/api/rakshagrid/health').catch(() => null),
        fetch('/api/rakshagrid/overview').catch(() => null),
        fetch('/api/rakshagrid/database/status').catch(() => null),
      ]);

      if (hRes && hRes.ok) {
        setHealthData(await hRes.json());
      }
      if (oRes && oRes.ok) {
        setOverviewData(await oRes.json());
      }
      if (dbRes && dbRes.ok) {
        setDbStatus(await dbRes.json());
      }
    } catch (e) {
      console.error('RakshaGrid telemetry synchronization error:', e);
    }
  }, []);

  useEffect(() => {
    let ignore = false;
    fetchTelemetry().then(() => {
      if (ignore) return;
    });
    return () => {
      ignore = true;
    };
  }, [fetchTelemetry]);

  const renderActiveSection = () => {
    switch (activeSection) {
      case 'overview':
        return <RakshaOverview overviewData={overviewData} onNavigate={setActiveSection} />;
      case 'incidents':
        return <RakshaIncidents />;
      case 'live-map':
        return <RakshaLiveMap />;
      case 'alerts':
        return <RakshaAlerts />;
      case 'response-teams':
        return <RakshaTeams />;
      case 'tasks':
        return <RakshaTasks />;
      case 'shelters':
        return <RakshaShelters />;
      case 'resources':
        return <RakshaResources />;
      case 'risk-analysis':
        return <RakshaRiskAnalysis />;
      case 'analytics':
        return <RakshaAnalytics />;
      case 'settings':
        return <RakshaSettings dbStatus={dbStatus} onRefreshDb={fetchTelemetry} />;
      default:
        return <RakshaOverview overviewData={overviewData} onNavigate={setActiveSection} />;
    }
  };

  return (
    <div className="rakshagrid-app">
      <RakshaHeader
        healthData={healthData}
        activePlatformMode={activePlatformMode}
        setActivePlatformMode={setActivePlatformMode}
        onRefresh={fetchTelemetry}
      />
      <div className="rg-layout-body">
        <RakshaSidebar
          activeSection={activeSection}
          onSelectSection={setActiveSection}
          dbStatus={dbStatus}
        />
        <main className="rg-content-area">
          {renderActiveSection()}
        </main>
      </div>
    </div>
  );
}
