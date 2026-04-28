import { useState, useEffect } from "react";

const FONT = `@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');`;

const styles = `
  ${FONT}
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0a0f; }

  .app {
    font-family: 'Syne', sans-serif;
    background: #0a0a0f;
    color: #e8e4dc;
    min-height: 100vh;
    padding: 0;
  }

  /* ── Grid noise overlay ── */
  .app::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(rgba(255,200,50,.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,200,50,.025) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }

  .inner { position: relative; z-index: 1; max-width: 1140px; margin: 0 auto; padding: 32px 24px 64px; }

  /* ── Header ── */
  .header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 48px; }
  .logo { display: flex; flex-direction: column; gap: 4px; }
  .logo-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px; letter-spacing: .15em; color: #f5c842;
    text-transform: uppercase;
  }
  .logo-title { font-size: 28px; font-weight: 800; line-height: 1; color: #fff; letter-spacing: -.5px; }
  .logo-title span { color: #f5c842; }
  .status-pill {
    display: flex; align-items: center; gap: 8px;
    background: rgba(245,200,66,.08); border: 1px solid rgba(245,200,66,.2);
    border-radius: 999px; padding: 6px 16px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #f5c842;
  }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

  /* ── Stat cards ── */
  .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 40px; }
  @media(max-width:700px){ .stats-grid { grid-template-columns: 1fr 1fr; } }

  .stat-card {
    background: #13131a; border: 1px solid #222230;
    border-radius: 12px; padding: 20px 22px 18px;
    display: flex; flex-direction: column; gap: 8px;
    transition: border-color .2s, transform .2s;
    cursor: default;
  }
  .stat-card:hover { border-color: rgba(245,200,66,.35); transform: translateY(-2px); }
  .stat-card.accent { border-color: rgba(245,200,66,.25); background: rgba(245,200,66,.04); }

  .stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: .12em;
    text-transform: uppercase; color: #666;
  }
  .stat-value { font-size: 34px; font-weight: 800; line-height: 1; color: #fff; }
  .stat-value.yellow { color: #f5c842; }
  .stat-value.green  { color: #4ade80; }
  .stat-value.red    { color: #f87171; }
  .stat-sub { font-size: 12px; color: #555; }

  /* ── Two-column layout ── */
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  @media(max-width:780px){ .columns { grid-template-columns: 1fr; } }

  /* ── Panel ── */
  .panel { background: #13131a; border: 1px solid #222230; border-radius: 14px; overflow: hidden; }
  .panel-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 20px; border-bottom: 1px solid #1e1e2a;
  }
  .panel-title { font-size: 13px; font-weight: 700; letter-spacing: .04em; color: #ccc; text-transform: uppercase; }
  .panel-body { padding: 20px; }

  /* ── Pipeline steps ── */
  .pipeline { display: flex; flex-direction: column; gap: 0; }
  .step {
    display: flex; align-items: flex-start; gap: 16px;
    padding: 14px 0;
    border-bottom: 1px solid #1a1a24;
    position: relative;
    animation: fadeUp .4s both;
  }
  .step:last-child { border-bottom: none; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }

  .step-num {
    flex-shrink: 0;
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600;
    margin-top: 2px;
  }
  .step-num.done    { background: rgba(74,222,128,.15); color: #4ade80; border: 1px solid rgba(74,222,128,.3); }
  .step-num.active  { background: rgba(245,200,66,.15); color: #f5c842; border: 1px solid rgba(245,200,66,.4); animation: glow 1.4s infinite; }
  .step-num.pending { background: #1a1a24; color: #444; border: 1px solid #282838; }
  @keyframes glow { 0%,100%{box-shadow:0 0 0 0 rgba(245,200,66,0)} 50%{box-shadow:0 0 0 5px rgba(245,200,66,.12)} }

  .step-info { flex: 1; }
  .step-name { font-size: 14px; font-weight: 700; color: #e0dcd2; margin-bottom: 3px; }
  .step-desc { font-size: 12px; color: #555; line-height: 1.5; }
  .step-badge {
    flex-shrink: 0; font-family: 'JetBrains Mono', monospace;
    font-size: 11px; padding: 3px 10px; border-radius: 999px;
    align-self: center;
  }
  .step-badge.done    { background: rgba(74,222,128,.1);  color: #4ade80; }
  .step-badge.active  { background: rgba(245,200,66,.1);  color: #f5c842; }
  .step-badge.pending { background: #1a1a24; color: #444; }

  /* ── CLI Reference ── */
  .cli-list { display: flex; flex-direction: column; gap: 10px; }
  .cli-item {
    background: #0e0e18; border: 1px solid #1e1e2c; border-radius: 10px;
    padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
    transition: border-color .15s;
  }
  .cli-item:hover { border-color: rgba(245,200,66,.25); }
  .cli-cmd {
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: #f5c842; white-space: pre-wrap; word-break: break-all;
  }
  .cli-note { font-size: 11px; color: #4a4a60; }

  /* ── Detection rules ── */
  .rule-list { display: flex; flex-direction: column; gap: 8px; }
  .rule {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 14px; border-radius: 8px;
    background: #0e0e18; border: 1px solid #1a1a28;
  }
  .rule-icon { font-size: 16px; flex-shrink: 0; }
  .rule-text { font-size: 12px; color: #888; line-height: 1.5; }
  .rule-text strong { color: #ccc; display: block; font-size: 13px; margin-bottom: 2px; }

  /* ── Progress bar ── */
  .progress-wrap { margin-top: 6px; }
  .progress-label { display: flex; justify-content: space-between; font-size: 11px; color: #555; margin-bottom: 6px; }
  .progress-track { height: 5px; background: #1a1a28; border-radius: 999px; overflow: hidden; }
  .progress-fill  { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #f5c842, #f59e0b); transition: width 1s ease; }

  /* ── Rate limit info ── */
  .rate-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .rate-item {
    background: #0e0e18; border: 1px solid #1a1a28; border-radius: 8px;
    padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
  }
  .rate-key   { font-size: 10px; color: #555; text-transform: uppercase; letter-spacing: .1em; }
  .rate-value { font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 600; color: #f5c842; }

  /* ── Tabs ── */
  .tabs { display: flex; gap: 2px; padding: 4px; background: #0e0e18; border-radius: 8px; }
  .tab {
    flex: 1; padding: 6px 10px; border-radius: 6px; border: none; cursor: pointer;
    font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 700;
    letter-spacing: .06em; text-transform: uppercase; transition: all .15s;
    background: transparent; color: #555;
  }
  .tab.active { background: #1e1e2c; color: #f5c842; }

  /* ── Footer ── */
  .footer {
    margin-top: 48px; padding-top: 24px; border-top: 1px solid #1a1a24;
    display: flex; align-items: center; justify-content: space-between;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #333;
  }
  .footer a { color: #555; text-decoration: none; }
`;

