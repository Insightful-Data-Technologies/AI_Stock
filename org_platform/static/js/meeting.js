const meetingId = location.pathname.split("/").pop();
const state = {
  meeting: null,
  roster: [],
  voiceOn: true,
  voiceUnlocked: false,
  speakingId: null,
  speakQueue: Promise.resolve(),
  speakAs: localStorage.getItem("meetingSpeakAs") || "me",
  mode41b: false,
  modeForecast: false,
  cameraStream: null,
  screenStream: null,
  listenOn: false,
  recognition: null,
  frameTimer: null,
  lastFrameCount: 0,
  avatarUrl: "/static/assets/avatar/agent-girl.mp4",
  avatarPoster: "/static/assets/avatar/agent-girl.png",
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
          setAgentSpeaking(true);
          document.getElementById("voiceStatus").textContent = `Speaking: ${agent?.name || "agent"}`;
        };
        u.onend = () => {
          if (state.speakingId === agentId) state.speakingId = null;
          paintParticipants();
          setAgentSpeaking(false);
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
  const you = state.modeForecast
    ? agentById("forecast-maya") || bySeat("you") || agentById("ea-sofia")
    : state.mode41b
    ? agentById("ea-sofia") || bySeat("you") || agentById("vp-rd")
    : bySeat("you") || agentById("vp-rd");
  if (me) {
    document.getElementById("mePhoto").src = me.photo;
    document.getElementById("meLabel").textContent = `Me: ${me.name}`;
  }
  if (you) {
    document.getElementById("youPhoto").src =
      state.mode41b || state.modeForecast ? state.avatarPoster : you.photo;
    document.getElementById("youLabel").textContent = state.modeForecast
      ? `You: ${you.name} · forecast`
      : state.mode41b
      ? `You: ${you.name} · human avatar`
      : `You: ${you.name}`;
  }
  document.getElementById("speakAs").value = state.speakAs;
}

function is41bMeeting(meeting) {
  if (!meeting) return false;
  if (reSearch41b(meeting.title || "")) return true;
  return (meeting.events || []).some((e) => e.type === "meeting_41b");
}

function isForecastMeeting(meeting) {
  if (!meeting) return false;
  if (/forecast|תחזית/i.test(meeting.title || "")) return true;
  return (meeting.events || []).some((e) => e.type === "forecast_one_on_one");
}

function reSearch41b(title) {
  return /41\s*b|meeting\s*41/i.test(title || "");
}

function updateSenseUI() {
  const sense = state.meeting?.sense || {};
  const hear = document.getElementById("hearPill");
  const see = document.getElementById("seePill");
  const detail = document.getElementById("senseDetail");
  if (!hear || !see) return;
  const heard = Boolean(sense.heard || state.listenOn);
  const seen = Boolean(sense.seen || (sense.frame_count || 0) > 0 || state.lastFrameCount > 0);
  hear.classList.toggle("on", heard);
  see.classList.toggle("on", seen);
  hear.textContent = heard ? "אני שומעת אותך" : "לא שומעת עדיין";
  see.textContent = seen
    ? `אני רואה אותך · ${sense.frame_count || state.lastFrameCount || 0} frames`
    : "לא רואה עדיין";
  if (detail) {
    detail.textContent = state.modeForecast
      ? "תחזית 1:1 · mic STT + camera frames"
      : "";
  }
}

function setAgentSpeaking(on) {
  const tile = document.getElementById("agentTile");
  const video = document.getElementById("agentAvatar");
  if (!tile || !video) return;
  tile.classList.toggle("speaking", Boolean(on));
  if (on) {
    video.play().catch(() => {});
  } else if (!state.mode41b && !state.modeForecast) {
    video.pause();
  }
}

async function enableAvatarStage(label) {
  const avatar = await api("/api/meetings/41b/avatar").catch(() => null);
  if (avatar?.poster_path) state.avatarPoster = avatar.poster_path;
  if (avatar?.video_path) state.avatarUrl = avatar.video_path;
  const poster = document.getElementById("agentPoster");
  const video = document.getElementById("agentAvatar");
  if (poster) poster.src = state.avatarPoster;
  if (video) {
    video.poster = state.avatarPoster;
    video.src = state.avatarUrl;
    video.classList.add("has-media");
    document.getElementById("agentTile")?.classList.add("has-media");
    video.play().catch(() => {});
  }
  document.getElementById("visualStatus").textContent = label;
}

