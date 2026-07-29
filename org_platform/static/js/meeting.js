const meetingId = location.pathname.split("/").pop();
const state = {
  meeting: null,
  roster: [],
  voiceOn: true,
  voiceUnlocked: false,
  speakingId: null,
  speakQueue: Promise.resolve(),
  speakAs: localStorage.getItem("meetingSpeakAs") || "me",
};

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function bySeat(seat) {
  return state.roster.find((a) => a.join_seat === seat);
}

function agentById(id) {
  return state.roster.find((a) => a.id === id);
}

function pickVoice(gender = "male") {
  const voices = window.speechSynthesis?.getVoices?.() || [];
  if (!voices.length) return null;
  const en = voices.filter((v) => (v.lang || "").toLowerCase().startsWith("en"));
  const pool = en.length ? en : voices;
  const femaleHints = /female|woman|zira|samantha|victoria|karen|moira|tessa|fiona|veena|susan|linda|jenny|aria|google us english female|microsoft aria|microsoft jenny|microsoft zira/i;
  const maleHints = /male|man|david|mark|daniel|alex|fred|google us english male|microsoft david|microsoft guy|microsoft tony/i;
  const preferred = pool.filter((v) => (gender === "female" ? femaleHints : maleHints).test(`${v.name} ${v.voiceURI}`));
  const natural = (preferred.length ? preferred : pool).find((v) => /natural|neural|premium|enhanced|google|microsoft/i.test(v.name))
    || (preferred[0] || pool[0]);
  return natural;
}

function unlockVoice() {
  if (!window.speechSynthesis) {
    toast("Speech synthesis unavailable in this browser");
    return;
  }
  // Warm-up utterance required by Chrome autoplay policy
  const warm = new SpeechSynthesisUtterance("Voice enabled.");
  warm.volume = 0.01;
  warm.rate = 1.1;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(warm);
  state.voiceUnlocked = true;
  document.getElementById("voiceUnlock").classList.add("hidden");
  document.getElementById("voiceStatus").textContent = "Human voices ready";
  // Re-speak latest agent lines after unlock
  const recent = (state.meeting?.messages || []).filter((m) => m.kind === "agent").slice(-3);
  recent.forEach((m) => enqueueSpeak(m.text, m.sender_id));
}

function enqueueSpeak(text, agentId) {
  if (!state.voiceOn || !state.voiceUnlocked || !window.speechSynthesis) return;
  state.speakQueue = state.speakQueue.then(
    () =>
      new Promise((resolve) => {
        const agent = agentById(agentId);
        const gender = agent?.voice_gender || "male";
        const u = new SpeechSynthesisUtterance(text);
        const voice = pickVoice(gender);
        if (voice) u.voice = voice;
        u.rate = gender === "female" ? 1.02 : 0.98;
        u.pitch = gender === "female" ? 1.12 : 0.92;
        u.onstart = () => {
          state.speakingId = agentId;
          paintParticipants();
          document.getElementById("voiceStatus").textContent = `Speaking: ${agent?.name || "agent"}`;
        };
        u.onend = () => {
          if (state.speakingId === agentId) state.speakingId = null;
          paintParticipants();
          resolve();
        };
        u.onerror = () => resolve();
        window.speechSynthesis.speak(u);
      })
  );
}

function avatarHtml(a, sizeClass = "avatar-img") {
  if (a?.photo) return `<img class="${sizeClass}" src="${a.photo}" alt="${a.name}" />`;
  return `<div class="avatar" style="background:${a?.color || "#444"}">${a?.avatar_initials || "?"}</div>`;
}