const PIPELINE_STEPS = [
  { name: "Collect Leads", desc: "Google Maps Places API → businesses by keyword + location", cmd: "python main.py collect --keyword ... --location ..." },
  { name: "Analyze Websites", desc: "Detect NopCommerce installs & flag missing websites", cmd: "python main.py analyze" },
  { name: "Extract Emails", desc: "Crawl homepage + contact pages for public email addresses", cmd: "python main.py extract" },
  { name: "Send Outreach", desc: "Throttled SMTP emails with personalized templates", cmd: "python main.py send_emails --limit 10" },
];

const CLI_COMMANDS = [
  { cmd: 'python main.py collect \\\n  --keyword "clothing stores" \\\n  --location "London" \\\n  --max-results 40', note: "Fetch up to 40 businesses from Google Maps" },
  { cmd: "python main.py analyze --limit 100", note: "Check each website for NopCommerce fingerprints" },
  { cmd: "python main.py extract --limit 50", note: "Scrape public emails from lead websites" },
  { cmd: "python main.py send_emails --dry-run", note: "Preview emails without sending — safe to test" },
  { cmd: "python main.py send_emails --limit 10", note: "Send up to 10 emails (respects hourly cap)" },
  { cmd: "python main.py stats", note: "Print database statistics" },
  { cmd: "python main.py schedule", note: "Start automated pipeline — runs every N hours" },
];

const DETECTION_RULES = [
  { icon: "🔍", title: "HTML Fingerprint", desc: 'Scans raw HTML for "nopCommerce", nop-ajax-cart class, known theme paths, and generator meta tag.' },
  { icon: "🛤️", title: "Admin Path Probe", desc: "Probes /Admin/Login — NopCommerce admin redirects with a distinctive 200 response." },
  { icon: "🌐", title: "No-Website Flag", desc: "Leads with empty website field in Places API response are immediately flagged as targets." },
];

const FAKE_STATS = {
  totalLeads: 247,
  analyzed: 198,
  noWebsite: 63,
  nopCommerce: 29,
  emailsCollected: 114,
  emailsSent: 41,
  emailsFailed: 3,
  emailsHourCap: 10,
  emailsThisHour: 4,
};

