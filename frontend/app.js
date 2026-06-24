const API = "";

let state = {
  provider: "",
  model: "",
  apiKey: "",
  agentId: "orchestrator",
  messages: [],
  providers: {},
  agents: [],
  sending: false,
};

// --- Init ---
async function init() {
  const [providersRes, agentsRes] = await Promise.all([
    fetch(`${API}/api/providers`).then((r) => r.json()),
    fetch(`${API}/api/agents`).then((r) => r.json()),
  ]);
  state.providers = providersRes;
  state.agents = agentsRes;

  renderProviders();
  renderAgents();
  loadSavedState();
  setupEventListeners();
}

// --- Render ---
function renderProviders() {
  const sel = document.getElementById("provider-select");
  sel.innerHTML = '<option value="">Select provider...</option>';
  for (const [id, info] of Object.entries(state.providers)) {
    sel.innerHTML += `<option value="${id}">${info.name}</option>`;
  }
}

function renderModels(providerId) {
  const sel = document.getElementById("model-select");
  sel.innerHTML = "";
  if (!providerId || !state.providers[providerId]) {
    sel.innerHTML = '<option value="">Select provider first</option>';
    return;
  }
  for (const m of state.providers[providerId].models) {
    sel.innerHTML += `<option value="${m.id}">${m.name}</option>`;
  }
  state.model = state.providers[providerId].models[0]?.id || "";
  updateBadge();
}

function renderAgents() {
  const list = document.getElementById("agent-list");
  list.innerHTML = "";
  const iconMap = {
    compass: "fa-compass",
    "drafting-compass": "fa-drafting-compass",
    "chart-line": "fa-chart-line",
    search: "fa-search",
    cogs: "fa-cogs",
  };
  for (const agent of state.agents) {
    const iconClass = iconMap[agent.icon] || "fa-robot";
    const active = agent.id === state.agentId ? "active" : "";
    list.innerHTML += `
      <div class="agent-item ${active}" data-id="${agent.id}">
        <div class="agent-icon"><i class="fas ${iconClass}"></i></div>
        <div class="agent-info">
          <div class="agent-name">${agent.name}</div>
          <div class="agent-desc">${agent.description}</div>
        </div>
      </div>`;
  }

  list.querySelectorAll(".agent-item").forEach((el) => {
    el.addEventListener("click", () => selectAgent(el.dataset.id));
  });
}

function selectAgent(id) {
  state.agentId = id;
  renderAgents();
  const agent = state.agents.find((a) => a.id === id);
  document.getElementById("current-agent-name").textContent =
    agent?.name || "Assistant";
  saveState();
}

function updateBadge() {
  const badge = document.getElementById("current-model-badge");
  if (state.model) {
    const provider = state.providers[state.provider];
    const model = provider?.models?.find((m) => m.id === state.model);
    badge.textContent = model?.name || state.model;
  } else {
    badge.textContent = "No model selected";
  }
}

// --- Messages ---
function addMessage(role, content, sources) {
  const container = document.getElementById("chat-messages");
  const welcome = document.getElementById("welcome-screen");
  if (welcome) welcome.style.display = "none";

  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}`;

  const avatarIcon = role === "user" ? "fa-user" : "fa-robot";
  const label = role === "user" ? "You" : getAgentName();

  let sourcesHtml = "";
  if (sources && sources.length > 0) {
    const uniqueSources = [...new Set(sources.map((s) => s.source))];
    sourcesHtml = `
      <div class="message-sources">
        <button class="sources-toggle" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'flex' : 'none'">
          <i class="fas fa-book"></i> ${uniqueSources.length} source(s) referenced
        </button>
        <div class="sources-list" style="display:none; margin-top:6px;">
          ${uniqueSources.map((s) => `<span class="source-tag">${s}</span>`).join("")}
        </div>
      </div>`;
  }

  msgDiv.innerHTML = `
    <div class="message-avatar"><i class="fas ${avatarIcon}"></i></div>
    <div class="message-content">
      <div class="role-label">${label}</div>
      <div class="message-body">${role === "user" ? escapeHtml(content) : renderMarkdown(content)}</div>
      ${sourcesHtml}
    </div>`;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function addThinking() {
  const container = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = "message assistant";
  div.id = "thinking-msg";
  div.innerHTML = `
    <div class="message-avatar"><i class="fas fa-robot"></i></div>
    <div class="message-content">
      <div class="role-label">${getAgentName()}</div>
      <div class="thinking"><span></span><span></span><span></span></div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function removeThinking() {
  document.getElementById("thinking-msg")?.remove();
}

function getAgentName() {
  return (
    state.agents.find((a) => a.id === state.agentId)?.name || "Assistant"
  );
}