async function enable41bVisuals() {
  state.mode41b = true;
  document.body.classList.add("mode-41b");
  await enableAvatarStage("41 B ready · turn on camera · share screen · human avatar voice");
  await startCamera();
  paintSeats();
}

async function enableForecastVisuals() {
  state.modeForecast = true;
  document.body.classList.add("mode-forecast");
  await enableAvatarStage("Forecast 1:1 · Listen on · Camera on · אני שומעת / רואה");
  await startCamera();
  startListening();
  startFrameLoop();
  paintSeats();
  updateSenseUI();
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    document.getElementById("visualStatus").textContent = "Camera API unavailable";
    return;
  }
  try {
    if (state.cameraStream) return;
    state.cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    const el = document.getElementById("meCamera");
    el.srcObject = state.cameraStream;
    document.getElementById("meTile")?.classList.add("has-media");
    document.getElementById("cameraBtn").textContent = "Camera on";
    document.getElementById("visualStatus").textContent = state.modeForecast
      ? "Camera on · frames go to forecast agent"
      : "Camera on you · avatar ready";
    if (state.modeForecast) startFrameLoop();
  } catch (err) {
    document.getElementById("visualStatus").textContent = "Camera blocked — allow webcam";
    console.error(err);
  }
}

function stopCamera() {
  if (state.cameraStream) {
    state.cameraStream.getTracks().forEach((t) => t.stop());
    state.cameraStream = null;
  }
  const el = document.getElementById("meCamera");
  if (el) el.srcObject = null;
  document.getElementById("meTile")?.classList.remove("has-media");
  document.getElementById("cameraBtn").textContent = "Camera off";
  stopFrameLoop();
}

function captureCameraFrame() {
  const video = document.getElementById("meCamera");
  if (!video || !state.cameraStream || video.videoWidth < 16) return null;
  const canvas = document.createElement("canvas");
  const w = Math.min(640, video.videoWidth);
  const h = Math.round((w / video.videoWidth) * video.videoHeight);
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, w, h);
  return canvas.toDataURL("image/jpeg", 0.7);
}

async function pushCameraFrame() {
  if (!state.modeForecast) return;
  const dataUrl = captureCameraFrame();
  if (!dataUrl) return;
  try {
    const data = await api(`/api/meetings/${meetingId}/frames`, {
      method: "POST",
      body: JSON.stringify({ data_url: dataUrl, source: "camera", note: "forecast-see" }),
    });
    if (data.meeting) state.meeting = data.meeting;
    state.lastFrameCount = (data.meeting?.frames || []).length;
    updateSenseUI();
    if (data.ack?.replies) {
      data.ack.replies.forEach((r) => enqueueSpeak(r.text, r.agent_id));
      paintMessages();
    }
  } catch (err) {
    console.error(err);
  }
}

function startFrameLoop() {
  if (state.frameTimer || !state.modeForecast) return;
  pushCameraFrame();
  state.frameTimer = setInterval(pushCameraFrame, 4000);
}

function stopFrameLoop() {
  if (state.frameTimer) {
    clearInterval(state.frameTimer);
    state.frameTimer = null;
  }
}

async function startScreenShare() {
  if (!navigator.mediaDevices?.getDisplayMedia) {
    toast("Screen share unavailable");
    return;
  }
  try {
    state.screenStream = await navigator.mediaDevices.getDisplayMedia({
      video: { frameRate: 8 },
      audio: false,
    });
    const el = document.getElementById("screenShare");
    el.srcObject = state.screenStream;
    document.getElementById("shareTile")?.classList.add("has-media");
    document.getElementById("stopShareBtn").disabled = false;
    document.getElementById("visualStatus").textContent = "Screen share live";
    state.screenStream.getVideoTracks()[0].addEventListener("ended", () => stopScreenShare());
    toast("Screen shared");
  } catch (err) {
    toast("Screen share blocked or cancelled");
    console.error(err);
  }
}

