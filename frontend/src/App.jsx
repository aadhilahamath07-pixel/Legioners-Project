import { useEffect, useMemo, useState } from "react";

import {

  Activity, AlertTriangle, BarChart3, CheckCircle2, ChevronRight,

  Clock3, FileText, Gauge, ImagePlus, LayoutDashboard, MapPin, Menu,

  Search, Settings, ShieldCheck, Upload, X, Download, LoaderCircle, ScanSearch,

} from "lucide-react";

import "./App.css";

import "leaflet/dist/leaflet.css";

import L from "leaflet";

import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";



const navItems = [

  { label: "Dashboard", icon: LayoutDashboard },

  { label: "Detect Potholes", icon: Activity },

  { label: "Reports", icon: FileText },

  { label: "Pothole Map", icon: MapPin },

  { label: "Analytics", icon: BarChart3 },

];



const API_BASE = (

  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

).replace(/\/$/, "");



function formatDetectedAt(value) {

  if (!value) return "Unknown";

  const date = new Date(value);

  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();

}



function normalizeResults(data) {

  const raw = data?.detections ?? data?.results ?? data?.predictions ?? data?.boxes ?? [];

  if (!Array.isArray(raw)) return [];



  return raw.map((item, index) => {

    const box = item?.box ?? item?.bbox ?? item?.xyxy ?? item?.coordinates ?? null;

    return {

      id: index + 1,

      label: item?.class_name ?? item?.label ?? item?.name ?? "Pothole",

      confidence: Number(item?.confidence ?? item?.conf ?? item?.score ?? 0),

      box: Array.isArray(box)

        ? box

        : box && typeof box === "object"

          ? [

              box.x1 ?? box.x ?? 0,

              box.y1 ?? box.y ?? 0,

              box.x2 ?? ((box.x ?? 0) + (box.width ?? 0)),

              box.y2 ?? ((box.y ?? 0) + (box.height ?? 0)),

            ]

          : null,

    };

  });

}



function mapInspectionToRecord(inspection) {

  const detections = Array.isArray(inspection.detections) ? inspection.detections : [];

  const confidences = detections.map((item) => {

    const value = Number(item?.confidence ?? item?.conf ?? item?.score ?? 0);

    return value <= 1 ? value * 100 : value;

  });

  const maxConfidence = confidences.length ? Math.max(...confidences) : 0;



  return {

    id: inspection.id,

    road: inspection.filename || "Uploaded image",

    latitude: inspection.latitude == null ? null : Number(inspection.latitude),

    longitude: inspection.longitude == null ? null : Number(inspection.longitude),

    location: inspection.latitude != null && inspection.longitude != null

      ? `${Number(inspection.latitude).toFixed(5)}, ${Number(inspection.longitude).toFixed(5)}`

      : "GPS unavailable",

    count: Number(inspection.count ?? detections.length),

    severity:

      detections.length === 0

        ? "None"

        : maxConfidence >= 80

          ? "High"

          : maxConfidence >= 50

            ? "Medium"

            : "Low",

    confidence: maxConfidence,

    detected: formatDetectedAt(inspection.created_at),

    createdAt: inspection.created_at,

    imageWidth: inspection.image_width,

    imageHeight: inspection.image_height,

    detections,

    annotatedImage: inspection.annotated_image || "",

    status: inspection.status || "Pending",
    priorityScore: inspection.priority_score == null ? null : Number(inspection.priority_score),
    priorityLevel: inspection.priority_level || null,
    priorityExplanation: inspection.priority_explanation || "",
    priorityFactors: inspection.priority_factors && typeof inspection.priority_factors === "object"
      ? inspection.priority_factors
      : null,

  };

}



function Sidebar({ page, setPage, mobileOpen, closeMobile }) {

  return (

    <>

      {mobileOpen && (

        <button className="sidebar-backdrop" onClick={closeMobile} aria-label="Close navigation" />

      )}

      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>

        <a className="brand" href="#dashboard" onClick={(event) => {

          event.preventDefault();

          setPage("Dashboard");

          closeMobile();

        }}>

          <span className="brand-icon"><ShieldCheck size={25} /></span>

          <span className="brand-copy">

            <strong>LEGIONERS</strong>

            <span>ROAD INTELLIGENCE</span>

          </span>

        </a>



        <div className="nav-section-label">WORKSPACE</div>

        <nav className="navigation">

          {navItems.map(({ label, icon: Icon }) => (

            <button key={label} className={`nav-item ${page === label ? "active" : ""}`} onClick={() => {

              setPage(label);

              closeMobile();

            }}>

              <Icon size={19} />

              <span>{label}</span>

              {page === label && <ChevronRight className="nav-chevron" size={16} />}

            </button>

          ))}

        </nav>



        <div className="nav-section-label preferences-label">PREFERENCES</div>

        <button className={`nav-item ${page === "Settings" ? "active" : ""}`} onClick={() => {

          setPage("Settings");

          closeMobile();

        }}>

          <Settings size={19} />

          <span>Settings</span>

        </button>



        <div className="sidebar-footer">

          <div className="system-status">

            <span className="status-dot" />

            <div><strong>System status</strong><span>Frontend operational</span></div>

          </div>

          <div className="team-card">

            <div className="team-avatar">L</div>

            <div><strong>Legioners Team</strong><span>Project workspace</span></div>

          </div>

        </div>

      </aside>

    </>

  );

}