// --- Chat ---
async function sendMessage(text) {
  if (!text.trim() || state.sending) return;
  if (!state.apiKey) {
    alert("Please enter your API key in the sidebar.");
    return;
  }
  if (!state.model) {
    alert("Please select a model.");
    return;
  }

  state.sending = true;
  updateSendButton();

  state.messages.push({ role: "user", content: text });
  addMessage("user", text);
  addThinking();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: state.provider,
        api_key: state.apiKey,
        model: state.model,
        agent_id: state.agentId,
        messages: state.messages,
      }),
    });

    removeThinking();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Request failed" }));
      addMessage("assistant", `**Error:** ${err.detail || "Something went wrong."}`);
      state.messages.pop();
    } else {
      const data = await res.json();
      state.messages.push({ role: "assistant", content: data.reply });
      addMessage("assistant", data.reply, data.sources);
    }
  } catch (e) {
    removeThinking();
    addMessage("assistant", `**Error:** Could not connect to the server. Is it running?`);
    state.messages.pop();
  }

  state.sending = false;
  updateSendButton();
}

function updateSendButton() {
  const btn = document.getElementById("send-btn");
  const input = document.getElementById("chat-input");
  btn.disabled = state.sending || !input.value.trim();
}

// --- Markdown ---
function renderMarkdown(text) {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, "<pre><code>$2</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^[-*] (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/<\/ul>\s*<ul>/g, "")
    .replace(/^\d+\. (.+)$/gm, "<li>$1</li>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/^(?!<)/, "<p>")
    .replace(/(?!>)$/, "</p>")
    .replace(/<p><(h[1-4]|ul|ol|pre|blockquote)/g, "<$1")
    .replace(/<\/(h[1-4]|ul|ol|pre|blockquote)><\/p>/g, "</$1>");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML.replace(/\n/g, "<br>");
}

// --- Persistence ---
function saveState() {
  localStorage.setItem(
    "we-agent",
    JSON.stringify({
      provider: state.provider,
      model: state.model,
      agentId: state.agentId,
      apiKey: state.apiKey,
    })
  );
}

function loadSavedState() {
  try {
    const saved = JSON.parse(localStorage.getItem("we-agent") || "{}");
    if (saved.provider) {
      state.provider = saved.provider;
      document.getElementById("provider-select").value = saved.provider;
      renderModels(saved.provider);
    }
    if (saved.model) {
      state.model = saved.model;
      document.getElementById("model-select").value = saved.model;
      updateBadge();
    }
    if (saved.apiKey) {
      state.apiKey = saved.apiKey;
      document.getElementById("api-key-input").value = saved.apiKey;
    }
    if (saved.agentId) {
      selectAgent(saved.agentId);
    }
  } catch {}
}

// --- Events ---
function setupEventListeners() {
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");

  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 150) + "px";
    updateSendButton();
  });

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input.value);
      input.value = "";
      input.style.height = "auto";
      updateSendButton();
    }
  });

  sendBtn.addEventListener("click", () => {
    sendMessage(input.value);
    input.value = "";
    input.style.height = "auto";
    updateSendButton();
  });

  document.getElementById("provider-select").addEventListener("change", (e) => {
    state.provider = e.target.value;
    renderModels(e.target.value);
    saveState();
  });

  document.getElementById("model-select").addEventListener("change", (e) => {
    state.model = e.target.value;
    updateBadge();
    saveState();
  });

  document.getElementById("api-key-input").addEventListener("input", (e) => {
    state.apiKey = e.target.value;
    saveState();
  });

  document.getElementById("toggle-key").addEventListener("click", () => {
    const inp = document.getElementById("api-key-input");
    const icon = document.querySelector("#toggle-key i");
    if (inp.type === "password") {
      inp.type = "text";
      icon.className = "fas fa-eye-slash";
    } else {
      inp.type = "password";
      icon.className = "fas fa-eye";
    }
  });

  document.getElementById("clear-chat").addEventListener("click", () => {
    state.messages = [];
    const container = document.getElementById("chat-messages");
    container.innerHTML = `
      <div class="welcome-screen" id="welcome-screen">
        <div class="welcome-icon"><i class="fas fa-compass"></i></div>
        <h2>Work Engineering Agent</h2>
        <p>Your AI-powered Work Design Engineering assistant. Select a model, enter your API key, and start asking questions.</p>
        <div class="starter-prompts">
          <button class="starter" data-prompt="What is Work Engineering and how does it differ from traditional org design?">What is Work Engineering?</button>
          <button class="starter" data-prompt="Help me classify the tasks in a Financial Analyst role using the A-E automation taxonomy.">Classify tasks for a role</button>
          <button class="starter" data-prompt="Walk me through the 10 scoping questions for a new Work Engineering engagement.">Scope an engagement</button>
          <button class="starter" data-prompt="What is the metabolic gap and how do I assess my organization's AI absorption capacity?">Explain metabolic gap</button>
          <button class="starter" data-prompt="Help me map the feedback loops that are preventing AI adoption in my organization.">Map change barriers</button>
          <button class="starter" data-prompt="How should I redesign our competency model for AI-augmented work?">Redesign competencies</button>
        </div>
      </div>`;
    attachStarterListeners();
  });

  document.getElementById("toggle-sidebar").addEventListener("click", () => {
    document.getElementById("sidebar").classList.toggle("open");
  });

  attachStarterListeners();
}

function attachStarterListeners() {
  document.querySelectorAll(".starter").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.getElementById("chat-input");
      input.value = btn.dataset.prompt;
      input.dispatchEvent(new Event("input"));
      sendMessage(btn.dataset.prompt);
      input.value = "";
      input.style.height = "auto";
      updateSendButton();
    });
  });
}

// --- Start ---
init();
