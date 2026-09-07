const get = (selector) => document.querySelector(selector);
const input = get("#command-input");
const form = get("#text-form");
const runButton = get("#run-button");
const recordButton = get("#record-button");
const requestStatus = get("#request-status");
let recorder;
let chunks = [];
let requestInFlight = false;

function text(selector, value, fallback = "--") { get(selector).textContent = value ?? fallback; }
function number(value, digits = 0) { return Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "--"; }
function localClock(value) {
  if (!value) return "--";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "--" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function setBusy(busy, label = "Ready") {
  requestInFlight = busy;
  runButton.disabled = busy;
  recordButton.disabled = busy && recorder?.state !== "recording";
  requestStatus.textContent = label;
}
function renderHealth(data) {
  text("#backend-status", data.home_assistant_reachable ? "HA · Connected" : "HA · Offline");
  text("#llm-status", `${data.ollama_reachable ? "LLM" : "LLM offline"} · ${data.llm_model || "Unknown"}`);
  text("#stt-status", `STT · ${data.stt_model || "Unknown"}`);
  get("#backend-status").classList.toggle("ok", Boolean(data.home_assistant_reachable));
  get("#llm-status").classList.toggle("ok", Boolean(data.ollama_reachable));
  get("#stt-status").classList.toggle("ok", Boolean(data.stt_configured));
}
function renderContext(context) {
  const room = context?.living_room || {};
  const curtain = room.curtain || {};
  const solar = context?.solar || {};
  const outdoor = context?.outdoor || {};
  text("#temperature-value", number(room.temperature_c, 1));
  text("#humidity-value", number(room.humidity_percent, 1));
  text("#illuminance-value", number(room.illuminance_lux));
  text("#curtain-value", curtain.state ? curtain.state.toUpperCase() : "--");
  text("#curtain-position", `${number(curtain.position)}% · Matter · Home Assistant`);
  text("#context-time", `Updated ${localClock(context?.captured_at)}`);
  text("#sunrise-value", localClock(solar.sunrise));
  text("#sunset-value", localClock(solar.sunset));
  text("#sun-position-value", solar.azimuth_deg == null ? "--" : `${number(solar.azimuth_deg)}° azimuth · ${number(solar.elevation_deg)}° elevation`);
  text("#window-value", solar.living_room_window_azimuth_deg == null ? "Not configured" : `${number(solar.living_room_window_azimuth_deg)}° SW · ${number(solar.sun_to_window_angle_deg)}° from sun`);
  text("#outdoor-temperature", `${number(outdoor.temperature_c, 1)} °C`);
  text("#cloud-value", `${number(outdoor.cloud_cover_percent)} %`);
  text("#radiation-value", `${number(outdoor.direct_radiation_wm2)} W/m²`);
  text("#rain-value", `${number(outdoor.precipitation_probability_percent)} %`);
}
function renderCurtainDevice(devices) {
  const curtain = devices?.["cover.living_room_curtain"];
  if (!curtain) return;
  text("#curtain-value", curtain.state?.toUpperCase());
  text("#curtain-position", `${number(curtain.position)}% · Matter · Home Assistant`);
}
function renderTrace(data) {
  const trace = data.llm_trace || {};
  text("#trace-output", JSON.stringify({ llm_mode: data.llm_mode, stt_mode: data.stt_mode, raw_model_output: trace.raw_model_output, normalization_applied: trace.normalization_applied, policy_applied: trace.policy_applied, parsed_before_normalization: trace.parsed_before_normalization, parsed_after_policy: trace.parsed_after_policy, home_context: data.home_context, error: trace.error }, null, 2));
}
function renderDecision(data) {
  const commands = data.parsed?.commands || [];
  const applied = data.result?.applied || [];
  const errors = data.result?.errors || [];
  const actionLabel = commands.length ? commands.map((command) => `${command.action} → ${command.entity_id}`).join(", ") : "No physical action";
  text("#transcript-output", data.transcript || data.input_text);
  text("#response-output", data.parsed?.response);
  text("#intent-output", data.parsed?.intent || "none");
  text("#action-output", actionLabel);
  text("#json-output", JSON.stringify(data.parsed, null, 2));
  text("#result-output", JSON.stringify(data.result, null, 2));
  renderTrace(data);
  renderContext(data.home_context);
  renderCurtainDevice(data.devices);
  const state = get("#execution-state");
  state.className = "execution-state";
  if (errors.length) { state.textContent = "Execution failed"; state.classList.add("error"); }
  else if (!commands.length) { state.textContent = "Safely suppressed · no-op"; state.classList.add("suppressed"); }
  else if (applied.some((item) => item.state_verified === false)) { state.textContent = "IR preset sent · AC state unverified"; state.classList.add("pending"); }
  else if (applied.every((item) => item.settled !== false)) { state.textContent = "Physical state confirmed"; state.classList.add("success"); }
  else { state.textContent = "Command accepted · state updating"; state.classList.add("pending"); }
}
async function jsonFetch(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}
async function refreshContext() {
  if (requestInFlight) return;
  try {
    const data = await jsonFetch("/api/context");
    renderContext(data.home_context);
    if (requestStatus.textContent.startsWith("Context unavailable")) requestStatus.textContent = "Ready";
  }
  catch (error) { requestStatus.textContent = `Context unavailable: ${error.message}`; }
}
async function runTextCommand(command) {
  if (!command.trim()) return;
  setBusy(true, "Reading context and running local LLM…");
  try {
    const data = await jsonFetch("/api/command/text", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: command }) });
    renderDecision(data);
    requestStatus.textContent = "Complete";
  } catch (error) {
    requestStatus.textContent = `Failed: ${error.message}`;
    text("#response-output", error.message);
    const state = get("#execution-state"); state.textContent = "Execution failed"; state.className = "execution-state error";
  } finally { setBusy(false, requestStatus.textContent); }
}
form.addEventListener("submit", (event) => { event.preventDefault(); runTextCommand(input.value); });
recordButton.addEventListener("click", async () => {
  if (recorder?.state === "recording") { recorder.stop(); recordButton.textContent = "Record voice"; requestStatus.textContent = "Transcribing audio…"; return; }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorder = new MediaRecorder(stream); chunks = [];
    recorder.ondataavailable = (event) => chunks.push(event.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
      setBusy(true, "STT → context → local LLM → Home Assistant…");
      const formData = new FormData(); formData.append("file", new Blob(chunks, { type: "audio/webm" }), "command.webm");
      try {
        const data = await jsonFetch("/api/command/audio", { method: "POST", body: formData });
        input.value = data.transcript; renderDecision(data); requestStatus.textContent = "Complete";
      } catch (error) { requestStatus.textContent = `Failed: ${error.message}`; text("#response-output", error.message); }
      finally { setBusy(false, requestStatus.textContent); }
    };
    recorder.start(); recordButton.textContent = "Stop recording"; requestStatus.textContent = "Listening…";
  } catch (error) { requestStatus.textContent = `Microphone unavailable: ${error.message}`; }
});
async function initialize() {
  try {
    const [health, context] = await Promise.all([jsonFetch("/api/health"), jsonFetch("/api/context")]);
    renderHealth(health); renderContext(context.home_context);
  } catch (error) { requestStatus.textContent = `Startup check failed: ${error.message}`; }
}
initialize();
setInterval(refreshContext, 10000);