function PageHeading({ eyebrow, title, description, children }) {

  return (

    <div className="page-heading">

      <div>

        <span className="eyebrow">{eyebrow}</span>

        <h1>{title}</h1>

        <p>{description}</p>

      </div>

      {children && <div className="heading-actions">{children}</div>}

    </div>

  );

}



function MetricCard({ label, value, change, icon: Icon, tone = "blue" }) {

  return (

    <article className="metric-card">

      <div className="metric-top">

        <span>{label}</span>

        <span className={`metric-icon ${tone}`}><Icon size={20} /></span>

      </div>

      <strong className="metric-value">{value}</strong>

      <span className="metric-change">{change}</span>

    </article>

  );

}



function DetectionTable({ records, query = "", onSelect, onStatusChange }) {

  const filtered = records.filter((record) =>

    `${record.road} ${record.location} ${record.priorityLevel || ""} ${record.priorityScore ?? ""} ${record.status}`

      .toLowerCase()

      .includes(query.toLowerCase())

  );



  return (

    <div className="table-scroll">

      <table className="data-table">

        <thead>

          <tr>

            <th>IMAGE / SOURCE</th><th>DETECTIONS</th><th>PRIORITY SCORE</th>

            <th>MAX CONFIDENCE</th><th>DETECTED AT</th><th>STATUS</th>

          </tr>

        </thead>

        <tbody>

          {filtered.map((record) => (

            <tr

              key={record.id}

              onClick={() => onSelect?.(record)}

              onKeyDown={(event) => {

                if (onSelect && (event.key === "Enter" || event.key === " ")) {

                  event.preventDefault();

                  onSelect(record);

                }

              }}

              tabIndex={onSelect ? 0 : undefined}

              aria-label={onSelect ? `Open inspection ${record.road}` : undefined}

              style={onSelect ? { cursor: "pointer" } : undefined}

              title={onSelect ? "Click to view inspection details" : undefined}

            >

              <td><div className="road-cell"><strong>{record.road}</strong><span>{record.location}</span></div></td>

              <td>{record.count}</td>

              <td>
                {record.priorityScore == null ? (
                  <span className="priority-unassigned">Not scored</span>
                ) : (
                  <span className={`severity ${(record.priorityLevel || "Low").toLowerCase()}`}>
                    {record.priorityLevel} · {record.priorityScore.toFixed(1)}
                  </span>
                )}
              </td>

              <td className="confidence">{record.confidence.toFixed(1)}%</td>

              <td className="muted-cell">{record.detected}</td>

              <td onClick={(event) => event.stopPropagation()}>

                {onStatusChange ? (

                  <select

                    className={`status-pill ${record.status.toLowerCase().replace(" ", "-")}`}

                    value={record.status}

                    aria-label={`Update status for ${record.road}`}

                    onChange={(event) => onStatusChange(record.id, event.target.value)}

                  >

                    <option value="Pending">Pending</option>

                    <option value="In Progress">In Progress</option>

                    <option value="Resolved">Resolved</option>

                  </select>

                ) : (

                  <span className={`status-pill ${record.status.toLowerCase().replace(" ", "-")}`}>{record.status}</span>

                )}

              </td>

            </tr>

          ))}

          {filtered.length === 0 && <tr><td colSpan={6} className="empty-state">No inspection records found.</td></tr>}

        </tbody>

      </table>

    </div>

  );

}



function Dashboard({ records, onDetect, onExport, onSelectInspection, onStatusChange, historyLoading, historyError }) {

  const totalDetections = records.reduce((sum, record) => sum + record.count, 0);

  const highPriority = records.filter((record) => record.priorityLevel === "High").length;

  const connected = !historyLoading && !historyError;



  return (

    <>

      <PageHeading eyebrow="OVERVIEW" title="Road Intelligence Dashboard" description="Monitor road conditions and review saved pothole inspections.">

        <button className="button button-secondary" onClick={onExport}><Download size={17} /> Export report</button>

        <button className="button button-primary" onClick={onDetect}><ScanSearch size={17} /> Detect potholes</button>

      </PageHeading>



      {historyError && <div className="alert alert-error">{historyError}</div>}



      <section className="metrics-grid">

        <MetricCard label="Total detections" value={historyLoading ? "…" : totalDetections} change="Across saved inspections" icon={ScanSearch} />

        <MetricCard label="Inspections" value={historyLoading ? "…" : records.length} change="Saved in SQLite" icon={MapPin} tone="purple" />

        <MetricCard label="High priority" value={historyLoading ? "…" : highPriority} change="Saved multi-factor risk scores" icon={AlertTriangle} tone="orange" />

        <MetricCard label="Database history" value={historyLoading ? "Loading…" : connected ? "Connected" : "Unavailable"} change={connected ? "Loaded from FastAPI" : "Check backend connection"} icon={Gauge} tone={connected ? "green" : "orange"} />

      </section>



      <section className="panel">

        <div className="panel-heading">

          <div><h2>Recent inspection records</h2><p>Records retrieved from the backend database</p></div>

          <span className="record-count">{records.length} records</span>

        </div>

        <DetectionTable records={records.slice(0, 8)} onSelect={onSelectInspection} onStatusChange={onStatusChange} />

      </section>



      <div className="bottom-grid">

        <section className="panel info-panel">

          <div className="panel-heading"><div><h2>Detection workflow</h2><p>From road image to inspection result</p></div></div>

          <div className="workflow">

            <div className="workflow-item"><span className="workflow-icon"><ImagePlus size={19} /></span><div><strong>Upload road image</strong><span>Select a JPG, PNG or WEBP file</span></div></div>

            <div className="workflow-item"><span className="workflow-icon"><ScanSearch size={19} /></span><div><strong>Run YOLO inference</strong><span>Identify potholes and confidence scores</span></div></div>

            <div className="workflow-item"><span className="workflow-icon"><FileText size={19} /></span><div><strong>Review the result</strong><span>Inspect detections before reporting</span></div></div>

          </div>

        </section>



        <section className="panel info-panel">

          <div className="panel-heading"><div><h2>System readiness</h2><p>Current connection status</p></div></div>

          <div className="readiness-row"><span>Frontend</span><span className="ready-label"><CheckCircle2 size={15} /> Running</span></div>

          <div className="readiness-row"><span>YOLO API</span><span className={historyError ? "pending-label" : "ready-label"}>{historyError ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}{historyError ? "Check connection" : "Reachable"}</span></div>

          <div className="readiness-row"><span>Inspection history</span><span className={connected ? "ready-label" : "pending-label"}>{connected ? <CheckCircle2 size={15} /> : <Clock3 size={15} />}{historyLoading ? "Loading" : connected ? "Connected" : "Unavailable"}</span></div>

        </section>

      </div>

    </>

  );

}



