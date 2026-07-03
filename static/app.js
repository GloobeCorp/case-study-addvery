const apiBadge = document.querySelector("#apiBadge");
const modelStatus = document.querySelector("#modelStatus");
const keyPanel = document.querySelector("#keyPanel");
const keyForm = document.querySelector("#keyForm");
const apiKeyInput = document.querySelector("#apiKeyInput");
const keyMessage = document.querySelector("#keyMessage");
const researchForm = document.querySelector("#researchForm");
const questionInput = document.querySelector("#questionInput");
const runButton = document.querySelector("#runButton");
const runMessage = document.querySelector("#runMessage");
const finalPanel = document.querySelector("#finalPanel");
const finalTitle = document.querySelector("#finalTitle");
const finalAnswer = document.querySelector("#finalAnswer");
const sourceList = document.querySelector("#sourceList");
const auditPanel = document.querySelector("#auditPanel");
const auditLog = document.querySelector("#auditLog");

const cards = {
  "Research Agent": {
    card: document.querySelector("#researchCard"),
    output: document.querySelector("#researchOutput"),
    tool: document.querySelector("#researchTool"),
  },
  "Analysis Agent": {
    card: document.querySelector("#analysisCard"),
    output: document.querySelector("#analysisOutput"),
  },
  "Writer Agent": {
    card: document.querySelector("#writerCard"),
    output: document.querySelector("#writerOutput"),
  },
};

loadConfig();

keyForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  keyMessage.textContent = "";
  keyMessage.classList.remove("error");
  const apiKey = apiKeyInput.value.trim();
  if (!apiKey) {
    setMessage(keyMessage, "OpenAI API key je prázdný.", true);
    return;
  }

  try {
    const response = await fetch("/api/config/openai-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: apiKey }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "OpenAI API key se nepodařilo uložit.");
    }
    apiKeyInput.value = "";
    setMessage(keyMessage, "OpenAI API key je uložen lokálně.");
    await loadConfig();
  } catch (error) {
    setMessage(keyMessage, error.message, true);
  }
});

researchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) {
    setMessage(runMessage, "Zadej téma nebo otázku.", true);
    return;
  }

  resetRun();
  runButton.disabled = true;
  setMessage(runMessage, "Běží Research Agent...");
  setCardStatus("Research Agent", "running", "Běží");

  try {
    const response = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Výzkum skončil chybou.");
    }
    const result = await response.json();
    renderResult(result);
    setMessage(runMessage, "Hotovo. Výstupy jsou uložené v output/.");
  } catch (error) {
    setMessage(runMessage, error.message, true);
    setCardStatus("Research Agent", "error", "Chyba");
  } finally {
    runButton.disabled = false;
  }
});

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();
  modelStatus.innerHTML = `
    <span>Model: ${escapeHtml(config.model)}</span>
    <span>Search model: ${escapeHtml(config.search_model)}</span>
    <span>Vypracoval: Martin Sedláček</span>
  `;
  if (config.has_openai_api_key) {
    apiBadge.textContent = "API uložen";
    apiBadge.classList.add("ready");
    keyPanel.classList.add("hidden");
  } else {
    apiBadge.textContent = "API chybí";
    apiBadge.classList.remove("ready");
    keyPanel.classList.remove("hidden");
  }
}

function resetRun() {
  runMessage.textContent = "";
  runMessage.classList.remove("error");
  finalPanel.classList.add("hidden");
  auditPanel.classList.add("hidden");
  sourceList.innerHTML = "";
  auditLog.innerHTML = "";

  Object.values(cards).forEach(({ card, output }) => {
    const status = card.querySelector(".status");
    status.dataset.status = "pending";
    status.textContent = "Čeká";
    output.textContent = "-";
  });
  cards["Research Agent"].tool.textContent = "web_search(query)";
}