function stopScreenShare() {
  if (state.screenStream) {
    state.screenStream.getTracks().forEach((t) => t.stop());
    state.screenStream = null;
  }
  const el = document.getElementById("screenShare");
  if (el) el.srcObject = null;
  document.getElementById("shareTile")?.classList.remove("has-media");
  document.getElementById("stopShareBtn").disabled = true;
  document.getElementById("visualStatus").textContent = "Screen share off";
}

async function uploadAvatarFile(file) {
  if (!file) return;
  const body = new FormData();
  body.append("file", file);
  const res = await fetch("/api/meetings/41b/avatar", { method: "POST", body });
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  if (data.avatar?.video_path) {
    state.avatarUrl = `${data.avatar.video_path}?t=${Date.now()}`;
    const video = document.getElementById("agentAvatar");
    video.src = state.avatarUrl;
    document.getElementById("agentTile")?.classList.add("has-media");
    video.play().catch(() => {});
  }
  toast("Avatar video updated — human appearance ready");
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
  updateSenseUI();
}

function handleBurst(payload) {
  if (payload.meeting) state.meeting = payload.meeting;
  paintMessages();
  paintEvents();
  updateSenseUI();
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
    const you = state.modeForecast
      ? agentById("forecast-maya") || bySeat("you")
      : bySeat("you") || agentById("vp-rd");
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
    if (data.type === "frame" && data.meeting) {
      state.meeting = data.meeting;
      state.lastFrameCount = (data.meeting.frames || []).length;
      updateSenseUI();
    }
    if (data.type === "meeting_ended") {
      applySnapshot(data.meeting, state.roster);
      toast("Meeting ended");
    }
  };
  ws.onclose = () => setTimeout(connectWs, 1500);
}

async function sendChat(text, opts = {}) {
  if (!text.trim()) return;
  const identity = speakerIdentity();
  const source = opts.source || "typed";
  const heard = Boolean(opts.heard || source === "mic");
  const seen_frame_count = (state.meeting?.frames || []).length || state.lastFrameCount || 0;
  const payload = { type: "chat", text, ...identity, heard, source, seen_frame_count };
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify(payload));
  } else {
    const data = await api(`/api/meetings/${meetingId}/messages`, {
      method: "POST",
      body: JSON.stringify({ text, ...identity, heard, source, seen_frame_count }),
    });
    handleBurst(data);
  }
}

document.getElementById("enableVoiceBtn").addEventListener("click", unlockVoice);
document.getElementById("testVoiceBtn").addEventListener("click", () => {
  if (!state.voiceUnlocked) unlockVoice();
  const partner = state.modeForecast
    ? agentById("forecast-maya")
    : agentById("ea-sofia");
  enqueueSpeak(
    state.modeForecast
      ? "שלום חנן. אני Maya Forecast. אני שומעת אותך ורואה אותך — בואו נתחיל בתחזית."
      : state.mode41b
      ? "Hello Chanan. This is Meeting 41 B. My human avatar and voice are ready for our session tomorrow."
      : "Hello, this is Sofia Marchetti, Executive Assistant to CEO Chanan Zevin. Human voice check successful.",
    partner?.id || "ea-sofia"
  );
});

document.getElementById("cameraBtn")?.addEventListener("click", async () => {
  if (state.cameraStream) stopCamera();
  else await startCamera();
});
document.getElementById("shareBtn")?.addEventListener("click", () => startScreenShare());
document.getElementById("stopShareBtn")?.addEventListener("click", () => stopScreenShare());
document.getElementById("avatarUpload")?.addEventListener("change", async (e) => {
  try {
    await uploadAvatarFile(e.target.files?.[0]);
  } catch (err) {
    toast(String(err.message || err));
  }
});
document.getElementById("listenBtn")?.addEventListener("click", () => {
  if (state.listenOn) stopListening();
  else startListening();
});

document.getElementById("composer").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.voiceUnlocked) unlockVoice();
  const input = document.getElementById("chatInput");
  const text = input.value;
  input.value = "";
  try {
    await sendChat(text, { source: "typed", heard: false });
  } catch (err) {
    toast(String(err.message || err));
  }
});