function DetectPage({ onRefreshRecords }) {

  const [file, setFile] = useState(null);

  const [preview, setPreview] = useState("");

  const [results, setResults] = useState([]);

  const [resultImage, setResultImage] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [message, setMessage] = useState("");



  function chooseFile(event) {

    const selected = event.target.files?.[0];

    if (!selected) return;



    setError("");

    setMessage("");

    setResults([]);

    setResultImage("");



    if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type)) {

      setError("Choose a JPG, PNG or WEBP image.");

      event.target.value = "";

      return;

    }

    if (selected.size > 10 * 1024 * 1024) {

      setError("The image must be 10 MB or smaller.");

      event.target.value = "";

      return;

    }



    if (preview) URL.revokeObjectURL(preview);

    setFile(selected);

    setPreview(URL.createObjectURL(selected));

  }



  function clearFile() {

    if (preview) URL.revokeObjectURL(preview);

    setFile(null);

    setPreview("");

    setResults([]);

    setResultImage("");

    setError("");

    setMessage("");

  }



  async function runDetection() {

    if (!file) {

      setError("Upload a road image before running detection.");

      return;

    }



    setLoading(true);

    setError("");

    setMessage("");

    setResults([]);

    setResultImage("");



    try {

      const formData = new FormData();

      formData.append("file", file);



      // GPS is optional: if permission is denied or unavailable, detection still proceeds.

      if ("geolocation" in navigator) {

        try {

          const position = await new Promise((resolve, reject) => {

            navigator.geolocation.getCurrentPosition(resolve, reject, {

              enableHighAccuracy: true,

              timeout: 8000,

              maximumAge: 60000,

            });

          });

          formData.append("latitude", String(position.coords.latitude));

          formData.append("longitude", String(position.coords.longitude));

        } catch {

          // Continue without coordinates when GPS permission is denied or times out.

        }

      }

      const response = await fetch(`${API_BASE}/api/v1/detect`, { method: "POST", body: formData });



      if (!response.ok) {

        const detail = await response.text();

        throw new Error(`API returned ${response.status}${detail ? `: ${detail.slice(0, 250)}` : ""}`);

      }



      const contentType = response.headers.get("content-type") || "";

      if (!contentType.includes("application/json")) throw new Error("The API returned a non-JSON response.");



      const data = await response.json();

      const detections = normalizeResults(data);

      setResults(detections);



      const annotated = data?.annotated_image ?? data?.image_base64;

      if (typeof annotated === "string" && annotated) {

        setResultImage(annotated.startsWith("data:") ? annotated : `data:image/jpeg;base64,${annotated}`);

      }



      setMessage(detections.length === 0

        ? "Inspection completed: no potholes detected."

        : `Inference completed: ${detections.length} detection(s).`);



      // Reload from SQLite after every successful inspection, even with zero detections.

      await onRefreshRecords();

    } catch (err) {

      setError(`${err.message || "Detection failed."} Check that FastAPI is running at ${API_BASE}.`);

    } finally {

      setLoading(false);

    }

  }



  return (

    <>

      <PageHeading eyebrow="COMPUTER VISION" title="Detect potholes" description="Upload a road image and analyze it using the YOLO detection API." />

      <section className="panel upload-panel">

        <div className="panel-heading">

          <div><h2>Image inspection</h2><p>JPG, PNG or WEBP · Maximum file size 10 MB</p></div>

          <span className="api-chip"><span className="status-dot" /> API mode</span>

        </div>



        {!file ? (

          <label className="upload-zone">

            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile} hidden />

            <span className="upload-icon"><Upload size={25} /></span>

            <strong>Choose a road image</strong>

            <span>Click to browse files from your computer</span>

            <span className="button button-secondary upload-button"><ImagePlus size={17} /> Select image</span>

          </label>

        ) : (

          <div className="image-review">

            <div className="image-preview-wrap">

              <img src={preview} alt="Selected road for inspection" />

              <button className="remove-image" onClick={clearFile} aria-label="Remove image" type="button"><X size={18} /></button>

            </div>

            <div className="file-details">

              <strong>{file.name}</strong>

              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>

              <div className="upload-actions">

                <button className="button button-secondary" onClick={clearFile} type="button">Remove</button>

                <button className="button button-primary" onClick={runDetection} disabled={loading} type="button">

                  {loading ? <LoaderCircle className="spin" size={17} /> : <ScanSearch size={17} />}

                  {loading ? "Analyzing..." : "Run detection"}

                </button>

              </div>

            </div>

          </div>

        )}

        {error && <div className="alert alert-error">{error}</div>}

        {message && <div className="alert alert-success">{message}</div>}

      </section>



      {(results.length > 0 || resultImage) && (

        <section className="panel results-panel">

          <div className="panel-heading"><div><h2>Inference results</h2><p>Returned by the detection API</p></div><span className="record-count">{results.length} detections</span></div>

          {resultImage && <img className="annotated-image" src={resultImage} alt="YOLO annotated result" />}

          {results.length > 0 && (

            <div className="table-scroll">

              <table className="data-table">

                <thead><tr><th>#</th><th>CLASS</th><th>CONFIDENCE</th><th>BOX COORDINATES</th></tr></thead>

                <tbody>

                  {results.map((result) => (

                    <tr key={result.id}>

                      <td>{result.id}</td><td>{result.label}</td>

                      <td>{(result.confidence * (result.confidence <= 1 ? 100 : 1)).toFixed(1)}%</td>

                      <td className="muted-cell">{result.box ? result.box.map((n) => Number(n).toFixed(0)).join(", ") : "Not provided"}</td>

                    </tr>

                  ))}

                </tbody>

              </table>

            </div>

          )}

        </section>

      )}



      <div className="api-help">

        <AlertTriangle size={18} />

        <div><strong>Backend contract</strong><p>This page sends multipart form data to <code>POST {API_BASE}/api/v1/detect</code> using the field <code>file</code>. The API returns detections, bounding boxes, and an annotated image.</p></div>

      </div>

    </>

  );

}