function StatCard({ label, value, sub, accent, color }) {
  const [displayed, setDisplayed] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = Math.ceil(value / 40);
    const t = setInterval(() => {
      start += step;
      if (start >= value) { setDisplayed(value); clearInterval(t); }
      else setDisplayed(start);
    }, 20);
    return () => clearInterval(t);
  }, [value]);
  return (
    <div className={`stat-card${accent ? " accent" : ""}`}>
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${color || ""}`}>{displayed.toLocaleString()}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
}

function PipelinePanel({ activeStep }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <span className="panel-title">Pipeline</span>
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: "#555" }}>4 stages</span>
      </div>
      <div className="panel-body">
        <div className="pipeline">
          {PIPELINE_STEPS.map((s, i) => {
            const state = i < activeStep ? "done" : i === activeStep ? "active" : "pending";
            return (
              <div className="step" key={i} style={{ animationDelay: `${i * 80}ms` }}>
                <div className={`step-num ${state}`}>{i < activeStep ? "✓" : i + 1}</div>
                <div className="step-info">
                  <div className="step-name">{s.name}</div>
                  <div className="step-desc">{s.desc}</div>
                </div>
                <div className={`step-badge ${state}`}>
                  {state === "done" ? "done" : state === "active" ? "running" : "idle"}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function DetectionPanel() {
  return (
    <div className="panel">
      <div className="panel-head">
        <span className="panel-title">Detection Rules</span>
      </div>
      <div className="panel-body">
        <div className="rule-list">
          {DETECTION_RULES.map((r, i) => (
            <div className="rule" key={i}>
              <div className="rule-icon">{r.icon}</div>
              <div className="rule-text"><strong>{r.title}</strong>{r.desc}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 20 }}>
          <div className="progress-wrap">
            <div className="progress-label"><span>Analysis progress</span><span>{FAKE_STATS.analyzed}/{FAKE_STATS.totalLeads}</span></div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${(FAKE_STATS.analyzed / FAKE_STATS.totalLeads) * 100}%` }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CLIPanel() {
  const [copied, setCopied] = useState(null);
  const copy = (i, text) => {
    navigator.clipboard?.writeText(text);
    setCopied(i);
    setTimeout(() => setCopied(null), 1500);
  };
  return (
    <div className="panel" style={{ gridColumn: "1 / -1" }}>
      <div className="panel-head">
        <span className="panel-title">Command Reference</span>
        <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 11, color: "#444" }}>click to copy</span>
      </div>
      <div className="panel-body">
        <div className="cli-list">
          {CLI_COMMANDS.map((c, i) => (
            <div className="cli-item" key={i} onClick={() => copy(i, c.cmd)} style={{ cursor: "pointer" }}>
              <div className="cli-cmd">{copied === i ? "✓ copied!" : c.cmd}</div>
              <div className="cli-note">{c.note}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RatePanel() {
  return (
    <div className="panel">
      <div className="panel-head"><span className="panel-title">Rate Limits</span></div>
      <div className="panel-body">
        <div className="rate-grid">
          {[
            { key: "Emails / hour", value: `${FAKE_STATS.emailsThisHour} / ${FAKE_STATS.emailsHourCap}` },
            { key: "Request delay", value: "2.0s" },
            { key: "Crawl pages", value: "3 max" },
            { key: "Request timeout", value: "10s" },
          ].map((r, i) => (
            <div className="rate-item" key={i}>
              <div className="rate-key">{r.key}</div>
              <div className="rate-value">{r.value}</div>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 16 }}>
          <div className="progress-wrap">
            <div className="progress-label">
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "#555" }}>Hourly send quota</span>
              <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: 10, color: "#f5c842" }}>{FAKE_STATS.emailsThisHour}/{FAKE_STATS.emailsHourCap}</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${(FAKE_STATS.emailsThisHour / FAKE_STATS.emailsHourCap) * 100}%` }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [activeStep, setActiveStep] = useState(2);
  const [tab, setTab] = useState("overview");

  // Simulate live pipeline ticking
  useEffect(() => {
    const t = setInterval(() => setActiveStep(s => (s + 1) % 4), 3500);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="app">
      <style>{styles}</style>
      <div className="inner">

        {/* Header */}
        <div className="header">
          <div className="logo">
            <div className="logo-tag">v1.0.0 · Python 3.11+</div>
            <div className="logo-title">Lead<span>Gen</span> Tool</div>
          </div>
          <div className="status-pill">
            <div className="dot" />
            Scheduler active
          </div>
        </div>

        {/* Tabs */}
        <div style={{ marginBottom: 28 }}>
          <div className="tabs">
            {["overview", "pipeline", "cli"].map(t2 => (
              <button key={t2} className={`tab${tab === t2 ? " active" : ""}`} onClick={() => setTab(t2)}>
                {t2}
              </button>
            ))}
          </div>
        </div>

        {tab === "overview" && (
          <>
            {/* Stats */}
            <div className="stats-grid">
              <StatCard label="Total Leads" value={FAKE_STATS.totalLeads} sub="via Google Maps API" />
              <StatCard label="No Website" value={FAKE_STATS.noWebsite} sub="prime targets" color="yellow" accent />
              <StatCard label="NopCommerce" value={FAKE_STATS.nopCommerce} sub="detected sites" color="yellow" accent />
              <StatCard label="Emails Found" value={FAKE_STATS.emailsCollected} sub="from public pages" />
              <StatCard label="Emails Sent" value={FAKE_STATS.emailsSent} sub="outreach delivered" color="green" />
              <StatCard label="Failed" value={FAKE_STATS.emailsFailed} sub="delivery errors" color="red" />
            </div>

            <div className="columns">
              <PipelinePanel activeStep={activeStep} />
              <DetectionPanel />
            </div>

            <RatePanel />
          </>
        )}

        {tab === "pipeline" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <PipelinePanel activeStep={activeStep} />
            <DetectionPanel />
          </div>
        )}

        {tab === "cli" && (
          <div className="columns" style={{ gridTemplateColumns: "1fr" }}>
            <CLIPanel />
          </div>
        )}

        {/* Footer */}
        <div className="footer">
          <span>SQLite · smtplib · Google Maps Places API · APScheduler</span>
          <span>Anti-spam throttled · Public data only</span>
        </div>

      </div>
    </div>
  );
}
