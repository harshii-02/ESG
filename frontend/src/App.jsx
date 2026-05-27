import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Check, Database, FileDown, RefreshCw, ShieldCheck, Upload } from "lucide-react";

const sources = [
  { id: "sap", label: "SAP fuel + procurement" },
  { id: "utility", label: "Utility electricity" },
  { id: "travel", label: "Corporate travel" }
];

const api = {
  async get(path) {
    const response = await fetch(path);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },
  async post(path, body) {
    const response = await fetch(path, { method: "POST", body });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  }
};

function formatNumber(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 });
}

function StatusPill({ status }) {
  return <span className={`pill ${status}`}>{status.replace("_", " ")}</span>;
}

function App() {
  const [summary, setSummary] = useState(null);
  const [activities, setActivities] = useState([]);
  const [audit, setAudit] = useState([]);
  const [failedRecords, setFailedRecords] = useState([]);
  const [source, setSource] = useState("sap");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState("all");
  const [canSeeAnalysis, setCanSeeAnalysis] = useState(false);

  async function refresh() {
    const [summaryData, activityData, auditData, failedData] = await Promise.all([
      api.get("/api/summary/"),
      api.get("/api/activities/"),
      api.get("/api/audit/"),
      api.get("/api/failed-records/")
    ]);
    setSummary(summaryData);
    setActivities(activityData);
    setAudit(auditData);
    setFailedRecords(failedData);
  }

  useEffect(() => {
    refresh().catch((error) => setMessage(error.message));
  }, []);

  async function importRows() {
    setLoading(true);
    setMessage("");
    try {
      const body = new FormData();
      if (file) body.append("file", file);
      const result = await api.post(`/api/ingest/${source}/`, body);
      const mode = file ? "Uploaded CSV" : "Built-in sample";
      setMessage(`${mode} imported: ${result.total_rows} rows, ${result.failed_rows} failed.`);
      setCanSeeAnalysis(true);
      setFile(null);
      await refresh();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function approve(id) {
    setLoading(true);
    try {
      await api.post(`/api/activities/${id}/approve/`);
      await refresh();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  const visibleActivities = useMemo(() => {
    if (filter === "all") return activities;
    if (filter === "flagged") return activities.filter((row) => row.suspicious_flags.length);
    return activities.filter((row) => row.review_status === filter);
  }, [activities, filter]);

  function seeAnalysis() {
    document.getElementById("analysis-report")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Breathe ESG prototype</p>
          <h1>Analyst ingestion review</h1>
        </div>
        <button className="icon-button" onClick={refresh} disabled={loading} title="Refresh dashboard">
          <RefreshCw size={18} />
          Refresh
        </button>
      </header>

      <section className="summary-grid">
        <Metric icon={<Database />} label="Normalized rows" value={summary?.total_rows || 0} />
        <Metric icon={<ShieldCheck />} label="Total kgCO2e" value={formatNumber(summary?.total_kg_co2e)} />
        <Metric icon={<AlertTriangle />} label="Flagged rows" value={summary?.flagged_rows || 0} tone="warn" />
        <Metric icon={<AlertTriangle />} label="Failed imports" value={summary?.failed_rows || 0} tone="danger" />
      </section>

      <section className="workspace">
        <aside className="panel import-panel">
          <h2>Data intake</h2>
          <div className="segmented">
            {sources.map((item) => (
              <button key={item.id} className={source === item.id ? "active" : ""} onClick={() => setSource(item.id)}>
                {item.label}
              </button>
            ))}
          </div>

          <label className="file-drop">
            <Upload size={24} />
            <span>{file ? file.name : "Choose a CSV file"}</span>
            <input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files[0])} />
          </label>

          <div className="import-actions">
            <button onClick={importRows} disabled={loading}>
              <Upload size={18} />
              {file ? "Import uploaded CSV" : "Import built-in sample"}
            </button>
            <a href={`/api/samples/${source}/`} className="secondary-button">
              <FileDown size={18} />
              Download sample CSV
            </a>
          </div>

          {message && <p className="message">{message}</p>}
          {canSeeAnalysis && (
            <button className="analysis-button" onClick={seeAnalysis}>
              See analysis report
            </button>
          )}

          <div className="scope-box">
            <h3>Scope totals</h3>
            {(summary?.scope_totals || []).map((row) => (
              <div className="scope-row" key={row.scope}>
                <span>{row.scope}</span>
                <strong>{formatNumber(row.kg_co2e)} kgCO2e</strong>
              </div>
            ))}
          </div>
        </aside>

        <section className="panel review-panel" id="analysis-report">
          <div className="panel-header">
            <h2>Normalized emissions report</h2>
            <div className="filters">
              {["all", "needs_review", "approved", "flagged"].map((item) => (
                <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>
                  {item.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Activity</th>
                  <th>Scope</th>
                  <th>Normalized</th>
                  <th>kgCO2e</th>
                  <th>Flags</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {visibleActivities.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>{row.batch.source_type.toUpperCase()}</strong>
                      <span>{row.facility_code || "No facility"}</span>
                    </td>
                    <td>
                      <strong>{row.description}</strong>
                      <span>{row.activity_date} · {row.supplier || "unknown supplier"}</span>
                    </td>
                    <td>{row.scope}</td>
                    <td>{formatNumber(row.normalized_quantity)} {row.normalized_unit}</td>
                    <td>{formatNumber(row.kg_co2e)}</td>
                    <td>
                      {row.suspicious_flags.length ? (
                        <div className="flags">{row.suspicious_flags.map((flag) => <span key={flag}>{flag}</span>)}</div>
                      ) : (
                        <span className="muted">Clear</span>
                      )}
                    </td>
                    <td><StatusPill status={row.review_status} /></td>
                    <td>
                      <button
                        className="approve-button"
                        disabled={row.locked_at || loading}
                        onClick={() => approve(row.id)}
                        title="Approve and lock for audit"
                      >
                        <Check size={17} />
                      </button>
                    </td>
                  </tr>
                ))}
                {!visibleActivities.length && (
                  <tr>
                    <td colSpan="8" className="empty">No rows match this filter.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </section>

      <section className="panel failed-panel">
        <h2>Failed source rows</h2>
        <div className="failed-list">
          {failedRecords.map((record) => (
            <div key={record.id} className="failed-item">
              <strong>{record.batch.source_type.toUpperCase()} row {record.row_number}</strong>
              <span>{record.error}</span>
              <code>{JSON.stringify(record.raw_payload)}</code>
            </div>
          ))}
          {!failedRecords.length && <p className="empty">No failed rows yet.</p>}
        </div>
      </section>

      <section className="panel audit-panel">
        <h2>Audit trail</h2>
        <div className="audit-list">
          {audit.map((event) => (
            <div key={event.id} className="audit-item">
              <strong>{event.event_type.replace("_", " ")}</strong>
              <span>{event.object_type} #{event.object_id} · {new Date(event.created_at).toLocaleString()}</span>
            </div>
          ))}
          {!audit.length && <p className="empty">No audit events yet.</p>}
        </div>
      </section>
    </main>
  );
}

function Metric({ icon, label, value, tone = "" }) {
  return (
    <div className={`metric ${tone}`}>
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;