function SimplePage({ page, records, onExport, onSelectInspection, onStatusChange, historyLoading, historyError }) {

  const descriptions = {

    Reports: "Search, review and export saved inspection records.",

    Analytics: "Review the inspection data currently available.",

    Settings: "Configure your workspace and API connection.",

  };



  return (

    <>

      <PageHeading eyebrow="WORKSPACE" title={page} description={descriptions[page]}>

        {page === "Reports" && <button className="button button-primary" onClick={onExport}><Download size={17} /> Export CSV</button>}

      </PageHeading>



      {page === "Reports" && (

        <>

          {historyError && <div className="alert alert-error">{historyError}</div>}

          <section className="panel">

            <div className="panel-heading">

              <div><h2>Inspection records</h2><p>{historyLoading ? "Loading records from backend…" : "Saved in the backend database"}</p></div>

              <span className="record-count">{records.length} records</span>

            </div>

            <DetectionTable records={records} onSelect={onSelectInspection} onStatusChange={onStatusChange} />

          </section>

        </>

      )}



      {page === "Analytics" && (

        <section className="metrics-grid">

          <MetricCard label="Inspections" value={historyLoading ? "…" : records.length} change="Saved inspections" icon={FileText} />

          <MetricCard label="Potholes detected" value={historyLoading ? "…" : records.reduce((sum, r) => sum + r.count, 0)} change="Across saved inspections" icon={AlertTriangle} tone="orange" />

          <MetricCard label="No detections" value={historyLoading ? "…" : records.filter((r) => r.count === 0).length} change="Inspections with zero detections" icon={CheckCircle2} tone="green" />

          <MetricCard label="Awaiting action" value={historyLoading ? "…" : records.filter((r) => r.status !== "Resolved").length} change="Inspection records" icon={Clock3} tone="purple" />

        </section>

      )}



      {page === "Settings" && (

        <section className="panel settings-panel">

          <h2>API connection</h2><p>Frontend API base URL</p><code>{API_BASE}</code>

          <p className="muted-cell">Set VITE_API_BASE_URL in frontend/.env to change this address, then restart Vite.</p>

          <div className="readiness-row">

            <span>Inspection history</span>

            <span className={historyError ? "pending-label" : "ready-label"}>

              {historyError ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}

              {historyLoading ? "Loading" : historyError ? "Unavailable" : "Connected"}

            </span>

          </div>

          {historyError && <div className="alert alert-error">{historyError}</div>}

        </section>

      )}

    </>

  );

}



function severityColor(severity) {

  if (severity === "High") return "#dc2626";

  if (severity === "Medium") return "#d97706";

  if (severity === "Low") return "#16a34a";

  return "#64748b";

}



function createSeverityIcon(severity) {

  const color = severityColor(severity);

  return L.divIcon({

    className: "pothole-map-marker-wrap",

    html: `<div style="width:20px;height:20px;border-radius:50%;background:${color};border:3px solid white;box-shadow:0 1px 7px #0007;"></div>`,

    iconSize: [20, 20],

    iconAnchor: [10, 10],

    popupAnchor: [0, -12],

  });

}



