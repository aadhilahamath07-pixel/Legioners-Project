
import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileText,
  Gauge,
  ImagePlus,
  LayoutDashboard,
  MapPin,
  Menu,
  Search,
  Settings,
  ShieldCheck,
  Upload,
  X,
  Download,
  LoaderCircle,
  ScanSearch,
} from "lucide-react";
import "./App.css";

const initialRecords = [
  {
    id: 1,
    road: "Avinashi Road",
    location: "Coimbatore",
    severity: "High",
    confidence: 96.8,
    detected: "Today, 10:42 AM",
    status: "Pending",
  },
  {
    id: 2,
    road: "Trichy Road",
    location: "Coimbatore",
    severity: "Medium",
    confidence: 91.2,
    detected: "Today, 09:18 AM",
    status: "In progress",
  },
  {
    id: 3,
    road: "Sathy Road",
    location: "Coimbatore",
    severity: "Low",
    confidence: 87.5,
    detected: "Yesterday, 04:35 PM",
    status: "Resolved",
  },
  {
    id: 4,
    road: "Mettupalayam Road",
    location: "Coimbatore",
    severity: "High",
    confidence: 94.1,
    detected: "Yesterday, 02:15 PM",
    status: "Pending",
  },
];

const navItems = [
  { label: "Dashboard", icon: LayoutDashboard },
  { label: "Detect Potholes", icon: Activity },
  { label: "Reports", icon: FileText },
  { label: "Analytics", icon: BarChart3 },
];

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

