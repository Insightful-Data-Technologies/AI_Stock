const state = { channel: "devops", channels: [] };

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

function paintChannels() {
  const root = document.getElementById("channels");
  root.innerHTML = state.channels
    .map(
      (c) => `<button class="chan ${c.id === state.channel ? "active" : ""}" data-id="${c.id}" type="button">
        #${c.id}
        <div style="color:var(--muted);font-size:0.72rem;">${c.message_count} messages</div>
      </button>`
    )
    .join("");
  root.querySelectorAll(".chan").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.channel = btn.dataset.id;
      document.getElementById("chanTitle").textContent = state.channel;
      paintChannels();
      loadMessages();
    });
  });
}

async function loadMessages() {
  const data = await api(`/api/channels/${state.channel}/messages`);
  const root = document.getElementById("messages");
  root.innerHTML = data.messages.length
    ? data.messages
        .slice()
        .reverse()
        .map(
          (m) => `<article class="msg">
            <div class="who">${m.sender_name} · ${new Date(m.ts).toLocaleString()} · ${m.priority}${m.escalation_label ? " · " + m.escalation_label : ""}</div>
            <div>${m.text}</div>
            ${m.attachments?.length ? `<div class="who">attachments: ${JSON.stringify(m.attachments)}</div>` : ""}
          </article>`
        )
        .join("")
    : `<div style="color:var(--muted)">No messages yet in #${state.channel}</div>`;
}

async function postMessage({ createTask }) {
  const sender_id = document.getElementById("sender").value;
  const text = document.getElementById("text").value.trim();
  const owner = document.getElementById("owner").value;
  if (!text) {
    toast("Write a message first");
    return;
  }

  // Always post to Slack channel
  const msgBody = {
    channel_id: state.channel,
    sender_id,
    text: createTask ? `TASK for <@${owner}>: ${text}` : text,
    mentions: createTask ? [owner, "devops-tl", "pm-devops"] : ["devops-tl"],
    priority: createTask ? "high" : "normal",
  };
  const posted = await api("/api/channels/messages", {
    method: "POST",
    body: JSON.stringify(msgBody),
  });

  let task = null;
  if (createTask) {
    const created = await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        title: text.slice(0, 120),
        description: text,
        business_objective: "DevOps execution via Slack #devops",
        acceptance_criteria: [
          "Acknowledged in #devops",
          "Evidence attached",
          "Public verification when deploy-related",
        ],
        created_by: sender_id,
        priority: "P1",
        target_environment: "production",
      }),
    });
    task = (
      await api(`/api/tasks/${created.task.id}/assign`, {
        method: "POST",
        body: JSON.stringify({
          owner,
          team_leader: owner.startsWith("devops-") && owner !== "devops-tl" ? "devops-tl" : "pm-devops",
          actor_id: sender_id,
        }),
      })
    ).task;

    // Follow-up message with task id
    await api("/api/channels/messages", {
      method: "POST",
      body: JSON.stringify({
        channel_id: state.channel,
        sender_id,
        text: `Assigned ${task.id} to ${owner}. Please acknowledge and report evidence in #devops / #agent-reports.`,
        mentions: [owner, "devops-tl"],
        priority: "high",
        attachments: [{ task_id: task.id }],
      }),
    });
  }

  document.getElementById("out").textContent = JSON.stringify(
    { channel: state.channel, message_id: posted.message.id, task_id: task?.id, owner: task?.owner },
    null,
    2
  );
  document.getElementById("text").value = "";
  toast(createTask ? `Task sent to DevOps (${task.id})` : "Posted to channel");
  await loadMessages();
  const ch = await api("/api/channels");
  state.channels = ch.channels;
  paintChannels();
}

document.getElementById("postOnly").addEventListener("click", () => postMessage({ createTask: false }).catch((e) => toast(String(e.message || e))));
document.getElementById("postTask").addEventListener("click", () => postMessage({ createTask: true }).catch((e) => toast(String(e.message || e))));

api("/api/channels")
  .then((data) => {
    state.channels = data.channels;
    paintChannels();
    return loadMessages();
  })
  .catch((e) => toast(String(e.message || e)));