function FitMapToMarkers({ records }) {

  const map = useMap();

  useEffect(() => {

    if (records.length === 1) {

      map.setView([records[0].latitude, records[0].longitude], 15);

    } else if (records.length > 1) {

      const bounds = L.latLngBounds(records.map((record) => [record.latitude, record.longitude]));

      map.fitBounds(bounds, { padding: [35, 35], maxZoom: 15 });

    }

  }, [map, records]);

  return null;

}



function PotholeMapPage({ records, onSelectInspection, historyLoading, historyError }) {

  const [statusFilter, setStatusFilter] = useState("All statuses");

  const [severityFilter, setSeverityFilter] = useState("All priorities");

  const mappedRecords = records.filter((record) =>

    Number.isFinite(record.latitude) && Number.isFinite(record.longitude) &&

    record.latitude >= -90 && record.latitude <= 90 &&

    record.longitude >= -180 && record.longitude <= 180

  );

  const filteredRecords = mappedRecords.filter((record) =>

    (statusFilter === "All statuses" || record.status === statusFilter) &&

    (severityFilter === "All priorities" ||
      (severityFilter === "None" ? record.priorityLevel == null : record.priorityLevel === severityFilter))

  );

  const center = filteredRecords.length

    ? [filteredRecords[0].latitude, filteredRecords[0].longitude]

    : mappedRecords.length

      ? [mappedRecords[0].latitude, mappedRecords[0].longitude]

      : [20.5937, 78.9629];



  return (

    <>

      <PageHeading eyebrow="GEO-SPATIAL INTELLIGENCE" title="Pothole map" description="Explore GPS-tagged inspections and filter by workflow status or saved multi-factor priority." />

      {historyError && <div className="alert alert-error">{historyError}</div>}

      <section className="panel" style={{ marginBottom: 18 }}>

        <div className="panel-heading">

          <div><h2>Map filters</h2><p>Filters apply to the markers and the inspection list.</p></div>

          <span className="record-count">{filteredRecords.length} mapped</span>

        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "end" }}>

          <label style={{ display: "grid", gap: 6, minWidth: 190, color: "var(--muted, #64748b)", fontSize: 13 }}>

            Inspection status

            <select className="map-filter-select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>

              <option>All statuses</option><option>Pending</option><option>In Progress</option><option>Resolved</option>

            </select>

          </label>

          <label style={{ display: "grid", gap: 6, minWidth: 190, color: "var(--muted, #64748b)", fontSize: 13 }}>

            Detection priority

            <select className="map-filter-select" value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>

              <option>All priorities</option><option>High</option><option>Medium</option><option>Low</option><option>None</option>

            </select>

          </label>

          <button className="button button-secondary" type="button" onClick={() => { setStatusFilter("All statuses"); setSeverityFilter("All priorities"); }}>Reset filters</button>

        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 16, fontSize: 13 }}>

          {[ ["High", "#dc2626"], ["Medium", "#d97706"], ["Low", "#16a34a"], ["None", "#64748b"] ].map(([label, color]) => (

            <span key={label} style={{ display: "inline-flex", alignItems: "center", gap: 7 }}><span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block" }} />{label}</span>

          ))}

        </div>

      </section>



      <section className="panel" style={{ padding: 10, marginBottom: 18 }}>

        <div style={{ height: 480, width: "100%", borderRadius: 12, overflow: "hidden", background: "#e2e8f0" }}>

          <MapContainer center={center} zoom={mappedRecords.length ? 12 : 5} scrollWheelZoom style={{ height: "100%", width: "100%" }}>

            <TileLayer

              attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a> contributors'

              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

            />

            <FitMapToMarkers records={filteredRecords} />

            {filteredRecords.map((record) => (

              <Marker key={record.id} position={[record.latitude, record.longitude]} icon={createSeverityIcon(record.priorityLevel || "None")}>

                <Popup>

                  <div style={{ minWidth: 190, display: "grid", gap: 6 }}>

                    <strong style={{ overflowWrap: "anywhere" }}>{record.road}</strong>

                    <span>{record.count} pothole(s) detected</span>

                    <span>Priority: <strong>{record.priorityScore == null ? "Not scored" : `${record.priorityLevel} · ${record.priorityScore.toFixed(1)}/100`}</strong></span>

                    <span>Status: <strong>{record.status}</strong></span>

                    <span style={{ fontSize: 12 }}>{record.latitude.toFixed(6)}, {record.longitude.toFixed(6)}</span>

                    <button type="button" className="button button-primary" onClick={() => onSelectInspection(record)}>View inspection</button>

                  </div>

                </Popup>

              </Marker>

            ))}

          </MapContainer>

        </div>

      </section>



      <section className="panel">

        <div className="panel-heading"><div><h2>Mapped inspections</h2><p>Only records with saved, valid GPS coordinates appear here.</p></div><span className="record-count">{filteredRecords.length} records</span></div>

        {historyLoading ? <p className="muted-cell">Loading inspection history…</p> : filteredRecords.length ? (

          <div className="table-scroll"><table className="data-table">

            <thead><tr><th>IMAGE / SOURCE</th><th>COORDINATES</th><th>DETECTIONS</th><th>PRIORITY</th><th>STATUS</th><th>MAP</th></tr></thead>

            <tbody>{filteredRecords.map((record) => <tr key={record.id}>

              <td><button type="button" className="map-text-button" onClick={() => onSelectInspection(record)}>{record.road}</button></td>

              <td className="muted-cell">{record.latitude.toFixed(5)}, {record.longitude.toFixed(5)}</td>

              <td>{record.count}</td>

              <td>
                {record.priorityScore == null ? (
                  <span className="priority-unassigned">Not scored</span>
                ) : (
                  <span className={`severity ${(record.priorityLevel || "Low").toLowerCase()}`}>
                    {record.priorityLevel} · {record.priorityScore.toFixed(1)}
                  </span>
                )}
              </td>

              <td><span className={`status-pill ${record.status.toLowerCase().replace(" ", "-")}`}>{record.status}</span></td>

              <td><a href={`https://www.google.com/maps?q=${record.latitude},${record.longitude}`} target="_blank" rel="noreferrer">Open map</a></td>

            </tr>)}</tbody>

          </table></div>

        ) : <div className="empty-state" style={{ padding: 24 }}>{mappedRecords.length === 0 ? "No inspections have GPS coordinates yet. Run a new detection and allow location access, or test the API with coordinates." : "No inspections match the selected filters."}</div>}

      </section>

      <p className="muted-cell" style={{ marginTop: 12 }}>Marker colors reflect saved multi-factor priority where available. Gray markers are unscored and need assessment.</p>

    </>

  );

}




