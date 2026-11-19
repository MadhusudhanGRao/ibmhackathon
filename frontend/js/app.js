/* ============================================================
   CyberRakshak AI — Frontend Application Logic
   Handles form submission, loading animation, dashboard render
============================================================ */

const API_BASE = "";   // same-origin (Flask serves frontend)

/* ═══════════════════════════════════════════════════════════
   LANDING PAGE — Form Handling
═══════════════════════════════════════════════════════════ */
(function initLanding() {
  const form = document.getElementById("incidentForm");
  if (!form) return;

  /* ── File upload UX ── */
  const uploadArea = document.getElementById("uploadArea");
  const fileInput  = document.getElementById("evidence");
  const fileList   = document.getElementById("fileList") || document.getElementById("file-list");
  let selectedFiles = [];

  if (uploadArea && fileInput) {
    uploadArea.addEventListener("click", () => fileInput.click());
    uploadArea.addEventListener("dragover", e => { e.preventDefault(); uploadArea.classList.add("dragover"); });
    uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
    uploadArea.addEventListener("drop", e => {
      e.preventDefault();
      uploadArea.classList.remove("dragover");
      addFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener("change", () => addFiles(fileInput.files));
  }

  function addFiles(files) {
    for (const f of files) {
      if (!selectedFiles.find(x => x.name === f.name && x.size === f.size)) {
        selectedFiles.push(f);
      }
    }
    renderFileList();
  }

  function renderFileList() {
    if (!fileList) return;
    fileList.innerHTML = "";
    selectedFiles.forEach((f, i) => {
      const div = document.createElement("div");
      div.className = "file-item";
      div.innerHTML = `
        <span>📎 ${escHtml(f.name)}</span>
        <span style="color:var(--text3);font-size:12px">${formatBytes(f.size)}</span>
        <span class="file-remove" data-idx="${i}" title="Remove">✕</span>
      `;
      fileList.appendChild(div);
    });
    fileList.querySelectorAll(".file-remove").forEach(btn => {
      btn.addEventListener("click", () => {
        selectedFiles.splice(parseInt(btn.dataset.idx), 1);
        renderFileList();
      });
    });
  }

  /* ── Live privacy warning on description field ── */
  const descField = document.getElementById("description");
  const privacyWarning = document.getElementById("privacy-warning");
  const SENSITIVE_PATTERNS = [
    { re: /\botp\b.*?\d{4,8}/i,            label: "⚠️ Possible OTP detected — please do not include OTPs." },
    { re: /\bpin\b.*?\d{4,6}/i,            label: "⚠️ Possible PIN detected — please do not include PINs." },
    { re: /\bcvv\b.*?\d{3,4}/i,            label: "⚠️ Possible CVV detected — please do not include CVVs." },
    { re: /password\s*[:=]\s*\S+/i,        label: "⚠️ Possible password detected — please remove it." },
  ];

  if (descField && privacyWarning) {
    descField.addEventListener("input", () => {
      const val = descField.value;
      const hit = SENSITIVE_PATTERNS.find(p => p.re.test(val));
      if (hit) {
        privacyWarning.textContent = hit.label;
        privacyWarning.classList.remove("hidden");
      } else {
        privacyWarning.classList.add("hidden");
      }
    });
  }

  /* ── Form submit ── */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    const formData = new FormData(form);
    // Attach files
    selectedFiles.forEach(f => formData.append("evidence", f));
    // Ensure consent flag
    if (!document.getElementById("consent")?.checked) {
      showError("Please provide consent before submitting.");
      return;
    }
    formData.set("consent", "true");

    showLoading();
    try {
      const res = await fetch(`${API_BASE}/api/incidents`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      hideLoading();
      if (data.success) {
        // Store result for dashboard and redirect
        sessionStorage.setItem("cyberrakshak_result", JSON.stringify(data));
        window.location.href = `/dashboard.html?id=${encodeURIComponent(data.incident_id)}`;
      } else {
        showError((data.errors || ["Submission failed. Please try again."]).join(" "));
      }
    } catch (err) {
      hideLoading();
      showError("Could not connect to the server. Please check that the backend is running.");
    }
  });

  /* ── Error helpers ── */
  function showError(msg) {
    const el = document.getElementById("form-error");
    if (el) { el.textContent = "⚠️ " + msg; el.classList.remove("hidden"); }
  }
  function clearError() {
    const el = document.getElementById("form-error");
    if (el) el.classList.add("hidden");
  }
})();

/* ── Demo scenario loader ── */
function loadDemo() {
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
  set("incident_category", "Fake KYC");
  set("description",
    "[SYNTHETIC DEMO — Not a real case] I received an SMS from a number claiming to be SBI Bank, " +
    "stating my account would be blocked unless I updated my KYC within 24 hours. " +
    "The SMS contained a link. I clicked the link and it opened a website that looked like SBI's " +
    "official site. I entered some details. About 30 minutes later, I received a notification that " +
    "₹5,000 had been debited from my account via UPI without my authorization. " +
    "I did not initiate this transaction. The city is Bengaluru, Karnataka."
  );
  const today = new Date().toISOString().split("T")[0];
  set("incident_date", today);
  set("incident_time", "14:30");
  set("platform", "SBI YONO / UPI");
  set("financial_loss", "5000");
  document.querySelectorAll("input[name='ongoing_status']").forEach(r => {
    r.checked = r.value === "false";
  });
  document.getElementById("consent").checked = true;
  document.getElementById("report")?.scrollIntoView({ behavior: "smooth" });

  const banner = document.createElement("div");
  banner.className = "privacy-notice";
  banner.style.cssText = "background:rgba(245,158,11,0.1);border-color:rgba(245,158,11,0.3);color:var(--warning);";
  banner.textContent = "⚠️ SYNTHETIC DEMO DATA loaded — This is a demonstration scenario only. Not a real Bengaluru cybercrime case.";
  const form = document.getElementById("incidentForm");
  if (form && !document.getElementById("demo-notice")) {
    banner.id = "demo-notice";
    form.prepend(banner);
  }
}

/* ═══════════════════════════════════════════════════════════
   LOADING OVERLAY ANIMATION
═══════════════════════════════════════════════════════════ */
const LOADING_STEPS = [
  { id: "step-privacy",   delay: 0 },
  { id: "step-intake",    delay: 1200 },
  { id: "step-scam",      delay: 2400 },
  { id: "step-evidence",  delay: 3600 },
  { id: "step-reporting", delay: 4800 },
  { id: "step-dashboard", delay: 5800 },
];
let _loadTimer = null;

function showLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (!overlay) return;
  overlay.classList.remove("hidden");

  // Reset steps
  LOADING_STEPS.forEach(s => {
    const el = document.getElementById(s.id);
    if (el) { el.className = "loading-step"; }
  });
  document.getElementById("loadingProgress").style.width = "0%";

  let prog = 0;
  LOADING_STEPS.forEach((s, i) => {
    setTimeout(() => {
      LOADING_STEPS.forEach((ss, ii) => {
        const el = document.getElementById(ss.id);
        if (!el) return;
        if (ii < i) el.className = "loading-step done";
        else if (ii === i) el.className = "loading-step active";
        else el.className = "loading-step";
      });
      prog = Math.round(((i + 1) / LOADING_STEPS.length) * 90);
      document.getElementById("loadingProgress").style.width = prog + "%";
    }, s.delay);
  });
}

