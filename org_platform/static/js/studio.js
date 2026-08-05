const pathParts = location.pathname.split("/").filter(Boolean);
const state = {
  sessionId: pathParts[0] === "studio" && pathParts[1] ? pathParts[1] : null,
  session: null,
  stream: null,
  captureTimer: null,
  voiceUnlocked: false,
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

function setEnabled(on) {
  ["shareBtn", "stopShareBtn", "snapBtn", "chatInput", "micBtn", "deliverBtn"].forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (id === "shareBtn" || id === "chatInput" || id === "micBtn" || id === "deliverBtn") el.disabled = !on;
    if (id === "stopShareBtn" || id === "snapBtn") el.disabled = !(on && state.stream);
  });
  document.querySelector("#composer button[type=submit]").disabled = !on;
}

function paintMessages() {
  const root = document.getElementById("messages");
  const msgs = state.session?.messages || [];
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

function escapeHtml(s) {
  return String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function showFrame(url) {
  const video = document.getElementById("screenVideo");
  const img = document.getElementById("lastFrame");
  const empty = document.getElementById("emptyScreen");
  if (state.stream) {
    empty.style.display = "none";
    video.style.display = "block";
    img.style.display = "none";
  } else if (url) {
    empty.style.display = "none";
    video.style.display = "none";
    img.style.display = "block";
    img.src = url + "?t=" + Date.now();
  }
}

function applySession(session) {
  state.session = session;
  state.sessionId = session.id;
  paintMessages();
  document.getElementById("vpStatus").textContent = session.screen_sharing
    ? `Watching screen · ${session.frames?.length || 0} frames`
    : `In session · ${session.frames?.length || 0} frames received`;
  if (session.delivery) {
    document.getElementById("out").textContent = JSON.stringify(session.delivery, null, 2);
  }
  const last = (session.frames || [])[session.frames.length - 1];
  if (last?.path) showFrame(last.path);
  setEnabled(true);
  if (state.stream) {
    document.getElementById("stopShareBtn").disabled = false;
    document.getElementById("snapBtn").disabled = false;
  }
}

function connectWs() {
  if (!state.sessionId) return;
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/studio/${state.sessionId}`);
  state.ws = ws;
  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    if (data.type === "snapshot") applySession(data.session);
    if (data.session) applySession(data.session);
    if (data.type === "studio_chat" || data.type === "studio_delivery" || data.type === "studio_event") {
      if (data.vp) speak(data.vp.text);
      if (data.message?.kind === "agent") speak(data.message.text);
    }
  };
  ws.onclose = () => setTimeout(connectWs, 1500);
}

function speak(text) {
  if (!state.voiceUnlocked || !window.speechSynthesis || !text) return;
  const u = new SpeechSynthesisUtterance(text);
  const voices = speechSynthesis.getVoices();
  const male = voices.find((v) => /male|david|daniel|mark|google us english/i.test(v.name)) || voices.find((v) => v.lang?.startsWith("en"));
  if (male) u.voice = male;
  u.rate = 0.98;
  speechSynthesis.speak(u);
}

function unlockVoice() {
  if (!window.speechSynthesis) return;
  const warm = new SpeechSynthesisUtterance("VP Delivery Studio voice ready.");
  warm.volume = 0.01;
  speechSynthesis.speak(warm);
  state.voiceUnlocked = true;
}

async function startSession() {
  unlockVoice();
  const data = await api("/api/studio/sessions", {
    method: "POST",
    body: JSON.stringify({ title: "VP Delivery Studio — Screen Share Briefing" }),
  });
  history.replaceState({}, "", `/studio/${data.session.id}`);
  applySession(data.session);
  connectWs();
  toast("Studio session started — share your screen");
  speak(data.session.messages?.[0]?.text || "VP R&D joined.");
}

async function shareScreen() {
  if (!state.sessionId) return;
  unlockVoice();
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({
      video: { frameRate: 5 },
      audio: false,
    });
    state.stream = stream;
    const video = document.getElementById("screenVideo");
    video.srcObject = stream;
    video.style.display = "block";
    document.getElementById("emptyScreen").style.display = "none";
    document.getElementById("lastFrame").style.display = "none";
    document.getElementById("shareStatus").textContent = "Screen: live";
    document.getElementById("meCard").classList.add("live");
    document.getElementById("youCard").classList.add("live");
    document.getElementById("stopShareBtn").disabled = false;
    document.getElementById("snapBtn").disabled = false;
    await api(`/api/studio/sessions/${state.sessionId}/share`, {
      method: "POST",
      body: JSON.stringify({ active: true }),
    });
    // auto-send a frame so VP has visual evidence immediately
    await captureAndSend("auto");
    state.captureTimer = setInterval(() => captureAndSend("heartbeat").catch(() => {}), 8000);
    stream.getVideoTracks()[0].addEventListener("ended", () => stopShare());
    toast("Screen shared — VP can see frames");
  } catch (err) {
    toast("Screen share blocked or cancelled");
    console.error(err);
  }
}

async function stopShare() {
  if (state.captureTimer) clearInterval(state.captureTimer);
  state.captureTimer = null;
  if (state.stream) {
    state.stream.getTracks().forEach((t) => t.stop());
    state.stream = null;
  }
  const video = document.getElementById("screenVideo");
  video.srcObject = null;
  video.style.display = "none";
  document.getElementById("shareStatus").textContent = "Screen: off";
  document.getElementById("stopShareBtn").disabled = true;
  document.getElementById("snapBtn").disabled = true;
  document.getElementById("meCard").classList.remove("live");
  if (state.sessionId) {
    await api(`/api/studio/sessions/${state.sessionId}/share`, {
      method: "POST",
      body: JSON.stringify({ active: false }),
    });
  }
}

async function captureAndSend(note = "") {
  if (!state.stream || !state.sessionId) return;
  const video = document.getElementById("screenVideo");
  if (!video.videoWidth) return;
  const canvas = document.createElement("canvas");
  const maxW = 1280;
  const scale = Math.min(1, maxW / video.videoWidth);
  canvas.width = Math.round(video.videoWidth * scale);
  canvas.height = Math.round(video.videoHeight * scale);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const data_url = canvas.toDataURL("image/jpeg", 0.72);
  const res = await api(`/api/studio/sessions/${state.sessionId}/frames`, {
    method: "POST",
    body: JSON.stringify({ data_url, note }),
  });
  showFrame(res.frame.path);
  document.getElementById("vpStatus").textContent = `Watching screen · frame ${res.frame.id.slice(0, 8)}`;
  return res.frame;
}

async function sendChat(text) {
  if (!text.trim() || !state.sessionId) return;
  unlockVoice();
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(
      JSON.stringify({
        type: "chat",
        text,
        sender_id: "ceo-chanan",
        sender_name: "Me (Chanan Zevin)",
      })
    );
  } else {
    const data = await api(`/api/studio/sessions/${state.sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({
        text,
        sender_id: "ceo-chanan",
        sender_name: "Me (Chanan Zevin)",
      }),
    });
    applySession(data.session);
    if (data.vp) speak(data.vp.text);
  }
}