function PriorityEditor({ inspection, onSaved }) {
  const defaults = {
    severity: 50,
    traffic: 50,
    road_importance: 50,
    location_risk: 50,
    accessibility: 50,
  };
  const [factors, setFactors] = useState({ ...defaults, ...(inspection.priorityFactors || {}) });
  const [emergencyOverride, setEmergencyOverride] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    setFactors({ ...defaults, ...(inspection.priorityFactors || {}) });
    setEmergencyOverride(false);
    setError("");
    setMessage("");
  }, [inspection.id]);

  const fields = [
    ["severity", "Damage severity"],
    ["traffic", "Traffic exposure"],
    ["road_importance", "Road importance"],
    ["location_risk", "Location risk"],
    ["accessibility", "Accessibility"],
  ];

  async function savePriority(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch(`${API_BASE}/api/v1/inspections/${inspection.id}/priority`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...factors, emergency_override: emergencyOverride }),
      });
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Priority update failed (${response.status})${detail ? `: ${detail.slice(0, 220)}` : ""}`);
      }
      const data = await response.json();
      if (!data.inspection) throw new Error("The API did not return the updated inspection.");
      setMessage(`Saved: ${data.inspection.priority_level} priority · ${Number(data.inspection.priority_score).toFixed(1)}/100`);
      onSaved?.(data.inspection);
    } catch (err) {
      setError(err.message || "Could not save priority factors.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="priority-editor">
      <div className="priority-editor-heading">
        <div>
          <h3>Maintenance priority</h3>
          <p>Rate each factor from 0 to 100. Use evidence where possible.</p>
        </div>
        {inspection.priorityScore != null && (
          <div className="priority-score-summary">
            <strong>{inspection.priorityScore.toFixed(1)}</strong>
            <span>{inspection.priorityLevel || "Scored"} / 100</span>
          </div>
        )}
      </div>
      {inspection.priorityExplanation && (
        <p className="priority-explanation">{inspection.priorityExplanation}</p>
      )}
      <form onSubmit={savePriority}>
        <div className="priority-factor-grid">
          {fields.map(([key, label]) => (
            <label className="priority-factor" key={key}>
              <span>{label}</span>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                required
                value={factors[key]}
                onChange={(event) => setFactors((current) => ({
                  ...current,
                  [key]: event.target.value === "" ? "" : Number(event.target.value),
                }))}
              />
            </label>
          ))}
        </div>
        <label className="priority-emergency">
          <input
            type="checkbox"
            checked={emergencyOverride}
            onChange={(event) => setEmergencyOverride(event.target.checked)}
          />
          <span>Emergency override (only when justified and authorized)</span>
        </label>
        {error && <div className="alert alert-error priority-alert">{error}</div>}
        {message && <div className="alert alert-success priority-alert">{message}</div>}
        <button className="button button-primary" type="submit" disabled={saving}>
          {saving ? <LoaderCircle className="spin" size={16} /> : <Gauge size={16} />}
          {saving ? "Saving priority..." : "Calculate and save priority"}
        </button>
      </form>
    </section>
  );
}

function InspectionDetailsModal({ inspection, onClose, onPrioritySaved }) {

  useEffect(() => {

    if (!inspection) return undefined;

    function handleKeyDown(event) {

      if (event.key === "Escape") onClose();

    }

    window.addEventListener("keydown", handleKeyDown);

    return () => window.removeEventListener("keydown", handleKeyDown);

  }, [inspection, onClose]);



  if (!inspection) return null;



  const detections = Array.isArray(inspection.detections) ? inspection.detections : [];

  const image = inspection.annotatedImage;

  const formatConfidence = (item) => {

    const value = Number(item?.confidence ?? item?.conf ?? item?.score ?? 0);

    return `${(value <= 1 ? value * 100 : value).toFixed(1)}%`;

  };

  const getBox = (item) => {

    const raw = item?.box ?? item?.bbox ?? item?.xyxy ?? item?.coordinates;

    if (Array.isArray(raw)) return raw;

    if (raw && typeof raw === "object") {

      return [

        raw.x1 ?? raw.x ?? 0,

        raw.y1 ?? raw.y ?? 0,

        raw.x2 ?? ((raw.x ?? 0) + (raw.width ?? 0)),

        raw.y2 ?? ((raw.y ?? 0) + (raw.height ?? 0)),

      ];

    }

    return null;

  };



  return (

    <div

      role="presentation"

      onClick={(event) => {

        if (event.target === event.currentTarget) onClose();

      }}

      style={{

        position: "fixed", inset: 0, zIndex: 1000, background: "rgba(5, 10, 20, 0.72)",

        display: "flex", alignItems: "center", justifyContent: "center", padding: "20px",

      }}

    >

      <section

        role="dialog"

        aria-modal="true"

        aria-labelledby="inspection-details-title"

        className="panel"

        style={{

          width: "min(100%, 1000px)", maxHeight: "90vh", overflowY: "auto",

          margin: 0, position: "relative", boxShadow: "0 24px 80px rgba(0,0,0,.3)",

        }}

      >

        <div className="panel-heading" style={{ alignItems: "flex-start" }}>

          <div>

            <span className="eyebrow">INSPECTION DETAILS · #{inspection.id}</span>

            <h2 id="inspection-details-title" style={{ marginTop: "8px", overflowWrap: "anywhere" }}>

              {inspection.road}

            </h2>

            <p>{inspection.detected}</p>

            <p style={{ marginTop: "8px" }}>

              Status: <strong>{inspection.status || "Pending"}</strong>

            </p>

            <p style={{ marginTop: "8px" }}>

              GPS location: {inspection.latitude != null && inspection.longitude != null

                ? <><strong>{inspection.latitude.toFixed(6)}, {inspection.longitude.toFixed(6)}</strong>{" "}<a href={`https://www.google.com/maps?q=${inspection.latitude},${inspection.longitude}`} target="_blank" rel="noreferrer">Open in Google Maps</a></>

                : <span className="muted-cell">Not captured (upload still works without GPS)</span>}

            </p>

          </div>

          <button className="button button-secondary" onClick={onClose} type="button" aria-label="Close inspection details">

            <X size={17} /> Close

          </button>

        </div>



        <PriorityEditor inspection={inspection} onSaved={onPrioritySaved} />

          <div className="metrics-grid" style={{ marginTop: "18px" }}>

          <MetricCard label="Potholes detected" value={inspection.count} change="In this image" icon={ScanSearch} />

          <MetricCard label="Max confidence" value={`${inspection.confidence.toFixed(1)}%`} change="Highest detection score" icon={Gauge} tone="purple" />

          <MetricCard label="Image dimensions" value={inspection.imageWidth && inspection.imageHeight ? `${inspection.imageWidth} × ${inspection.imageHeight}` : "Not available"} change="Width × height in pixels" icon={ImagePlus} tone="green" />

        </div>



        {image ? (

          <div style={{ marginTop: "20px" }}>

            <h3>Annotated image</h3>

            <img

              src={image.startsWith("data:") ? image : `data:image/jpeg;base64,${image}`}

              alt={`Annotated pothole detections for ${inspection.road}`}

              style={{ display: "block", maxWidth: "100%", maxHeight: "440px", objectFit: "contain", borderRadius: "12px", marginTop: "12px" }}

            />

          </div>

        ) : (

          <div className="alert alert-error" style={{ marginTop: "18px" }}>

            No annotated image was saved for this inspection.

          </div>

        )}



        <div className="panel-heading" style={{ marginTop: "24px" }}>

          <div><h2>Individual detections</h2><p>Confidence scores and bounding-box coordinates</p></div>

          <span className="record-count">{detections.length} detections</span>

        </div>



        <div className="table-scroll">

          <table className="data-table">

            <thead><tr><th>#</th><th>CLASS</th><th>CONFIDENCE</th><th>BOUNDING BOX (X1, Y1, X2, Y2)</th></tr></thead>

            <tbody>

              {detections.map((item, index) => {

                const box = getBox(item);

                return (

                  <tr key={index}>

                    <td>{index + 1}</td>

                    <td>{item?.class_name ?? item?.label ?? item?.name ?? "Pothole"}</td>

                    <td className="confidence">{formatConfidence(item)}</td>

                    <td className="muted-cell">{box ? box.map((value) => Number(value).toFixed(0)).join(", ") : "Not provided"}</td>

                  </tr>

                );

              })}

              {detections.length === 0 && (

                <tr><td colSpan={4} className="empty-state">No potholes were detected in this image.</td></tr>

              )}

            </tbody>

          </table>

        </div>

        <p className="muted-cell" style={{ marginTop: "16px" }}>

          Saved timestamp: {inspection.createdAt ? new Date(inspection.createdAt).toLocaleString() : inspection.detected}

        </p>

      </section>

    </div>

  );

}