function paintSeats() {
  const me = bySeat("me") || agentById("ceo-chanan");
  const you = bySeat("you") || agentById("vp-rd");
  if (me) {
    document.getElementById("mePhoto").src = me.photo;
    document.getElementById("meLabel").textContent = `Me: ${me.name}`;
  }
  if (you) {
    document.getElementById("youPhoto").src = you.photo;
    document.getElementById("youLabel").textContent = `You: ${you.name}`;
  }
  document.getElementById("speakAs").value = state.speakAs;
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
      const seat = a.join_seat === "me" ? " · ME" : a.join_seat === "you" ? " · YOU" : "";
      return `<div class="participant ${speaking}">
        ${avatarHtml(a)}
        <div>
          <div class="name" style="font-weight:600;font-size:0.9rem;">${a.name}${seat}</div>
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
  const byId = Object.fromEntries(state.roster.map((r) => [r.id, r]));
  root.innerHTML = msgs
    .map((m) => {
      const cls = m.kind === "human" ? "human" : "agent";
      const a = byId[m.sender_id];
      const photo = a?.photo
        ? `<img src="${a.photo}" alt="" style="width:22px;height:22px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:0.35rem;" />`
        : "";
      return `<article class="bubble ${cls}">
        <div class="who">${photo}${m.sender_name}</div>
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
    <div class="event">Voice: ${state.voiceUnlocked ? "unlocked" : "needs click"}</div>
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
  paintSeats();
  paintParticipants();
  paintMessages();
  paintEvents();
}

function handleBurst(payload) {
  if (payload.meeting) state.meeting = payload.meeting;
  paintMessages();
  paintEvents();
  (payload.replies || []).forEach((r) => {
    enqueueSpeak(r.text || r.meta?.text || "", r.sender_id || r.meta?.agent_id);
  });
}

function speakerIdentity() {
  if (state.speakAs === "me") {
    const me = bySeat("me") || agentById("ceo-chanan");
    return { sender_id: me.id, sender_name: `Me (${me.name})` };
  }
  if (state.speakAs === "you") {
    const you = bySeat("you") || agentById("vp-rd");
    return { sender_id: you.id, sender_name: `You (${you.name})` };
  }
  return { sender_id: "human-operator", sender_name: "Observer" };
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
  ws.onclose = () => setTimeout(connectWs, 1500);
}

async function sendChat(text) {
  if (!text.trim()) return;
  const identity = speakerIdentity();
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: "chat", text, ...identity }));
  } else {
    const data = await api(`/api/meetings/${meetingId}/messages`, {
      method: "POST",
      body: JSON.stringify({ text, ...identity }),
    });
    handleBurst(data);
  }
}

document.getElementById("enableVoiceBtn").addEventListener("click", unlockVoice);
document.getElementById("testVoiceBtn").addEventListener("click", () => {
  if (!state.voiceUnlocked) unlockVoice();
  const sofia = agentById("ea-sofia");
  enqueueSpeak(
    "Hello, this is Sofia Marchetti, Executive Assistant to CEO Chanan Zevin. Human voice check successful.",
    sofia?.id || "ea-sofia"
  );
});

document.getElementById("composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.voiceUnlocked) unlockVoice();
  const input = document.getElementById("chatInput");
  const text = input.value;
  input.value = "";
  try {
    await sendChat(text);
  } catch (err) {
    toast(String(err.message || err));
  }
});

document.getElementById("speakAs").addEventListener("change", (e) => {
  state.speakAs = e.target.value;
  localStorage.setItem("meetingSpeakAs", state.speakAs);
  toast(state.speakAs === "me" ? "Speaking as Me (CEO)" : state.speakAs === "you" ? "Speaking as You (VP R&D)" : "Observer mode");
});

document.getElementById("escalateBtn").addEventListener("click", async () => {
  if (!state.voiceUnlocked) unlockVoice();
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
  const start = () => {
    if (!state.voiceUnlocked) unlockVoice();
    try {
      recognition.start();
      document.getElementById("voiceStatus").textContent = "Listening…";
    } catch (_) {}
  };
  const stop = () => {
    try {
      recognition.stop();
    } catch (_) {}
  };
  micBtn.addEventListener("mousedown", start);
  micBtn.addEventListener("mouseup", stop);
  micBtn.addEventListener("touchstart", (e) => {
    e.preventDefault();
    start();
  });
  micBtn.addEventListener("touchend", stop);
} else {
  micBtn.disabled = true;
  document.getElementById("voiceStatus").textContent = "Speech recognition unavailable — TTS still active";
}

if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => pickVoice("female");
}

api(`/api/meetings/${meetingId}`)
  .then((data) => {
    applySnapshot(data.meeting, state.roster);
    return api("/api/org");
  })
  .then((org) => {
    state.roster = org.roster;
    paintSeats();
    paintParticipants();
    paintMessages();
    connectWs();
  })
  .catch((err) => toast(String(err.message || err)));
