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
        ${a.photo ? `<img class="avatar-img" src="${a.photo}" alt="${a.name}" style="width:42px;height:42px;border-radius:50%;object-fit:cover;" />` : `<div class="avatar" style="background:${a.color}">${a.avatar_initials}</div>`}
        <div>
          <div class="name">${a.name}${a.join_seat === "me" ? " · ME" : a.join_seat === "you" ? " · YOU" : ""}</div>
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

  let oneOnOneId = null;
  try {
    oneOnOneId = localStorage.getItem("one_on_one_meeting_id");
  } catch (_) {
    oneOnOneId = null;
  }
  const liveOneOnOne = (meetings.meetings || []).find(
    (m) => m.status === "live" && /1:1|one[- ]?on[- ]?one/i.test(m.title || "")
  );
  if (liveOneOnOne) {
    setOneOnOneLink(liveOneOnOne.id);
  } else if (oneOnOneId) {
    setOneOnOneLink(oneOnOneId);
  }

  let meeting41bId = null;
  try {
    meeting41bId = localStorage.getItem("meeting_41b_id");
  } catch (_) {
    meeting41bId = null;
  }
  const live41b = (meetings.meetings || []).find(
    (m) => m.status === "live" && /41\s*b|meeting\s*41/i.test(m.title || "")
  );
  if (live41b) {
    set41bLink(live41b.id);
  } else if (meeting41bId) {
    set41bLink(meeting41bId);
  }
}

function setOneOnOneLink(meetingId) {
  const path = `/meeting/${meetingId}`;
  const absolute = `${location.origin}${path}`;
  const openLink = document.getElementById("openOneOnOneLink");
  const urlEl = document.getElementById("oneOnOneUrl");
  if (openLink) openLink.href = path;
  if (urlEl) urlEl.textContent = absolute;
  try {
    localStorage.setItem("one_on_one_meeting_id", meetingId);
  } catch (_) {
    /* ignore */
  }
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

function set41bLink(meetingId) {
  const path = `/meeting/${meetingId}`;
  const absolute = `${location.origin}${path}`;
  const openLink = document.getElementById("open41bLink");
  const urlEl = document.getElementById("meeting41bUrl");
  if (openLink) openLink.href = path;
  if (urlEl) urlEl.textContent = absolute;
  try {
    localStorage.setItem("meeting_41b_id", meetingId);
  } catch (_) {
    /* ignore */
  }
}

document.getElementById("launchOneOnOne").addEventListener("click", async () => {
  const btn = document.getElementById("launchOneOnOne");
  btn.disabled = true;
  try {
    const data = await api("/api/meetings", {
      method: "POST",
      body: JSON.stringify({
        title: "Ultra Agent Meeting 1:1",
        chair_id: "vp-rd",
        participant_ids: ["ceo-chanan", "vp-rd", "dev-tl-cursor"],
        seed_intro: true,
        morning: false,
        one_on_one: true,
      }),
    });
    setOneOnOneLink(data.meeting.id);
    toast("1:1 room ready");
    location.href = `/meeting/${data.meeting.id}`;
  } catch (err) {
    toast(String(err.message || err));
    btn.disabled = false;
  }
});

document.getElementById("launch41b")?.addEventListener("click", async () => {
  const btn = document.getElementById("launch41b");
  btn.disabled = true;
  try {
    const data = await api("/api/meetings/41b/ensure", { method: "POST" });
    set41bLink(data.meeting.id);
    toast(data.created ? "Meeting 41 B created" : "Meeting 41 B ready");
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