export default function App() {

  const [page, setPage] = useState("Dashboard");

  const [mobileOpen, setMobileOpen] = useState(false);

  const [search, setSearch] = useState("");

  const [records, setRecords] = useState([]);

  const [historyLoading, setHistoryLoading] = useState(true);

  const [historyError, setHistoryError] = useState("");

  const [selectedInspection, setSelectedInspection] = useState(null);



  const pageTitle = useMemo(() => page === "Dashboard" ? "Overview" : page, [page]);



  async function loadInspectionHistory() {

    setHistoryLoading(true);

    try {

      setHistoryError("");

      const response = await fetch(`${API_BASE}/api/v1/inspections`);

      if (!response.ok) throw new Error(`History API returned ${response.status}`);



      const data = await response.json();

      if (!Array.isArray(data.inspections)) throw new Error("The history API did not return an inspections array.");

      setRecords(data.inspections.map(mapInspectionToRecord));

    } catch (error) {

      setHistoryError(`${error.message || "Could not load history."} Check that FastAPI is running at ${API_BASE}.`);

    } finally {

      setHistoryLoading(false);

    }

  }



  useEffect(() => {

    loadInspectionHistory();

  }, []);



  async function updateInspectionStatus(inspectionId, status) {

    try {

      setHistoryError("");

      const response = await fetch(

        `${API_BASE}/api/v1/inspections/${inspectionId}/status`,

        {

          method: "PATCH",

          headers: { "Content-Type": "application/json" },

          body: JSON.stringify({ status }),

        }

      );



      if (!response.ok) {

        const detail = await response.text();

        throw new Error(`Status update failed (${response.status})${detail ? `: ${detail.slice(0, 200)}` : ""}`);

      }



      const data = await response.json();

      const updatedInspection = data.inspection;

      if (updatedInspection) {

        setRecords((current) =>

          current.map((record) =>

            record.id === inspectionId

              ? { ...record, status: updatedInspection.status || status }

              : record

          )

        );

        setSelectedInspection((current) =>

          current && current.id === inspectionId

            ? { ...current, status: updatedInspection.status || status }

            : current

        );

      } else {

        await loadInspectionHistory();

      }

    } catch (error) {

      setHistoryError(error.message || "Could not update inspection status.");

      await loadInspectionHistory();

    }

  }



  function exportCSV() {

    const headers = ["Inspection ID", "Image filename", "Latitude", "Longitude", "Google Maps URL", "Detection count", "Priority", "Maximum confidence (%)", "Detected at", "Status"];

    const rows = records.map((record) => [

      record.id, record.road, record.latitude ?? "", record.longitude ?? "",

      record.latitude != null && record.longitude != null ? `https://www.google.com/maps?q=${record.latitude},${record.longitude}` : "",

      record.count, record.severity, `${record.confidence.toFixed(1)}%`, record.detected, record.status,

    ]);

    const csv = [headers, ...rows]

      .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(","))

      .join("\r\n");

    const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8;" });

    const url = URL.createObjectURL(blob);

    const anchor = document.createElement("a");

    anchor.href = url;

    anchor.download = "legioners-inspection-report.csv";

    anchor.click();

    URL.revokeObjectURL(url);

  }



  const filteredRecords = records.filter((record) =>

    `${record.road} ${record.location} ${record.priorityLevel || ""} ${record.priorityScore ?? ""} ${record.status}`

      .toLowerCase()

      .includes(search.toLowerCase())

  );



  return (

    <div className="app-shell">

      <Sidebar page={page} setPage={setPage} mobileOpen={mobileOpen} closeMobile={() => setMobileOpen(false)} />

      <main className="main-content">

        <header className="topbar">

          <button className="mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation" type="button"><Menu size={21} /></button>

          <div className="breadcrumb"><span>Legioners</span><span>/</span><strong>{pageTitle}</strong></div>

          <div className="topbar-right"><span className="environment-label"><span className="status-dot" /> Development</span><div className="user-avatar">L</div></div>

        </header>



        <div className="content-area">

          {page === "Dashboard" && (

            <Dashboard records={records} historyLoading={historyLoading} historyError={historyError} onSelectInspection={setSelectedInspection} onStatusChange={updateInspectionStatus} onDetect={() => setPage("Detect Potholes")} onExport={exportCSV} />

          )}

          {page === "Detect Potholes" && <DetectPage onRefreshRecords={loadInspectionHistory} />}

          {page === "Pothole Map" && (

            <PotholeMapPage records={records} historyLoading={historyLoading} historyError={historyError} onSelectInspection={setSelectedInspection} />

          )}

          {page === "Reports" && (

            <>

              <div className="search-row">

                <label className="search-box">

                  <Search size={17} />

                  <input placeholder="Search filenames, priority or status..." value={search} onChange={(event) => setSearch(event.target.value)} />

                </label>

                <button className="button button-secondary" onClick={exportCSV} type="button"><Download size={17} /> Export CSV</button>

              </div>

              <SimplePage page={page} records={filteredRecords} onExport={exportCSV} onSelectInspection={setSelectedInspection} onStatusChange={updateInspectionStatus} historyLoading={historyLoading} historyError={historyError} />

            </>

          )}

          {(page === "Analytics" || page === "Settings") && (

            <SimplePage page={page} records={records} onExport={exportCSV} onSelectInspection={setSelectedInspection} onStatusChange={updateInspectionStatus} historyLoading={historyLoading} historyError={historyError} />

          )}

          <footer className="app-footer"><span>LEGIONERS ROAD INTELLIGENCE</span><span>Prototype · Verify all detection results before operational use</span></footer>

        </div>

      </main>

      <InspectionDetailsModal

        inspection={selectedInspection}

        onClose={() => setSelectedInspection(null)}

      />

    </div>

  );

}