function hideLoading() {
  const overlay = document.getElementById("loadingOverlay");
  if (overlay) overlay.classList.add("hidden");
  document.getElementById("loadingProgress").style.width = "100%";
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD — Render incident result
═══════════════════════════════════════════════════════════ */
(function initDashboard() {
  if (!document.getElementById("dashIncidentId")) return;

  // Load result from sessionStorage or fetch by ID
  const params = new URLSearchParams(window.location.search);
  const incidentId = params.get("id");

  const stored = sessionStorage.getItem("cyberrakshak_result");
  if (stored) {
    try {
      const data = JSON.parse(stored);
      renderDashboard(data);
      sessionStorage.removeItem("cyberrakshak_result");
      return;
    } catch (_) {}
  }

  if (incidentId) {
    fetchAndRender(incidentId);
  } else {
    document.getElementById("dashExecutiveSummary").textContent =
      "No incident data found. Please submit an incident from the home page.";
  }
})();

async function fetchAndRender(incidentId) {
  try {
    const res = await fetch(`${API_BASE}/api/incidents/${encodeURIComponent(incidentId)}`);
    const data = await res.json();
    if (data.success) {
      renderDashboard({ incident_id: incidentId, data: { dashboard: buildDashFromDB(data) } });
    }
  } catch (e) {
    document.getElementById("dashExecutiveSummary").textContent =
      "Could not load incident data. Please go back and re-submit.";
  }
}

function buildDashFromDB(dbData) {
  // Reconstruct a minimal dashboard structure from DB records
  return {
    incident_id: dbData.incident?.incident_id || "",
    generated_at: dbData.incident?.created_at || "",
    incident_summary: {
      incident_id: dbData.incident?.incident_id || "",
      category: dbData.incident?.incident_category || "",
      platform: dbData.incident?.platform || "",
      incident_date: dbData.incident?.incident_date || "",
      financial_loss: parseFloat(dbData.incident?.financial_loss || 0),
      ongoing: dbData.incident?.ongoing_status || false,
      executive_summary: dbData.analysis?.explanation || "Incident loaded from database.",
      key_facts: [],
    },
    risk_assessment: {
      risk_level: dbData.analysis?.risk_level || "Low Concern",
      risk_color: "#94A3B8",
      potential_scam_category: dbData.analysis?.potential_category || "",
      suspicious_indicators: tryParseJSON(dbData.analysis?.indicators, []),
      explanation: dbData.analysis?.explanation || "",
      uncertainty_note: "AI analysis identifies potential indicators only.",
      indicator_count: 0,
    },
    privacy_status: { status: "CLEAN", sensitive_data_found: false, warnings: [] },
    evidence_summary: {
      evidence_count: (dbData.evidence || []).length,
      summary: `${(dbData.evidence || []).length} evidence file(s) on record.`,
      inventory: dbData.evidence || [],
      missing_checklist: [],
    },
    incident_timeline: (dbData.timeline || []).map(t => ({
      event: t.event_description, timestamp: t.event_timestamp, source: t.source_type,
    })),
    reporting: {
      is_emergency: false,
      immediate_actions: ["File a complaint at cybercrime.gov.in", "Call 1930 for financial fraud"],
      reporting_steps: [],
      bank_contact_guidance: "Contact your bank only through the number on your card.",
      complaint_checklist: [],
      disclaimer: "CyberRakshak AI has NOT submitted any complaint on your behalf.",
    },
    awareness_tips: [],
    ai_powered_agents: {},
  };
}

function tryParseJSON(str, fallback) {
  try { return JSON.parse(str); } catch (_) { return fallback; }
}

function renderDashboard(apiResponse) {
  const dash = apiResponse?.data?.dashboard || apiResponse?.dashboard || {};
  const incId = apiResponse?.incident_id || dash?.incident_id || "—";
  const isDemo = (dash?.incident_summary?.executive_summary || "").includes("SYNTHETIC") ||
                 (dash?.incident_summary?.executive_summary || "").includes("DEMO");

  // Demo banner
  if (isDemo) document.getElementById("demoBanner")?.classList.remove("hidden");

  // AI mode banner
  const aiModes = dash?.ai_powered_agents || {};
  const llmMap  = dash?.llm_map || {};
  const anyAI = Object.values(aiModes).some(Boolean);
  const aiModeBanner = document.getElementById("aiModeBanner");
  if (aiModeBanner) {
    aiModeBanner.textContent = anyAI
      ? "✨ Multi-LLM Powered: IBM Granite ×3 · Google Gemini · Groq — AI analysis active"
      : "ℹ️ Running in deterministic fallback mode — Add API keys to .env to enable multi-LLM analysis";
  }

  // Emergency banner
  if (dash?.reporting?.is_emergency) {
    document.getElementById("emergencyBanner")?.classList.remove("hidden");
  }

  // Header
  setText("dashIncidentId", `Incident ID: ${incId}`);
  setText("dashGeneratedAt", dash?.generated_at ? `Generated: ${dash.generated_at}` : "");

  // Risk badge
  const riskLevel = dash?.risk_assessment?.risk_level || "Low Concern";
  const riskBadge = document.getElementById("dashRiskBadge");
  if (riskBadge) {
    riskBadge.textContent = riskLevel;
    riskBadge.className = "risk-badge " + getRiskClass(riskLevel);
  }

  setText("dashCategory", dash?.incident_summary?.category || "—");

  if (dash?.incident_summary?.ongoing) {
    document.getElementById("dashOngoing")?.classList.remove("hidden");
  }

  setText("dashExecutiveSummary", dash?.incident_summary?.executive_summary || "—");

  // Key facts chips
  const kfRow = document.getElementById("dashKeyFacts");
  if (kfRow) {
    (dash?.incident_summary?.key_facts || []).forEach(fact => {
      const chip = document.createElement("span");
      chip.className = "key-fact-chip";
      chip.textContent = fact;
      kfRow.appendChild(chip);
    });
  }

  // Meta
  setText("dashPlatform", dash?.incident_summary?.platform || "—");
  setText("dashDate", dash?.incident_summary?.incident_date || "—");
  const loss = dash?.incident_summary?.financial_loss;
  setText("dashLoss", loss > 0 ? `₹${Number(loss).toLocaleString("en-IN")}` : "—");

  // ── Privacy ──
  renderPrivacy(dash?.privacy_status || {});

  // ── Risk Assessment ──
  renderRisk(dash?.risk_assessment || {});

  // ── Evidence ──
  renderEvidence(dash?.evidence_summary || {}, dash?.incident_timeline || []);

  // ── Guidance ──
  renderGuidance(dash?.reporting || {});

  // ── Awareness ──
  renderAwarenessTips(dash?.awareness_tips || []);

  // ── Agent Status ──
  renderAgentStatus(apiResponse?.data?.execution_log || [], aiModes, llmMap);

  // ── Download report button ──
  const dlBtn = document.getElementById("downloadReportBtn");
  if (dlBtn && incId !== "—") {
    dlBtn.onclick = () => {
      window.open(`${API_BASE}/api/incidents/${encodeURIComponent(incId)}/report`, "_blank");
    };
  }
}

function renderPrivacy(privacy) {
  const badge = document.getElementById("privacyStatusBadge");
  const text  = document.getElementById("privacyStatusText");
  const list  = document.getElementById("privacyWarningsList");
  if (!badge) return;

  const isClean = privacy.status === "CLEAN" || !privacy.sensitive_data_found;
  badge.textContent = isClean ? "✅ CLEAN" : "⚠️ DATA REDACTED";
  badge.className = "privacy-status-badge " + (isClean ? "privacy-clean" : "privacy-redacted");
  if (text) text.textContent = isClean
    ? "No sensitive data detected in your submission."
    : "Sensitive information was detected and redacted before AI processing.";

  if (list) {
    list.innerHTML = "";
    (privacy.warnings || []).forEach(w => {
      const div = document.createElement("div");
      div.className = "privacy-warning-item";
      div.innerHTML = `<span>⚠️</span> <span>${escHtml(w)}</span>`;
      list.appendChild(div);
    });
  }
}

function renderRisk(risk) {
  const level = risk.risk_level || "Low Concern";
  const meter = document.getElementById("riskMeterValue");
  if (meter) {
    meter.textContent = level;
    meter.className = "risk-meter-value " + getRiskClass(level);
  }
  setText("riskScamCategory", risk.potential_scam_category || "—");
  setText("riskExplanation", risk.explanation || "");

  const indList = document.getElementById("indicatorsList");
  if (indList) {
    indList.innerHTML = "";
    const indicators = risk.suspicious_indicators || [];
    if (indicators.length === 0) {
      indList.innerHTML = '<span style="color:var(--text3);font-size:13px">No specific indicators detected.</span>';
    } else {
      indicators.forEach(ind => {
        const chip = document.createElement("span");
        chip.className = "indicator-chip";
        chip.textContent = ind;
        indList.appendChild(chip);
      });
    }
  }
  setText("uncertaintyNote", risk.uncertainty_note || "");
}

function renderEvidence(evidence, timeline) {
  const evList = document.getElementById("evidenceList");
  if (evList) {
    evList.innerHTML = "";
    const inventory = evidence.inventory || [];
    if (inventory.length === 0) {
      evList.innerHTML = '<div class="empty-state">No evidence files submitted.</div>';
    } else {
      inventory.forEach(ev => {
        const div = document.createElement("div");
        div.className = "evidence-item";
        const icon = ev.file_category === "image" ? "🖼️" : ev.file_category === "document" ? "📄" : "📎";
        div.innerHTML = `
          <span class="evidence-icon">${icon}</span>
          <div class="evidence-info">
            <div class="ev-name">${escHtml(ev.file_name)}</div>
            <div class="ev-meta">${escHtml(ev.evidence_category || ev.file_type || "")} · ${formatBytes(ev.size_bytes || 0)}</div>
          </div>`;
        evList.appendChild(div);
      });
    }
  }

  // Missing checklist
  const missingList = document.getElementById("missingEvidenceList");
  if (missingList) {
    missingList.innerHTML = "";
    (evidence.missing_checklist || []).forEach(item => {
      const div = document.createElement("div");
      div.className = "missing-item";
      div.innerHTML = `<span class="missing-checkbox">☐</span> <span>${escHtml(item)}</span>`;
      missingList.appendChild(div);
    });
  }

  // Timeline
  const tlList = document.getElementById("timelineList");
  if (tlList) {
    tlList.innerHTML = "";
    if (!timeline.length) {
      tlList.innerHTML = '<div class="empty-state">No timeline events.</div>';
    } else {
      timeline.forEach(ev => {
        const div = document.createElement("div");
        div.className = "timeline-item";
        const ts = ev.timestamp ? new Date(ev.timestamp).toLocaleString("en-IN") : "—";
        div.innerHTML = `
          <div>
            <div class="timeline-time">${escHtml(ts)}</div>
            <div class="timeline-event">${escHtml(ev.event || "")}</div>
            <div class="timeline-source">${escHtml(ev.source || "")}</div>
          </div>`;
        tlList.appendChild(div);
      });
    }
  }
}

function renderGuidance(reporting) {
  const actList = document.getElementById("immediateActionsList");
  if (actList) {
    actList.innerHTML = "";
    (reporting.immediate_actions || []).forEach((action, i) => {
      const div = document.createElement("div");
      div.className = "action-item";
      div.innerHTML = `<span class="action-num">${i + 1}.</span> <span>${escHtml(action)}</span>`;
      actList.appendChild(div);
    });
  }

  const stepList = document.getElementById("reportingStepsList");
  if (stepList) {
    stepList.innerHTML = "";
    (reporting.reporting_steps || []).forEach((step, i) => {
      const div = document.createElement("div");
      div.className = "step-item";
      div.innerHTML = `<span class="action-num">${i + 1}.</span> <span>${escHtml(step)}</span>`;
      stepList.appendChild(div);
    });
  }

  setText("bankGuidance", reporting.bank_contact_guidance || "");

  const ckList = document.getElementById("complaintChecklist");
  if (ckList) {
    ckList.innerHTML = "";
    (reporting.complaint_checklist || []).forEach(item => {
      const div = document.createElement("div");
      div.className = "checklist-item";
      div.innerHTML = `<span class="check-icon">☐</span> <span>${escHtml(item)}</span>`;
      ckList.appendChild(div);
    });
  }

  setText("dashDisclaimer", reporting.disclaimer || "");
}

function renderAwarenessTips(tips) {
  const list = document.getElementById("awarenessTipsList");
  if (!list) return;
  list.innerHTML = "";
  if (!tips.length) {
    list.innerHTML = '<div class="empty-state">No specific tips for this incident type.</div>';
    return;
  }
  tips.forEach(tip => {
    const div = document.createElement("div");
    div.className = "awareness-tip-item";
    div.innerHTML = `<span class="tip-icon">💡</span> <span>${escHtml(tip)}</span>`;
    list.appendChild(div);
  });
}

function renderAgentStatus(execLog, aiModes, llmMap) {
  const grid = document.getElementById("agentStatusGrid");
  if (!grid) return;
  grid.innerHTML = "";

  const agents = [
    { name: "Privacy Protection Agent",    key: "privacy",       defaultLlm: "Deterministic (regex)" },
    { name: "Incident Intake Agent",       key: "intake",        defaultLlm: "Llama 3.3 70B (watsonx)" },
    { name: "Scam Analysis Agent",         key: "scam_analysis", defaultLlm: "Llama 3.3 70B (watsonx)" },
    { name: "Evidence Organization Agent", key: "evidence",      defaultLlm: "Llama 3.3 70B (watsonx)" },
    { name: "Reporting Guidance Agent",    key: "reporting",     defaultLlm: "Gemini 3.5 Flash Lite" },
    { name: "Guidance Dashboard Agent",    key: "dashboard",     defaultLlm: "Groq Qwen3.8 27B" },
  ];

  agents.forEach(ag => {
    const logEntry  = execLog.find(e => e.agent === ag.name);
    const success   = !logEntry || logEntry.status === "success";
    const isAI      = ag.key && aiModes && aiModes[ag.key];
    const resolvedLlm = (llmMap && llmMap[ag.key]) || ag.defaultLlm;
    const isPrivacy  = ag.key === "privacy";
    // Evidence agent runs deterministic when no files uploaded — not a failure
    const isEvidence = ag.key === "evidence";

    const statusLabel = (isAI || isPrivacy)
      ? escHtml(resolvedLlm)
      : isEvidence
        ? "Deterministic (no files)"
        : "⚠ Fallback";

    const dotClass = success
      ? (isAI || isPrivacy || isEvidence ? "status-ai" : "status-success")
      : "status-error";

    const div = document.createElement("div");
    div.className = "agent-status-item";
    div.innerHTML = `
      <div class="agent-status-dot ${dotClass}"></div>
      <span class="agent-status-name">${escHtml(ag.name)}</span>
      <span class="agent-status-mode">${statusLabel}</span>
    `;
    grid.appendChild(div);
  });
}

/* ═══════════════════════════════════════════════════════════
   HELPERS
═══════════════════════════════════════════════════════════ */
function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text || "—";
}

function escHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatBytes(bytes) {
  if (!bytes) return "—";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function getRiskClass(level) {
  if (!level) return "risk-low";
  const l = level.toLowerCase();
  if (l.includes("critical")) return "risk-critical";
  if (l.includes("high"))     return "risk-high";
  if (l.includes("medium"))   return "risk-medium";
  return "risk-low";
}