// Handles several common object-detection response formats.
// Adjust the field names here if your FastAPI response differs.
function normalizeResults(data) {
  const raw =
    data?.detections ??
    data?.results ??
    data?.predictions ??
    data?.boxes ??
    [];

  if (!Array.isArray(raw)) return [];

  return raw.map((item, index) => {
    const box =
      item?.box ??
      item?.bbox ??
      item?.xyxy ??
      item?.coordinates ??
      null;

    return {
      id: index + 1,
      label: item?.class_name ?? item?.label ?? item?.name ?? "Pothole",
      confidence: Number(
        item?.confidence ?? item?.conf ?? item?.score ?? 0
      ),
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

function Sidebar({ page, setPage, mobileOpen, closeMobile }) {
  return (
    <>
      {mobileOpen && (
        <button
          className="sidebar-backdrop"
          onClick={closeMobile}
          aria-label="Close navigation"
        />
      )}

      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <a className="brand" href="#dashboard" onClick={(event) => {
          event.preventDefault();
          setPage("Dashboard");
          closeMobile();
        }}>
          <span className="brand-icon">
            <ShieldCheck size={25} />
          </span>
          <span className="brand-copy">
            <strong>LEGIONERS</strong>
            <span>ROAD INTELLIGENCE</span>
          </span>
        </a>

        <div className="nav-section-label">WORKSPACE</div>

        <nav className="navigation">
          {navItems.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${page === label ? "active" : ""}`}
              onClick={() => {
                setPage(label);
                closeMobile();
              }}
            >
              <Icon size={19} />
              <span>{label}</span>
              {page === label && <ChevronRight className="nav-chevron" size={16} />}
            </button>
          ))}
        </nav>

        <div className="nav-section-label preferences-label">PREFERENCES</div>
        <button
          className={`nav-item ${page === "Settings" ? "active" : ""}`}
          onClick={() => {
            setPage("Settings");
            closeMobile();
          }}
        >
          <Settings size={19} />
          <span>Settings</span>
        </button>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" />
            <div>
              <strong>System status</strong>
              <span>Frontend operational</span>
            </div>
          </div>
          <div className="team-card">
            <div className="team-avatar">L</div>
            <div>
              <strong>Legioners Team</strong>
              <span>Project workspace</span>
            </div>
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
        <span className={`metric-icon ${tone}`}>
          <Icon size={20} />
        </span>
      </div>
      <strong className="metric-value">{value}</strong>
      <span className="metric-change">{change}</span>
    </article>
  );
}

function DetectionTable({ records, query = "" }) {
  const filtered = records.filter((record) =>
    `${record.road} ${record.location} ${record.severity} ${record.status}`
      .toLowerCase()
      .includes(query.toLowerCase())
  );

  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th>ROAD / LOCATION</th>
            <th>SEVERITY</th>
            <th>CONFIDENCE</th>
            <th>DETECTED AT</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((record) => (
            <tr key={record.id}>
              <td>
                <div className="road-cell">
                  <strong>{record.road}</strong>
                  <span>{record.location}</span>
                </div>
              </td>
              <td>
                <span className={`severity ${record.severity.toLowerCase()}`}>
                  {record.severity}
                </span>
              </td>
              <td className="confidence">{record.confidence.toFixed(1)}%</td>
              <td className="muted-cell">{record.detected}</td>
              <td>
                <span
                  className={`status-pill ${record.status
                    .toLowerCase()
                    .replace(" ", "-")}`}
                >
                  {record.status}
                </span>
              </td>
            </tr>
          ))}
          {filtered.length === 0 && (
            <tr>
              <td colSpan={5} className="empty-state">
                No matching records found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function Dashboard({ records, onDetect, onExport }) {
  const highPriority = records.filter(
    (record) => record.severity === "High" && record.status !== "Resolved"
  ).length;

  return (
    <>
      <PageHeading
        eyebrow="OVERVIEW"
        title="Road Intelligence Dashboard"
        description="Monitor road conditions and review pothole detection activity."
      >
        <button className="button button-secondary" onClick={onExport}>
          <Download size={17} /> Export report
        </button>
        <button className="button button-primary" onClick={onDetect}>
          <ScanSearch size={17} /> Detect potholes
        </button>
      </PageHeading>

      <div className="demo-notice">
        <Activity size={16} />
        <span>
          Demo mode: dashboard figures and records are sample data, not live
          YOLO detections.
        </span>
      </div>

      <section className="metrics-grid">
        <MetricCard
          label="Total detections"
          value="1,284"
          change="Sample cumulative count"
          icon={ScanSearch}
        />
        <MetricCard
          label="Roads inspected"
          value="346 km"
          change="Sample distance monitored"
          icon={MapPin}
          tone="purple"
        />
        <MetricCard
          label="High priority"
          value={highPriority || 38}
          change="Sample unresolved cases"
          icon={AlertTriangle}
          tone="orange"
        />
        <MetricCard
          label="Resolution rate"
          value="76.4%"
          change="Sample performance metric"
          icon={Gauge}
          tone="green"
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Recent detection records</h2>
            <p>Example road inspection records</p>
          </div>
          <span className="record-count">{records.length} records</span>
        </div>
        <DetectionTable records={records} />
      </section>

      <div className="bottom-grid">
        <section className="panel info-panel">
          <div className="panel-heading">
            <div>
              <h2>Detection workflow</h2>
              <p>From road image to inspection result</p>
            </div>
          </div>
          <div className="workflow">
            <div className="workflow-item">
              <span className="workflow-icon"><ImagePlus size={19} /></span>
              <div><strong>Upload road image</strong><span>Select a JPG, PNG or WEBP file</span></div>
            </div>
            <div className="workflow-item">
              <span className="workflow-icon"><ScanSearch size={19} /></span>
              <div><strong>Run YOLO inference</strong><span>Identify potholes and confidence scores</span></div>
            </div>
            <div className="workflow-item">
              <span className="workflow-icon"><FileText size={19} /></span>
              <div><strong>Review the result</strong><span>Inspect detections before reporting</span></div>
            </div>
          </div>
        </section>

        <section className="panel info-panel">
          <div className="panel-heading">
            <div>
              <h2>System readiness</h2>
              <p>Current frontend integration status</p>
            </div>
          </div>
          <div className="readiness-row">
            <span>Frontend</span><span className="ready-label"><CheckCircle2 size={15} /> Running</span>
          </div>
          <div className="readiness-row">
            <span>YOLO API</span><span className="pending-label"><Clock3 size={15} /> Verify connection</span>
          </div>
          <div className="readiness-row">
            <span>Database</span><span className="pending-label"><Clock3 size={15} /> Not connected</span>
          </div>
        </section>
      </div>
    </>
  );
}

function DetectPage({ onAddRecords }) {
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

    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(selected.type)) {
      setError("Choose a JPG, PNG or WEBP image.");
      event.target.value = "";
      return;
    }

    if (selected.size > 10 * 1024 * 1024) {
      setError("The image must be 10 MB or smaller.");
      event.target.value = "";
      return;
    }

    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  }

  function clearFile() {
    if (preview) URL.revokeObjectURL(preview);
    if (resultImage.startsWith("blob:")) URL.revokeObjectURL(resultImage);
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

    try {
      const formData = new FormData();
      formData.append("file", file);

      // Assumes FastAPI exposes POST /predict and accepts a field named "file".
      const response = await fetch(`${API_BASE}/api/v1/detect`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(
          `API returned ${response.status}${detail ? `: ${detail.slice(0, 250)}` : ""}`
        );
      }

      const contentType = response.headers.get("content-type") || "";
      let data;

      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        throw new Error(
          "The API returned a non-JSON response. This page expects JSON detections."
        );
      }

      const detections = normalizeResults(data);
      setResults(detections);

      // Supports an API that returns a base64 image as annotated_image.
      const annotated = data?.annotated_image ?? data?.image_base64;
      if (annotated && typeof annotated === "string") {
        setResultImage(
          annotated.startsWith("data:")
            ? annotated
            : `data:image/jpeg;base64,${annotated}`
        );
      }

      if (detections.length === 0) {
        setMessage(
          "The request succeeded, but no detections were found in the expected response fields. Check the API JSON schema."
        );
      } else {
        setMessage(`Inference completed: ${detections.length} detection(s).`);
        onAddRecords(detections, file.name);
      }
    } catch (err) {
      setError(
        `${err.message}. Check that FastAPI is running, the endpoint is /predict, and CORS allows the Vite origin.`
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="COMPUTER VISION"
        title="Detect potholes"
        description="Upload a road image and analyze it using the YOLO detection API."
      />

      <section className="panel upload-panel">
        <div className="panel-heading">
          <div>
            <h2>Image inspection</h2>
            <p>JPG, PNG or WEBP · Maximum file size 10 MB</p>
          </div>
          <span className="api-chip"><span className="status-dot" /> API mode</span>
        </div>

        {!file ? (
          <label className="upload-zone">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={chooseFile}
              hidden
            />
            <span className="upload-icon"><Upload size={25} /></span>
            <strong>Choose a road image</strong>
            <span>Click to browse files from your computer</span>
            <span className="button button-secondary upload-button">
              <ImagePlus size={17} /> Select image
            </span>
          </label>
        ) : (
          <div className="image-review">
            <div className="image-preview-wrap">
              <img src={preview} alt="Selected road for inspection" />
              <button className="remove-image" onClick={clearFile} aria-label="Remove image">
                <X size={18} />
              </button>
            </div>
            <div className="file-details">
              <strong>{file.name}</strong>
              <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
              <div className="upload-actions">
                <button className="button button-secondary" onClick={clearFile}>
                  Remove
                </button>
                <button
                  className="button button-primary"
                  onClick={runDetection}
                  disabled={loading}
                >
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
          <div className="panel-heading">
            <div>
              <h2>Inference results</h2>
              <p>Returned by the detection API</p>
            </div>
            <span className="record-count">{results.length} detections</span>
          </div>

          {resultImage && (
            <img className="annotated-image" src={resultImage} alt="YOLO annotated result" />
          )}

          {results.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr><th>#</th><th>CLASS</th><th>CONFIDENCE</th><th>BOX COORDINATES</th></tr></thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.id}>
                      <td>{result.id}</td>
                      <td>{result.label}</td>
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
        <div>
          <strong>Backend contract</strong>
          <p>
            This page sends multipart form data to{" "}
            <code>POST {API_BASE}/api/v1/detect</code> with the file field
            named <code>file</code>. The API returns pothole detections
            and bounding-box coordinates.
          </p>
        </div>
      </div>
    </>
  );
}

function SimplePage({ page, records, onExport }) {
  const descriptions = {
    Reports: "Search, review and export inspection records.",
    Analytics: "Review the inspection data currently available.",
    Settings: "Configure your workspace and API connection.",
  };

  return (
    <>
      <PageHeading
        eyebrow="WORKSPACE"
        title={page}
        description={descriptions[page]}
      >
        {page === "Reports" && (
          <button className="button button-primary" onClick={onExport}>
            <Download size={17} /> Export CSV
          </button>
        )}
      </PageHeading>

      {page === "Reports" && (
        <section className="panel">
          <div className="panel-heading">
            <div><h2>Inspection records</h2><p>Current local records</p></div>
            <span className="record-count">{records.length} records</span>
          </div>
          <DetectionTable records={records} />
        </section>
      )}

      {page === "Analytics" && (
        <section className="metrics-grid">
          <MetricCard label="Local records" value={records.length} change="Records in this session" icon={FileText} />
          <MetricCard label="High severity" value={records.filter((r) => r.severity === "High").length} change="Current local records" icon={AlertTriangle} tone="orange" />
          <MetricCard label="Resolved" value={records.filter((r) => r.status === "Resolved").length} change="Current local records" icon={CheckCircle2} tone="green" />
          <MetricCard label="Awaiting action" value={records.filter((r) => r.status !== "Resolved").length} change="Current local records" icon={Clock3} tone="purple" />
        </section>
      )}

      {page === "Settings" && (
        <section className="panel settings-panel">
          <h2>API connection</h2>
          <p>Frontend API base URL</p>
          <code>{API_BASE}</code>
          <p className="muted-cell">
            Set VITE_API_BASE_URL in frontend/.env to change this address, then restart Vite.
          </p>
        </section>
      )}
    </>
  );
}

export default function App() {
  const [page, setPage] = useState("Dashboard");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [records, setRecords] = useState(initialRecords);

  const pageTitle = useMemo(() => {
    if (page === "Dashboard") return "Overview";
    return page;
  }, [page]);

  function exportCSV() {
    const headers = ["Road", "Location", "Severity", "Confidence", "Detected at", "Status"];
    const rows = records.map((record) => [
      record.road,
      record.location,
      record.severity,
      `${record.confidence}%`,
      record.detected,
      record.status,
    ]);

    const csv = [headers, ...rows]
      .map((row) => row.map((value) =>
        `"${String(value).replaceAll('"', '""')}"`
      ).join(","))
      .join("\r\n");

    const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "legioners-detection-report.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function addDetectionRecords(detections, filename) {
    const timestamp = new Date().toLocaleString();

    const newRecords = detections.map((detection, index) => ({
      id: Date.now() + index,
      road: `${filename} — detection ${index + 1}`,
      location: "Uploaded image",
      severity:
        detection.confidence >= 0.8
          ? "High"
          : detection.confidence >= 0.5
            ? "Medium"
            : "Low",
      confidence: Number(
        (detection.confidence <= 1
          ? detection.confidence * 100
          : detection.confidence).toFixed(1)
      ),
      detected: timestamp,
      status: "Pending",
    }));

    setRecords((current) => [...newRecords, ...current]);
  }

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        mobileOpen={mobileOpen}
        closeMobile={() => setMobileOpen(false)}
      />

      <main className="main-content">
        <header className="topbar">
          <button
            className="mobile-menu"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={21} />
          </button>
          <div className="breadcrumb">
            <span>Legioners</span><span>/</span><strong>{pageTitle}</strong>
          </div>
          <div className="topbar-right">
            <span className="environment-label"><span className="status-dot" /> Development</span>
            <div className="user-avatar">L</div>
          </div>
        </header>

        <div className="content-area">
          {page === "Dashboard" && (
            <Dashboard
              records={records}
              onDetect={() => setPage("Detect Potholes")}
              onExport={exportCSV}
            />
          )}

          {page === "Detect Potholes" && (
            <DetectPage onAddRecords={addDetectionRecords} />
          )}

          {page === "Reports" && (
            <>
              <div className="search-row">
                <label className="search-box">
                  <Search size={17} />
                  <input
                    placeholder="Search roads, severity or status..."
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </label>
                <button className="button button-secondary" onClick={exportCSV}>
                  <Download size={17} /> Export CSV
                </button>
              </div>
              <SimplePage page={page} records={records.filter((record) =>
                `${record.road} ${record.location} ${record.severity} ${record.status}`
                  .toLowerCase().includes(search.toLowerCase())
              )} onExport={exportCSV} />
            </>
          )}

          {(page === "Analytics" || page === "Settings") && (
            <SimplePage page={page} records={records} onExport={exportCSV} />
          )}

          <footer className="app-footer">
            <span>LEGIONERS ROAD INTELLIGENCE</span>
            <span>Prototype · Verify all detection results before operational use</span>
          </footer>
        </div>
      </main>
    </div>
  );
}
