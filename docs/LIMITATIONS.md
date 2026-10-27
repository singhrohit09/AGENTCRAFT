# AgentCraft / RakshaGrid — System Limitations & Future Roadmap

This document outlines the operational boundaries, assumptions, trade-offs, and future engineering milestones for **AgentCraft / RakshaGrid**.

---

## 1. Current System Boundaries & Trade-Offs

### 1.1 External Data & Telemetry
- **API Quotas**: Real-time hydro-meteorological telemetry relies on the Open-Meteo Weather Forecast and Flood APIs. In high-traffic deployments, rate limits on public tiers could trigger fallback responses.
- **Mitigation**: The system incorporates an in-memory 15-minute Time-To-Live (TTL) cache and resilient offline heuristic fallbacks that generate estimated data when remote APIs are unreachable.

### 1.2 GIS & Cartographic Mapping
- **Tile Sources**: The Leaflet-based interactive live map currently pulls map tiles from OpenStreetMap over HTTPS.
- **Remote Field Deployments**: In disaster scenarios with complete cellular and internet blackouts, map tiles may not render without pre-cached offline tile packages. (Vector coordinates and markers continue to render accurately).

### 1.3 Emergency Warning Delivery (CAP Gateways)
- **Broadcast Reach**: Alerts conform to the Common Alerting Protocol (CAP) and are published immediately to the in-app WebSocket/REST feeds and dashboard console.
- **Telecom Carrier Integration**: Direct SMS or Cell Broadcast (CB) transmission requires integration with government telecommunications authorities and dedicated SMS gateways.

### 1.4 Sandboxed Code Execution
- **Isolation Scope**: Code execution runs in an isolated Python process namespace with standard input/output redirection and mathematical standard library modules.
- **System Calls**: Low-level networking, raw socket creation, and destructive file-system operations are strictly prohibited.

---

## 2. Failure Handling & Edge Case Safeguards

| Failure Mode | AgentCraft / RakshaGrid Safeguard |
| :--- | :--- |
| **Directory Traversal** | Path normalization checks in `FileManagerTool` ensure all operations are strictly bound within `./temp_sandbox`. |
| **AI Decision Hallucinations** | Consequential operations (dispatching teams, allocating inventory) require human commander sign-off via mandatory approval gates. |
| **Negative Inventory & Overbooking** | Check constraints (`quantity_available >= 0` and `current_occupancy <= capacity`) enforce relational consistency in atomic database transactions. |
| **Alert Notification Floods** | SHA-256 deduplication hashing with a 15-minute cooldown window suppresses redundant broadcast spikes. |
| **Simulation State Contamination** | Simulations operate exclusively on in-memory clones or decoupled query projections, ensuring zero database mutations. |
| **API Denial of Service (DoS)** | Thread-safe sliding-window rate limiters throttle sensitive intelligence and agent endpoints. |

---

## 3. Future Roadmap (AgentCraft 2.0 / Post-Challenge)

1. **Offline Map Tile Packager**: Bundle offline MBTiles / vector map caches directly within the container for deployment in deep-field disaster zones without internet connectivity.
2. **Cell Broadcast & SMS Gateway Connectors**: Native adapters for Twilio, AWS SNS, and Indian NDMA CAP-CP (Common Alerting Protocol - Integrated Early Warning System).
3. **Multi-Agent Swarm Collaboration**: Specialized agent sub-roles (e.g., Triage Agent, Logistics Routing Agent, Evacuation Modeler) operating in collaborative peer networks.
4. **Hardware-Isolated MicroVM Sandboxes**: Integration with AWS Firecracker or gVisor for arbitrary untrusted code execution.
5. **Satellite Imagery & Drone Telemetry Streaming**: Direct ingestion of GeoTIFF orthomosaics and live video stream analysis from reconnaissance drones.
