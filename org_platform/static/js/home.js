async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2800);
}

function renderRoster(roster) {
  const root = document.getElementById("roster");
  root.innerHTML = roster
    .map(
      (a) => `<article class="agent">
        <div class="avatar" style="background:${a.color}">${a.avatar_initials}</div>
        <div>
          <div class="name">${a.name}</div>
          <div class="title">${a.title}</div>
          <div class="meta">${a.team}${a.can_approve ? " · approver" : ""}${a.is_ceo ? " · CEO" : ""}${a.is_vp_rd ? " · VP R&D" : ""}${a.is_ea ? " · EA" : ""}</div>
        </div>
      </article>`
    )
    .join("");
  const chair = document.getElementById("chair");
  chair.innerHTML = roster
    .map((a) => `<option value="${a.id}" ${a.is_vp_rd ? "selected" : ""}>${a.name} — ${a.title}</option>`)
    .join("");
}

function renderMeetings(meetings) {
  const root = document.getElementById("meetings");
  root.innerHTML = meetings.length
    ? meetings
        .map(
          (m) => `<a class="meet-item" href="/meeting/${m.id}">
            <div><div class="t">${m.title}</div><div class="s">${new Date(m.created_at).toLocaleString()} · ${m.message_count} msgs</div></div>
            <div class="status-${m.status}">${m.status}</div>
          </a>`
        )
        .join("")
    : `<div style="color:var(--muted)">No meetings yet.</div>`;
}

async function boot() {
  const [org, health, meetings] = await Promise.all([
    api("/api/org"),
    api("/api/health"),
    api("/api/meetings"),
  ]);
  renderRoster(org.roster);
  renderMeetings(meetings.meetings);
  document.getElementById("health").textContent =
    `${health.company.legal_name} · ${health.agents} agents · ${health.channels} channels · email ${health.email.mode} · tasks ${health.tasks.total}`;
}

document.getElementById("createForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true;
  try {
    const data = await api("/api/meetings", {
      method: "POST",
      body: JSON.stringify({
        title: document.getElementById("title").value.trim(),
        chair_id: document.getElementById("chair").value,
        seed_intro: true,
        morning: document.getElementById("morning").checked,
      }),
    });
    location.href = `/meeting/${data.meeting.id}`;
  } catch (err) {
    toast(String(err.message || err));
    btn.disabled = false;
  }
});

document.getElementById("runComm").addEventListener("click", async () => {
  toast("Running communication tests…");
  const data = await api("/api/comm-tests/run-all", { method: "POST" });
  document.getElementById("opsOut").textContent = JSON.stringify(
    { status: data.status, tested: data.tested, passed: data.passed, blocked: data.blocked_agents, email: data.email_mode },
    null,
    2
  );
  toast(`Comm tests ${data.status}`);
});

document.getElementById("runE2E").addEventListener("click", async () => {
  toast("Running SRS workflow…");
  const data = await api("/api/workflows/e2e-demo", { method: "POST" });
  document.getElementById("opsOut").textContent = JSON.stringify(
    {
      status: data.status,
      morning_meeting_id: data.morning_meeting_id,
      dev_task: data.dev_task?.id,
      deploy_task: data.deploy_task?.id,
      blocker: data.blocker_task?.id,
      audit_events: data.audit_events,
    },
    null,
    2
  );
  toast(`SRS workflow ${data.status}`);
  const meetings = await api("/api/meetings");
  renderMeetings(meetings.meetings);
});

boot().catch((err) => toast(String(err.message || err)));
