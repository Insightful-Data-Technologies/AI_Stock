async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

function renderRoster(roster) {
  const root = document.getElementById("roster");
  root.innerHTML = roster
    .map(
      (a) => `
    <article class="agent">
      <div class="avatar" style="background:${a.color}">${a.avatar_initials}</div>
      <div>
        <div class="name">${a.name}</div>
        <div class="title">${a.title}</div>
        <div class="meta">${a.team}${a.can_approve ? " · approver" : ""}${a.is_super_admin ? " · SUPER ADMIN" : ""}${a.is_ceo ? " · CEO" : ""}</div>
      </div>
    </article>`
    )
    .join("");

  const chair = document.getElementById("chair");
  chair.innerHTML = roster
    .map(
      (a) =>
        `<option value="${a.id}" ${a.is_super_admin ? "selected" : ""}>${a.name} — ${a.title}</option>`
    )
    .join("");
}

function renderMeetings(meetings) {
  const root = document.getElementById("meetings");
  if (!meetings.length) {
    root.innerHTML = `<div class="s" style="color:var(--muted)">No meetings yet — open the first room.</div>`;
    return;
  }
  root.innerHTML = meetings
    .map(
      (m) => `
    <a class="meet-item" href="/meeting/${m.id}">
      <div>
        <div class="t">${m.title}</div>
        <div class="s">${new Date(m.created_at).toLocaleString()} · ${m.message_count} messages</div>
      </div>
      <div class="status-${m.status}">${m.status}</div>
    </a>`
    )
    .join("");
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
    `Health OK · ${health.agents} agents · store ${health.store.primary}` +
    (health.store.redis_connected ? " · redis connected" : " · redis optional") +
    ` · target project ${health.project_target}`;
}

document.getElementById("createForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("title").value.trim();
  const chair_id = document.getElementById("chair").value;
  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true;
  try {
    const data = await api("/api/meetings", {
      method: "POST",
      body: JSON.stringify({ title, chair_id, seed_intro: true }),
    });
    toast("Meeting room opened");
    location.href = `/meeting/${data.meeting.id}`;
  } catch (err) {
    toast(String(err.message || err));
    btn.disabled = false;
  }
});

document.getElementById("refreshMeetings").addEventListener("click", async () => {
  const meetings = await api("/api/meetings");
  renderMeetings(meetings.meetings);
  toast("History refreshed");
});

boot().catch((err) => toast(String(err.message || err)));