async function deliver() {
  if (!state.sessionId) return;
  const briefing =
    document.getElementById("chatInput").value.trim() ||
    [...(state.session?.messages || [])].reverse().find((m) => m.kind === "human")?.text ||
    "";
  if (!briefing) {
    toast("Explain the task first (type or speak)");
    return;
  }
  // ensure VP has a fresh frame if sharing
  if (state.stream) await captureAndSend("pre-delivery");
  const data = await api(`/api/studio/sessions/${state.sessionId}/deliver`, {
    method: "POST",
    body: JSON.stringify({
      briefing,
      owner: document.getElementById("owner").value,
      priority: "P1",
    }),
  });
  applySession(data.session);
  document.getElementById("out").textContent = JSON.stringify(
    { task_id: data.task.id, owner: data.task.owner, status: data.task.status, slack: data.delivery.slack_message_id },
    null,
    2
  );
  toast(`Delivered ${data.task.id} to DevOps`);
  speak(data.session.messages.slice(-1)[0]?.text || "Delivered to DevOps.");
}

document.getElementById("newSession").addEventListener("click", () => startSession().catch((e) => toast(String(e.message || e))));
document.getElementById("shareBtn").addEventListener("click", () => shareScreen().catch((e) => toast(String(e.message || e))));
document.getElementById("stopShareBtn").addEventListener("click", () => stopShare().catch((e) => toast(String(e.message || e))));
document.getElementById("snapBtn").addEventListener("click", () => captureAndSend("manual").then(() => toast("Frame sent to VP")).catch((e) => toast(String(e.message || e))));
document.getElementById("deliverBtn").addEventListener("click", () => deliver().catch((e) => toast(String(e.message || e))));
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

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const micBtn = document.getElementById("micBtn");
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = false;
  recognition.onresult = (ev) => {
    const text = ev.results[0][0].transcript;
    document.getElementById("chatInput").value = text;
    sendChat(text);
  };
  micBtn.addEventListener("mousedown", () => {
    try {
      recognition.start();
    } catch (_) {}
  });
  micBtn.addEventListener("mouseup", () => {
    try {
      recognition.stop();
    } catch (_) {}
  });
} else {
  micBtn.disabled = true;
}

if (state.sessionId) {
  api(`/api/studio/sessions/${state.sessionId}`)
    .then((d) => {
      applySession(d.session);
      connectWs();
      setEnabled(true);
    })
    .catch(() => toast("Session not found — start a new one"));
} else {
  setEnabled(false);
}
