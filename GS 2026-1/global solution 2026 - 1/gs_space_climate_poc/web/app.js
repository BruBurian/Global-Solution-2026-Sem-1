const form = document.getElementById("predictForm");
const resultCard = document.getElementById("resultCard");
const runPipelineBtn = document.getElementById("runPipelineBtn");
const healthBtn = document.getElementById("healthBtn");
const pipelineStatus = document.getElementById("pipelineStatus");
const riskText = document.getElementById("riskText");
const riskLabel = document.getElementById("riskLabel");
const riskProbability = document.getElementById("riskProbability");
const meterBar = document.getElementById("meterBar");
const resultMessage = document.getElementById("resultMessage");
const predictBtn = document.getElementById("predictBtn");
const metricAccuracy = document.getElementById("metricAccuracy");
const metricF1 = document.getElementById("metricF1");
const metricAuc = document.getElementById("metricAuc");
const seedInput = document.getElementById("seedInput");
const historyBody = document.getElementById("historyBody");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");

const HISTORY_STORAGE_KEY = "space_climate_history_v1";
const HISTORY_MAX_ITEMS = 20;
const SEED_MIN = 0;
const SEED_MAX = 999999;

function readHistory() {
  try {
    const blob = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!blob) {
      return [];
    }
    const parsed = JSON.parse(blob);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeHistory(entries) {
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(entries));
}

function renderHistory() {
  const entries = readHistory();

  if (!entries.length) {
    historyBody.innerHTML = `
      <tr>
        <td class="history-empty" colspan="7">Sem testes salvos ainda.</td>
      </tr>
    `;
    return;
  }

  historyBody.innerHTML = entries
    .map((item) => {
      return `
        <tr>
          <td>${item.timestamp}</td>
          <td>${item.surface_temp_c.toFixed(1)} C</td>
          <td>${item.ndvi.toFixed(2)}</td>
          <td>${item.rainfall_mm_7d.toFixed(1)} mm</td>
          <td>${item.soil_moisture_pct.toFixed(1)}%</td>
          <td>${(item.risk_probability * 100).toFixed(2)}%</td>
          <td>${String(item.risk_text || "-").toUpperCase()}</td>
        </tr>
      `;
    })
    .join("");
}

function saveHistoryEntry(payload, result) {
  const now = new Date();
  const timestamp = now.toLocaleString("pt-BR", {
    hour12: false,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });

  const newEntry = {
    timestamp,
    surface_temp_c: Number(payload.surface_temp_c),
    ndvi: Number(payload.ndvi),
    rainfall_mm_7d: Number(payload.rainfall_mm_7d),
    soil_moisture_pct: Number(payload.soil_moisture_pct),
    risk_probability: Number(result.risk_probability) || 0,
    risk_text: String(result.risk_text || "-")
  };

  const current = readHistory();
  const updated = [newEntry, ...current].slice(0, HISTORY_MAX_ITEMS);
  writeHistory(updated);
  renderHistory();
}

function updateMetricCards(metrics) {
  metricAccuracy.textContent = metrics.accuracy ?? "-";
  metricF1.textContent = metrics.f1 ?? "-";
  metricAuc.textContent = metrics.roc_auc ?? "-";
}

async function loadMetrics() {
  const response = await fetch("/metrics");
  if (!response.ok) {
    return;
  }
  const metrics = await response.json();
  updateMetricCards(metrics);
}

async function checkHealth() {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error("api_offline");
  }
  const payload = await response.json();
  if (payload.status !== "ok") {
    throw new Error("api_unhealthy");
  }
}

function setResultTheme(probability) {
  resultCard.classList.remove("low", "medium", "high");
  if (probability >= 0.7) {
    resultCard.classList.add("high");
    return;
  }
  if (probability >= 0.4) {
    resultCard.classList.add("medium");
    return;
  }
  resultCard.classList.add("low");
}

async function sendPrediction(payload) {
  const response = await fetch("/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "request_failed" }));
    throw new Error(error.error || "request_failed");
  }

  return response.json();
}

runPipelineBtn.addEventListener("click", async () => {
  const seedValue = Number(seedInput.value);
  if (!Number.isInteger(seedValue) || seedValue < SEED_MIN || seedValue > SEED_MAX) {
    pipelineStatus.textContent = `Seed invalida. Use um inteiro de ${SEED_MIN} a ${SEED_MAX}.`;
    return;
  }

  runPipelineBtn.disabled = true;
  pipelineStatus.textContent = `Executando pipeline com seed ${seedValue}... isso pode levar alguns segundos.`;

  try {
    const response = await fetch("/run-pipeline", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ seed: seedValue })
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || "pipeline_failed");
    }

    updateMetricCards(result.metrics || {});
    const elapsed = result.elapsed_seconds ?? "-";
    const rows = result.dataset_rows ?? "-";
    const usedSeed = result.seed ?? seedValue;
    pipelineStatus.textContent = `Pipeline concluido em ${elapsed}s com seed ${usedSeed}. Dataset atualizado com ${rows} linhas.`;
  } catch (error) {
    pipelineStatus.textContent = `Falha ao executar pipeline: ${error.message}`;
  } finally {
    runPipelineBtn.disabled = false;
  }
});

healthBtn.addEventListener("click", async () => {
  healthBtn.disabled = true;
  try {
    await checkHealth();
    pipelineStatus.textContent = "API online e pronta para predicoes.";
  } catch {
    pipelineStatus.textContent = "API indisponivel no momento.";
  } finally {
    healthBtn.disabled = false;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = Object.fromEntries(new FormData(form).entries());
  for (const key of Object.keys(payload)) {
    payload[key] = Number(payload[key]);
  }

  predictBtn.disabled = true;
  predictBtn.textContent = "Calculando...";
  resultMessage.textContent = "Executando inferencia do modelo...";

  try {
    const result = await sendPrediction(payload);
    const probability = Number(result.risk_probability) || 0;

    riskText.textContent = String(result.risk_text || "-").toUpperCase();
    riskLabel.textContent = String(result.risk_label ?? "-");
    riskProbability.textContent = `${(probability * 100).toFixed(2)}%`;
    meterBar.style.width = `${Math.min(100, Math.max(0, probability * 100))}%`;

    setResultTheme(probability);

    if (probability >= 0.7) {
      resultMessage.textContent = "Cenario com risco alto de seca. Recomendado monitoramento imediato.";
    } else if (probability >= 0.4) {
      resultMessage.textContent = "Cenario de atencao. Acompanhar variacao de chuva e umidade do solo.";
    } else {
      resultMessage.textContent = "Cenario estavel no momento, com risco baixo de seca.";
    }

    saveHistoryEntry(payload, result);
  } catch (error) {
    riskText.textContent = "ERRO";
    riskLabel.textContent = "-";
    riskProbability.textContent = "-";
    meterBar.style.width = "0%";
    resultCard.classList.remove("low", "medium", "high");
    resultMessage.textContent = `Falha na predicao: ${error.message}`;
  } finally {
    predictBtn.disabled = false;
    predictBtn.textContent = "Calcular risco";
  }
});

clearHistoryBtn.addEventListener("click", () => {
  writeHistory([]);
  renderHistory();
  pipelineStatus.textContent = "Historico de testes limpo.";
});

loadMetrics();
checkHealth()
  .then(() => {
    pipelineStatus.textContent = "API online. Voce pode executar pipeline ou testar predicoes.";
  })
  .catch(() => {
    pipelineStatus.textContent = "API nao respondeu no carregamento inicial.";
  });

renderHistory();
