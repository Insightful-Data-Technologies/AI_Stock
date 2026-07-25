function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2800);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }
  if (!res.ok) throw new Error(data.detail || text || res.statusText);
  return data;
}

function payload(dryRunOverride) {
  const dry_run = dryRunOverride !== undefined ? dryRunOverride : document.getElementById("dryRun").checked;
  return {
    site_url: document.getElementById("siteUrl").value.trim(),
    domain: document.getElementById("domain").value.trim(),
    verification_txt: document.getElementById("verifyTxt").value.trim() || null,
    include_www: document.getElementById("includeWww").checked,
    apex_forward: document.getElementById("apexForward").checked,
    dry_run,
    api_key: document.getElementById("apiKey").value.trim() || null,
    api_secret: document.getElementById("apiSecret").value.trim() || null,
  };
}

function paintResult(data) {
  const plan = data.plan || data.job?.plan || {};
  const app = data.application || data.job?.application || {};
  const status = data.status || data.job?.status || "unknown";
  const pub = plan.public_urls || {};
  document.getElementById("summary").innerHTML = `
    <span class="status-pill ${status === "failed" ? "bad" : "ok"}">${status}</span>
    &nbsp; Studio: <a href="${pub.studio || "#"}" target="_blank" rel="noreferrer">${pub.studio || "—"}</a><br/>
    Domain www: <a href="${pub.www || "#"}" target="_blank" rel="noreferrer">${pub.www || "—"}</a>
    · apex: <a href="${pub.apex || "#"}" target="_blank" rel="noreferrer">${pub.apex || "—"}</a>
  `;
  document.getElementById("steps").innerHTML = (plan.steps || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("");
  document.getElementById("out").textContent = JSON.stringify(
    {
      status,
      credentials_configured: data.credentials_configured ?? data.job?.credentials_configured,
      records: plan.records,
      application: app,
      notes: plan.notes,
    },
    null,
    2
  );
}

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

async function loadJobs() {
  const data = await api("/api/publish/jobs");
  const root = document.getElementById("jobs");
  if (!data.jobs?.length) {
    root.innerHTML = `<div class="tiny">No publish jobs yet.</div>`;
    return;
  }
  root.innerHTML = data.jobs
    .slice(0, 12)
    .map(
      (j) => `<div class="job">
        <strong>${escapeHtml(j.domain || "")}</strong>
        ← ${escapeHtml(j.studio_host || "")}
        <div class="tiny">${escapeHtml(j.status)} · ${escapeHtml(j.created_at || "")} · ${j.dry_run ? "dry-run" : "live"}</div>
      </div>`
    )
    .join("");
}

async function refreshCredStatus() {
  const body = {
    api_key: document.getElementById("apiKey").value.trim() || null,
    api_secret: document.getElementById("apiSecret").value.trim() || null,
  };
  const data = await api("/api/publish/credentials", { method: "POST", body: JSON.stringify(body) });
  const el = document.getElementById("credStatus");
  if (data.ok) {
    el.className = "status-pill ok";
    el.textContent = `ok · ${data.domain_count || 0} domains`;
  } else if (data.configured) {
    el.className = "status-pill bad";
    el.textContent = `auth failed (${data.status_code || "?"})`;
  } else {
    el.className = "status-pill";
    el.textContent = "not configured";
  }
  return data;
}

document.getElementById("checkCreds").addEventListener("click", () => {
  refreshCredStatus().catch((e) => toast(String(e.message || e)));
});

document.getElementById("planBtn").addEventListener("click", async () => {
  try {
    const data = await api("/api/publish/plan", { method: "POST", body: JSON.stringify(payload(true)) });
    paintResult({ ...data, status: "planned" });
    toast("DNS plan ready");
  } catch (e) {
    toast(String(e.message || e));
  }
});

document.getElementById("publishForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const dry = document.getElementById("dryRun").checked;
    if (!dry) {
      const ok = confirm("This will WRITE DNS records on your GoDaddy domain. Continue?");
      if (!ok) return;
    }
    const data = await api("/api/publish", { method: "POST", body: JSON.stringify(payload()) });
    paintResult(data);
    await loadJobs();
    toast(dry ? "Dry-run saved" : data.status === "published" ? "Published to GoDaddy" : "Publish finished with errors");
  } catch (err) {
    toast(String(err.message || err));
  }
});

refreshCredStatus().catch(() => {});
loadJobs().catch(() => {});