function renderResult(result) {
  for (const step of result.steps) {
    setCardStatus(step.agent_name, step.status, step.status === "done" ? "Hotovo" : step.status);
    if (step.agent_name === "Research Agent") {
      const query = result.research.search_query || "-";
      const tool = step.tool_calls?.[0];
      cards["Research Agent"].tool.textContent = tool
        ? `${tool.tool_name}(${JSON.stringify(tool.arguments, null, 2)})`
        : `web_search(${query})`;
      cards["Research Agent"].output.textContent =
        `${result.research.summary}\n\nZdroje: ${result.research.sources.length}\nMezery: ${result.research.gaps.join("; ") || "neuvedeno"}`;
    }
    if (step.agent_name === "Analysis Agent") {
      cards["Analysis Agent"].output.innerHTML = renderAnalysisOutput(result.analysis);
    }
    if (step.agent_name === "Writer Agent") {
      cards["Writer Agent"].output.textContent = result.writer.final_answer;
    }
  }

  finalTitle.textContent = result.writer.title || "Finální odpověď";
  finalAnswer.textContent = result.final_answer;
  sourceList.innerHTML = "";
  for (const source of result.writer.cited_sources) {
    const item = document.createElement("li");
    if (source.url) {
      const link = document.createElement("a");
      link.href = source.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = source.title || source.url;
      item.appendChild(link);
      item.append(` - ${source.relevance || source.snippet || ""}`);
    } else {
      item.textContent = `${source.title}: ${source.relevance || source.snippet || ""}`;
    }
    sourceList.appendChild(item);
  }
  finalPanel.classList.remove("hidden");

  auditLog.innerHTML = "";
  for (const step of result.steps) {
    const item = document.createElement("div");
    item.className = "audit-item";
    item.innerHTML = `
      <strong>${escapeHtml(step.agent_name)}</strong>
      <p>${escapeHtml(step.role)}</p>
      <p><b>Vstup:</b> ${escapeHtml(step.input_summary)}</p>
      <p><b>Výstup:</b> ${escapeHtml(step.output_summary)}</p>
      <p><b>Handoff:</b> ${escapeHtml(step.handoff_summary)}</p>
      <p><b>Messages:</b> ${step.messages.length} · <b>Tool calls:</b> ${step.tool_calls.length}</p>
      <details class="audit-detail">
        <summary>Messages / system prompt / tools</summary>
        <div class="audit-detail__section">
          <h3>System prompt</h3>
          <pre>${escapeHtml(step.system_prompt_excerpt || "Není dostupný.")}</pre>
        </div>
        <div class="audit-detail__section">
          <h3>Messages</h3>
          ${renderMessages(step.messages)}
        </div>
        <div class="audit-detail__section">
          <h3>Tool calls</h3>
          ${renderToolCalls(step.tool_calls)}
        </div>
      </details>
    `;
    auditLog.appendChild(item);
  }
  auditPanel.classList.remove("hidden");
}

function setCardStatus(agentName, status, label) {
  const entry = cards[agentName];
  if (!entry) return;
  const badge = entry.card.querySelector(".status");
  badge.dataset.status = status;
  badge.textContent = label;
}

function setMessage(element, text, isError = false) {
  element.textContent = text;
  element.classList.toggle("error", isError);
}

function renderAnalysisOutput(analysis) {
  return `
    <p>${escapeHtml(analysis.synthesis || "Syntéza není dostupná.")}</p>
    <div class="analysis-section">
      <h3>Závěry</h3>
      ${renderSimpleList(analysis.key_findings, "Žádné závěry nejsou k dispozici.")}
    </div>
    <div class="analysis-section">
      <h3>Hodnocení zdrojů podle Source Quality Skill</h3>
      ${renderSourceQualityTable(analysis.source_quality)}
    </div>
    <div class="analysis-section">
      <h3>Rizika</h3>
      ${renderSimpleList(analysis.risks_or_uncertainties, "Žádná rizika nejsou uvedená.")}
    </div>
  `;
}

function renderSimpleList(items, emptyText) {
  if (!items || items.length === 0) {
    return `<p class="muted">${escapeHtml(emptyText)}</p>`;
  }
  return `
    <ul class="compact-list">
      ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderSourceQualityTable(sourceQuality) {
  if (!sourceQuality || sourceQuality.length === 0) {
    return "<p class=\"muted\">Hodnocení zdrojů není k dispozici.</p>";
  }
  return `
    <div class="source-quality-table-wrap">
      <table class="source-quality-table">
        <thead>
          <tr>
            <th>Zdroj</th>
            <th>Skóre</th>
            <th>Důvod</th>
          </tr>
        </thead>
        <tbody>
          ${sourceQuality.map((source) => `
            <tr>
              <td>${renderSourceQualityTitle(source)}</td>
              <td><span class="source-quality-score">${escapeHtml(source.score)}</span></td>
              <td>${escapeHtml(source.reason || "Důvod není uveden.")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderSourceQualityTitle(source) {
  const title = escapeHtml(source.title || source.url || "Zdroj bez názvu");
  if (!isHttpUrl(source.url)) {
    return title;
  }
  return `<a href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer">${title}</a>`;
}

function isHttpUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function renderMessages(messages) {
  if (!messages || messages.length === 0) {
    return "<p class=\"muted\">Žádné messages nejsou k dispozici.</p>";
  }
  return messages
    .map((message, index) => {
      const content = normalizedMessageContent(message);
      return `
        <div class="message-record">
          <span>${index + 1}. ${escapeHtml(message.role)}</span>
          <pre>${escapeHtml(content)}</pre>
        </div>
      `;
    })
    .join("");
}

function normalizedMessageContent(message) {
  const content = String(message.content || "").trim();
  if (content) {
    return content;
  }
  if (message.role === "assistant") {
    return "Assistant zde nevrátil textovou odpověď, ale požádal o zavolání toolu. Detail najdeš v sekci Tool calls níže.";
  }
  if (message.role === "tool") {
    return "Tool nevrátil textový obsah.";
  }
  return "Tato zpráva nemá textový obsah.";
}

function renderToolCalls(toolCalls) {
  if (!toolCalls || toolCalls.length === 0) {
    return "<p class=\"muted\">Tento agent nevolal žádný tool.</p>";
  }
  return toolCalls
    .map((toolCall, index) => `
      <div class="message-record">
        <span>${index + 1}. ${escapeHtml(toolCall.tool_name)}</span>
        <pre>Arguments:
${escapeHtml(JSON.stringify(toolCall.arguments, null, 2))}

Output preview:
${escapeHtml(toolCall.output_preview)}</pre>
      </div>
    `)
    .join("");
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
