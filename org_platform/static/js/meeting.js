const meetingId = location.pathname.split("/").pop();
const state = {
  meeting: null,
  roster: [],
  voiceOn: true,
  speakingId: null,
  recognition: null,
};

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2400);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function pickVoice() {
  const voices = window.speechSynthesis?.getVoices?.() || [];
  const preferred = voices.find((v) => /Google US English|Samantha|Jenny|aria|natural/i.test(v.name))
    || voices.find((v) => v.lang?.startsWith("en") && v.localService)
    || voices.find((v) => v.lang?.startsWith("en"))
    || voices[0];
  return preferred;
}

function speak(text, agentId) {
  if (!state.voiceOn || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(text);
  const voice = pickVoice();
  if (voice) u.voice = voice;
  u.rate = 1.02;
  u.pitch = 1.0;
  u.onstart = () => {
    state.speakingId = agentId;
    paintParticipants();
  };
  u.onend = () => {
    if (state.speakingId === agentId) state.speakingId = null;
    paintParticipants();
  };
  window.speechSynthesis.speak(u);
}

function paintParticipants() {
  const root = document.getElementById("participants");
  const ids = state.meeting?.participant_ids || state.roster.map((r) => r.id);
  const byId = Object.fromEntries(state.roster.map((r) => [r.id, r]));
  root.innerHTML = ids
    .map((id) => {
      const a = byId[id];
      if (!a) return "";
      const speaking = state.speakingId === id ? "speaking" : "";
      return `<div class="participant ${speaking}">
        <div class="avatar" style="background:${a.color}">${a.avatar_initials}</div>
        <div>
          <div class="name" style="font-weight:600;font-size:0.9rem;">${a.name}</div>
          <div style="color:var(--muted);font-size:0.72rem;">${a.title}</div>
        </div>
        <div class="dot" title="present"></div>
      </div>`;
    })
    .join("");
}

function paintMessages() {
  const root = document.getElementById("messages");
  const msgs = state.meeting?.messages || [];
  root.innerHTML = msgs
    .map((m) => {
      const cls = m.kind === "human" ? "human" : "agent";
      return `<article class="bubble ${cls}">
        <div class="who">${m.sender_name}</div>
        <div>${escapeHtml(m.text)}</div>
      </article>`;
    })
    .join("");
  root.scrollTop = root.scrollHeight;
}

function paintEvents() {
  const root = document.getElementById("events");
  const events = state.meeting?.events || [];
  root.innerHTML = events.length
    ? events
        .map((e) => {
          if (e.type === "approval") {
            return `<div class="event approval"><strong>Approved</strong> by ${e.payload.by}<br/>${e.payload.note || e.payload.scope}</div>`;
          }
          if (e.type === "escalation") {
            return `<div class="event escalation"><strong>Escalated</strong> ${e.payload.from} → ${e.payload.to_name}</div>`;
          }
          return `<div class="event">${e.type}</div>`;
        })
        .join("")
    : `<div class="event">No escalations yet.</div>`;

  document.getElementById("meta").innerHTML = `
    <div class="event">Status: <strong>${state.meeting?.status}</strong></div>
    <div class="event">Chair: ${state.meeting?.chair_id}</div>
    <div class="event">Messages: ${state.meeting?.messages?.length || 0}</div>
    <div class="event">Created: ${state.meeting?.created_at ? new Date(state.meeting.created_at).toLocaleString() : "—"}</div>
  `;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function applySnapshot(meeting, roster) {
  state.meeting = meeting;
  if (roster) state.roster = roster;
  document.getElementById("meetingTitle").textContent = meeting.title;
  paintParticipants();
  paintMessages();
  paintEvents();
}

function handleBurst(payload) {
  if (payload.meeting) state.meeting = payload.meeting;
  paintMessages();
  paintEvents();
  const replies = payload.replies || [];
  // Speak agent replies in sequence for human-quality presence
  let delay = 0;
  replies.forEach((r) => {
    const text = r.text || r.meta?.text;
    const agentId = r.sender_id || r.meta?.agent_id;
    if (!text) return;
    setTimeout(() => speak(text, agentId), delay);
    delay += Math.min(6000, 800 + text.length * 15);
  });
}

function connectWs() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/meetings/${meetingId}`);
  state.ws = ws;
  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    if (data.type === "snapshot") applySnapshot(data.meeting, data.roster);
    if (data.type === "chat_burst") handleBurst(data);
    if (data.type === "meeting_ended") {
      applySnapshot(data.meeting, state.roster);
      toast("Meeting ended");
    }
  };
  ws.onclose = () => {
    setTimeout(connectWs, 1500);
  };
}

async function sendChat(text) {
  if (!text.trim()) return;
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: "chat", text }));
  } else {
    const data = await api(`/api/meetings/${meetingId}/messages`, {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    handleBurst(data);
  }
}

document.getElementById("composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chatInput");
  const text = input.value;
  input.value = "";
  try {
    await sendChat(text);
  } catch (err) {
    toast(String(err.message || err));
  }
});

document.getElementById("escalateBtn").addEventListener("click", async () => {
  try {
    const data = await api(`/api/meetings/${meetingId}/escalate`, {
      method: "POST",
      body: JSON.stringify({ reason: "Operator requested CEO escalation from meeting room" }),
    });
    handleBurst(data);
    toast("Escalated to CEO Chanan Zevin");
  } catch (err) {
    toast(String(err.message || err));
  }
});

document.getElementById("endBtn").addEventListener("click", async () => {
  await api(`/api/meetings/${meetingId}/end`, { method: "POST" });
});

document.getElementById("voiceToggle").addEventListener("click", (e) => {
  state.voiceOn = !state.voiceOn;
  e.target.textContent = state.voiceOn ? "Voice on" : "Voice off";
  if (!state.voiceOn) window.speechSynthesis?.cancel();
});

// Push-to-talk via Web Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = document.getElementById("micBtn");
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";
  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    document.getElementById("chatInput").value = text;
    sendChat(text);
    document.getElementById("voiceStatus").textContent = "Heard you — agents responding";
  };
  recognition.onerror = () => {
    document.getElementById("voiceStatus").textContent = "Mic error — type instead";
  };
  micBtn.addEventListener("mousedown", () => {
    try {
      recognition.start();
      document.getElementById("voiceStatus").textContent = "Listening…";
    } catch (_) {}
  });
  micBtn.addEventListener("mouseup", () => {
    try { recognition.stop(); } catch (_) {}
  });
  micBtn.addEventListener("touchstart", (e) => {
    e.preventDefault();
    try { recognition.start(); } catch (_) {}
  });
  micBtn.addEventListener("touchend", () => {
    try { recognition.stop(); } catch (_) {}
  });
} else {
  micBtn.disabled = true;
  document.getElementById("voiceStatus").textContent = "Speech recognition unavailable — TTS still active";
}

if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => pickVoice();
}

api(`/api/meetings/${meetingId}`)
  .then((data) => {
    applySnapshot(data.meeting, state.roster);
    return api("/api/org");
  })
  .then((org) => {
    state.roster = org.roster;
    paintParticipants();
    connectWs();
  })
  .catch((err) => toast(String(err.message || err)));