document.getElementById("speakAs").addEventListener("change", (e) => {
  state.speakAs = e.target.value;
  localStorage.setItem("meetingSpeakAs", state.speakAs);
  toast(state.speakAs === "me" ? "Speaking as Me (CEO)" : state.speakAs === "you" ? "Speaking as You (AI)" : "Observer mode");
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

function wireRecognition(recognition) {
  recognition.continuous = Boolean(state.modeForecast);
  recognition.interimResults = false;
  recognition.lang = state.modeForecast ? "he-IL" : "en-US";
  recognition.onresult = (event) => {
    const text = event.results[event.results.length - 1][0].transcript;
    document.getElementById("chatInput").value = text;
    sendChat(text, { source: "mic", heard: true });
    document.getElementById("voiceStatus").textContent = "Heard you — forecast responding";
    updateSenseUI();
  };
  recognition.onerror = () => {
    document.getElementById("voiceStatus").textContent = "Mic error — type instead";
  };
  recognition.onend = () => {
    if (state.listenOn && state.modeForecast) {
      try {
        recognition.start();
      } catch (_) {}
    }
  };
  return recognition;
}

function startListening() {
  if (!state.recognition) {
    if (!SpeechRecognition) {
      toast("Speech recognition unavailable");
      return;
    }
    state.recognition = wireRecognition(new SpeechRecognition());
  } else {
    wireRecognition(state.recognition);
  }
  if (!state.voiceUnlocked) unlockVoice();
  try {
    state.recognition.start();
    state.listenOn = true;
    const btn = document.getElementById("listenBtn");
    if (btn) btn.textContent = "Listening…";
    document.getElementById("voiceStatus").textContent = "Listening continuously…";
    updateSenseUI();
  } catch (_) {}
}

function stopListening() {
  state.listenOn = false;
  try {
    state.recognition?.stop();
  } catch (_) {}
  const btn = document.getElementById("listenBtn");
  if (btn) btn.textContent = "Listen on";
  document.getElementById("voiceStatus").textContent = "Listen off";
  updateSenseUI();
}

if (SpeechRecognition) {
  state.recognition = wireRecognition(new SpeechRecognition());
  const start = () => {
    if (!state.voiceUnlocked) unlockVoice();
    try {
      state.recognition.start();
      document.getElementById("voiceStatus").textContent = "Listening…";
    } catch (_) {}
  };
  const stop = () => {
    if (state.listenOn) return;
    try {
      state.recognition.stop();
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
  const listenBtn = document.getElementById("listenBtn");
  if (listenBtn) listenBtn.disabled = true;
}

if (window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => pickVoice("female");
}

api(`/api/meetings/${meetingId}`)
  .then(async (data) => {
    applySnapshot(data.meeting, state.roster);
    if (isForecastMeeting(data.meeting)) {
      await enableForecastVisuals();
    } else if (is41bMeeting(data.meeting)) {
      await enable41bVisuals();
    }
    return api("/api/org");
  })
  .then((org) => {
    state.roster = org.roster;
    if (state.modeForecast) {
      state.roster = state.roster.map((a) => {
        if (a.id === "forecast-maya") {
          return { ...a, photo: state.avatarPoster, voice_gender: "female", join_seat: "you" };
        }
        if (a.id === "vp-rd") {
          return { ...a, join_seat: a.join_seat === "you" ? "" : a.join_seat };
        }
        return a;
      });
    } else if (state.mode41b) {
      // For 41 B, present the AI seat with Sofia's human girl appearance + female voice.
      state.roster = state.roster.map((a) => {
        if (a.id === "ea-sofia") {
          return { ...a, photo: state.avatarPoster, voice_gender: "female", join_seat: "you" };
        }
        if (a.id === "vp-rd") {
          return { ...a, join_seat: a.join_seat === "you" ? "" : a.join_seat };
        }
        return a;
      });
    }
    paintSeats();
    paintParticipants();
    paintMessages();
    updateSenseUI();
    connectWs();
  })
  .catch((err) => toast(String(err.message || err)));
