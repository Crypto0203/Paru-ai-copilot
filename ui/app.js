/**
 * PARU PRO - Advanced 3D Autonomous AI Desktop Copilot
 * Features: Three.js 3D Holographic Particle Sphere, GSAP Smooth Transitions,
 * Direct Hardware Audio Streaming, WebSocket Telemetry, and Instant Tool Dispatch.
 */

// Global State
let isListening = false;
let isSpeaking = false;
let isProcessing = false;
let isRecordingAudio = false;

let audioContext = null;
let analyser = null;
let visualizerAnimationId = null;

let recordingStream = null;
let recordingContext = null;
let scriptProcessor = null;
let audioBuffers = [];
let silenceTimer = null;

// Three.js Globals
let threeScene, threeCamera, threeRenderer;
let particleSphere, particleGeometry, originalPositions;
let innerCore, ringMesh1, ringMesh2;

// DOM Elements
const orbWrapper = document.getElementById("orbWrapper");
const statePill = document.getElementById("statePill");
const stateText = document.getElementById("stateText");
const btnMic = document.getElementById("btnMic");
const feedMessages = document.getElementById("feedMessages");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const audioPlayer = document.getElementById("audioPlayer");
const btnVision = document.getElementById("btnVision");
const btnSettings = document.getElementById("btnSettings");
const btnClearFeed = document.getElementById("btnClearFeed");
const settingsModal = document.getElementById("settingsModal");
const btnCloseSettings = document.getElementById("btnCloseSettings");
const btnCancelSettings = document.getElementById("btnCancelSettings");
const btnSaveSettings = document.getElementById("btnSaveSettings");
const inputApiKey = document.getElementById("inputApiKey");
const selectVoice = document.getElementById("selectVoice");
const inputUserName = document.getElementById("inputUserName");

const hudClock = document.getElementById("hudClock");
const hudBattery = document.getElementById("hudBattery");
const hudCpu = document.getElementById("hudCpu");

const canvas = document.getElementById("audioVisualizer");
const ctx = canvas ? canvas.getContext("2d") : null;

// =======================================================
// 1. THREE.JS 3D HOLOGRAPHIC PARTICLE SPHERE
// =======================================================
function initThreeOrb() {
  const container = document.getElementById("threeOrbCanvas");
  if (!container || typeof THREE === "undefined") {
    console.warn("Three.js not loaded or container missing.");
    return;
  }

  container.innerHTML = "";
  const width = 280;
  const height = 280;

  threeScene = new THREE.Scene();
  threeCamera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  threeCamera.position.z = 3.2;

  threeRenderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
  threeRenderer.setSize(width, height);
  threeRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(threeRenderer.domElement);

  // 1. Particle Sphere Cloud (1,800 points)
  const particleCount = 1800;
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  originalPositions = new Float32Array(particleCount * 3);

  const colorCyan = new THREE.Color("#00f2fe");
  const colorPurple = new THREE.Color("#7928ca");
  const colorGreen = new THREE.Color("#00f076");

  for (let i = 0; i < particleCount; i++) {
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(Math.random() * 2 - 1);
    const r = 0.95 + (Math.random() - 0.5) * 0.12;

    const x = r * Math.sin(phi) * Math.cos(theta);
    const y = r * Math.sin(phi) * Math.sin(theta);
    const z = r * Math.cos(phi);

    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    originalPositions[i * 3] = x;
    originalPositions[i * 3 + 1] = y;
    originalPositions[i * 3 + 2] = z;

    const mixed = colorCyan.clone().lerp(colorPurple, Math.random() * 0.85);
    colors[i * 3] = mixed.r;
    colors[i * 3 + 1] = mixed.g;
    colors[i * 3 + 2] = mixed.b;
  }

  particleGeometry = new THREE.BufferGeometry();
  particleGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  particleGeometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const particleMaterial = new THREE.PointsMaterial({
    size: 0.045,
    vertexColors: true,
    transparent: true,
    opacity: 0.95,
    blending: THREE.AdditiveBlending
  });

  particleSphere = new THREE.Points(particleGeometry, particleMaterial);
  threeScene.add(particleSphere);

  // 2. Holographic Geometric Core (Icosahedron wireframe)
  const coreGeo = new THREE.IcosahedronGeometry(0.62, 1);
  const coreMat = new THREE.MeshBasicMaterial({
    color: 0x00f2fe,
    wireframe: true,
    transparent: true,
    opacity: 0.45
  });
  innerCore = new THREE.Mesh(coreGeo, coreMat);
  threeScene.add(innerCore);

  // 3. Glowing Orbital Rings
  const ringGeo1 = new THREE.TorusGeometry(1.22, 0.012, 16, 100);
  const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x00f2fe, transparent: true, opacity: 0.5 });
  ringMesh1 = new THREE.Mesh(ringGeo1, ringMat1);
  ringMesh1.rotation.x = Math.PI / 3;
  threeScene.add(ringMesh1);

  const ringGeo2 = new THREE.TorusGeometry(1.35, 0.01, 16, 100);
  const ringMat2 = new THREE.MeshBasicMaterial({ color: 0x7928ca, transparent: true, opacity: 0.4 });
  ringMesh2 = new THREE.Mesh(ringGeo2, ringMat2);
  ringMesh2.rotation.y = Math.PI / 4;
  threeScene.add(ringMesh2);

  // 4. Render Animation Loop
  function animateThree() {
    requestAnimationFrame(animateThree);

    const time = Date.now() * 0.0018;
    particleSphere.rotation.y += 0.007;
    particleSphere.rotation.x += 0.003;
    innerCore.rotation.y -= 0.012;
    innerCore.rotation.z += 0.006;
    ringMesh1.rotation.z += 0.005;
    ringMesh2.rotation.x -= 0.004;

    // Audio Frequency Reactivity
    let avg = 0;
    if (analyser && (isSpeaking || isRecordingAudio)) {
      const freqData = new Uint8Array(analyser.frequencyBinCount);
      analyser.getByteFrequencyData(freqData);
      avg = freqData.reduce((a, b) => a + b, 0) / freqData.length;
    }

    const boost = 1 + (avg / 255) * 0.5;
    const posArr = particleGeometry.attributes.position.array;

    for (let i = 0; i < particleCount; i++) {
      const noise = Math.sin(time * 5 + i * 0.4) * 0.06 * (avg > 0 ? (avg / 75) : 0.4);
      posArr[i * 3] = originalPositions[i * 3] * (boost + noise);
      posArr[i * 3 + 1] = originalPositions[i * 3 + 1] * (boost + noise);
      posArr[i * 3 + 2] = originalPositions[i * 3 + 2] * (boost + noise);
    }
    particleGeometry.attributes.position.needsUpdate = true;

    // Dynamic Color Shift on state
    if (isRecordingAudio) {
      innerCore.material.color.setHex(0x00f076);
      ringMesh1.material.color.setHex(0x00f076);
    } else if (isSpeaking) {
      innerCore.material.color.setHex(0x00f2fe);
      ringMesh1.material.color.setHex(0x7928ca);
    } else {
      innerCore.material.color.setHex(0x00f2fe);
      ringMesh1.material.color.setHex(0x00f2fe);
    }

    threeRenderer.render(threeScene, threeCamera);
  }
  animateThree();
}

// =======================================================
// 2. AUDIO VISUALIZER (BOTTOM SOUNDWAVE)
// =======================================================
function initVisualizer() {
  if (!canvas) return;
  canvas.width = canvas.parentElement.clientWidth || 320;
  canvas.height = canvas.parentElement.clientHeight || 28;
}

function drawVisualizerWave(frequencies = null) {
  if (!ctx || !canvas) return;
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  const bufferLength = frequencies ? frequencies.length : 24;
  const barWidth = width / bufferLength;
  let x = 0;

  for (let i = 0; i < bufferLength; i++) {
    let barHeight = frequencies 
      ? (frequencies[i] / 255) * height * 0.95 
      : isRecordingAudio ? Math.sin(Date.now() * 0.005 + i * 0.3) * 8 + 8 : 3;
    
    barHeight = Math.max(3, barHeight);

    const gradient = ctx.createLinearGradient(0, height - barHeight, 0, height);
    if (isSpeaking) {
      gradient.addColorStop(0, "#00f2fe");
      gradient.addColorStop(1, "#7928ca");
    } else if (isRecordingAudio) {
      gradient.addColorStop(0, "#00f076");
      gradient.addColorStop(1, "#00a854");
    } else {
      gradient.addColorStop(0, "#00f2fe");
      gradient.addColorStop(1, "#1c2538");
    }

    ctx.fillStyle = gradient;
    ctx.fillRect(x, height / 2 - barHeight / 2, barWidth - 2, barHeight);
    x += barWidth;
  }
}

function animateIdleVisualizer() {
  drawVisualizerWave();
  visualizerAnimationId = requestAnimationFrame(animateIdleVisualizer);
}

// =======================================================
// 3. SOUND EFFECTS & STATE MANAGEMENT
// =======================================================
function playWakeChime() {
  try {
    const actx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = actx.createOscillator();
    const gain = actx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(587.33, actx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(880.00, actx.currentTime + 0.12);

    gain.gain.setValueAtTime(0.2, actx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, actx.currentTime + 0.28);

    osc.connect(gain);
    gain.connect(actx.destination);
    osc.start();
    osc.stop(actx.currentTime + 0.28);
  } catch (e) {}
}

function setAssistantState(state, message = "") {
  if (!statePill || !stateText) return;
  statePill.className = `state-pill ${state}`;

  switch(state) {
    case "listening":
      stateText.textContent = message || "LISTENING... (SPEAK NOW)";
      statePill.style.borderColor = "var(--accent-green)";
      statePill.style.color = "var(--accent-green)";
      if (btnMic) btnMic.classList.add("active");
      break;
    case "thinking":
      stateText.textContent = message || "PROCESSING...";
      statePill.style.borderColor = "#e056fd";
      statePill.style.color = "#e056fd";
      if (btnMic) btnMic.classList.remove("active");
      break;
    case "speaking":
      stateText.textContent = message || "SPEAKING...";
      statePill.style.borderColor = "#00f2fe";
      statePill.style.color = "#00f2fe";
      if (btnMic) btnMic.classList.remove("active");
      break;
    default:
      stateText.textContent = "SECURE STANDBY";
      statePill.style.borderColor = "var(--border-color)";
      statePill.style.color = "var(--text-secondary)";
      if (btnMic) btnMic.classList.remove("active");
  }

  // GSAP subtle state bounce
  if (typeof gsap !== "undefined") {
    gsap.fromTo(statePill, { scale: 0.96 }, { scale: 1.0, duration: 0.25, ease: "back.out(2)" });
  }
}

function resetToStandby() {
  isProcessing = false;
  isSpeaking = false;
  isRecordingAudio = false;
  setAssistantState("idle");
}

// =======================================================
// 4. CHAT FEED & MESSAGE RENDERING (GSAP POWERED)
// =======================================================
function appendMessage(role, text, toolData = null) {
  if (!feedMessages) return;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble msg-${role}`;

  const author = document.createElement("div");
  author.className = "msg-author";
  author.textContent = role === "assistant" ? "PARU AI" : "USER";

  const content = document.createElement("div");
  content.className = "msg-content";
  content.textContent = text;

  bubble.appendChild(author);
  bubble.appendChild(content);

  if (toolData && Array.isArray(toolData)) {
    toolData.forEach(t => {
      const toolTag = document.createElement("div");
      toolTag.className = "msg-bubble tool-pill";
      toolTag.style.marginTop = "0.4rem";
      
      let resultText = typeof t.result === "object" ? (t.result.message || JSON.stringify(t.result)) : t.result;
      let url = t.result && t.result.url ? t.result.url : (typeof t.result === "string" && t.result.startsWith("http") ? t.result : null);
      
      if (url) {
        toolTag.innerHTML = `🔧 <code>${t.name}</code>: <a href="${url}" target="_blank" style="color: #00f2fe; text-decoration: underline;">${resultText} (Click to Open)</a>`;
      } else {
        toolTag.innerHTML = `🔧 <code>${t.name}</code>: ${resultText}`;
      }
      bubble.appendChild(toolTag);
    });
  }

  feedMessages.appendChild(bubble);
  feedMessages.scrollTop = feedMessages.scrollHeight;

  // GSAP Smooth Physics Reveal Animation
  if (typeof gsap !== "undefined") {
    gsap.from(bubble, {
      y: 18,
      opacity: 0,
      duration: 0.32,
      ease: "power2.out"
    });
  }
}

// =======================================================
// 5. HARDWARE AUDIO RECORDER (WAV PCM ENCODER)
// =======================================================
function bufferToWav(buffer) {
  let numOfChan = buffer.numberOfChannels,
      length = buffer.length * numOfChan * 2 + 44,
      out = new DataView(new ArrayBuffer(length)),
      channels = [], i, sample,
      offset = 0, pos = 0;

  function setUint16(data) { out.setUint16(pos, data, true); pos += 2; }
  function setUint32(data) { out.setUint32(pos, data, true); pos += 4; }

  // RIFF header
  out.setUint8(pos++, 0x52); out.setUint8(pos++, 0x49); out.setUint8(pos++, 0x46); out.setUint8(pos++, 0x46);
  setUint32(length - 8);
  out.setUint8(pos++, 0x57); out.setUint8(pos++, 0x41); out.setUint8(pos++, 0x56); out.setUint8(pos++, 0x45);

  // fmt chunk
  out.setUint8(pos++, 0x66); out.setUint8(pos++, 0x6d); out.setUint8(pos++, 0x74); out.setUint8(pos++, 0x20);
  setUint32(16);
  setUint16(1);
  setUint16(numOfChan);
  setUint32(buffer.sampleRate);
  setUint32(buffer.sampleRate * 2 * numOfChan);
  setUint16(numOfChan * 2);
  setUint16(16);

  // data chunk
  out.setUint8(pos++, 0x64); out.setUint8(pos++, 0x61); out.setUint8(pos++, 0x74); out.setUint8(pos++, 0x61);
  setUint32(length - pos - 4);

  for (i = 0; i < buffer.numberOfChannels; i++)
    channels.push(buffer.getChannelData(i));

  while (offset < buffer.length) {
    for (i = 0; i < numOfChan; i++) {
      sample = Math.max(-1, Math.min(1, channels[i][offset]));
      sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
      out.setInt16(pos, sample, true);
      pos += 2;
    }
    offset++;
  }
  return new Blob([out], { type: "audio/wav" });
}

async function startVoiceRecording() {
  if (isRecordingAudio || isSpeaking) return;
  try {
    recordingStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordingContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    if (recordingContext.state === "suspended") {
      await recordingContext.resume();
    }

    const source = recordingContext.createMediaStreamSource(recordingStream);
    analyser = recordingContext.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);

    scriptProcessor = recordingContext.createScriptProcessor(4096, 1, 1);
    audioBuffers = [];

    scriptProcessor.onaudioprocess = (e) => {
      if (!isRecordingAudio) return;
      const input = e.inputBuffer.getChannelData(0);
      audioBuffers.push(new Float32Array(input));
    };

    source.connect(scriptProcessor);
    scriptProcessor.connect(recordingContext.destination);

    isRecordingAudio = true;
    playWakeChime();
    setAssistantState("listening", "LISTENING... (CLICK TO SEND)");

    // Live wave animation
    cancelAnimationFrame(visualizerAnimationId);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    function renderLiveMic() {
      if (isRecordingAudio) {
        analyser.getByteFrequencyData(dataArray);
        drawVisualizerWave(dataArray);
        requestAnimationFrame(renderLiveMic);
      }
    }
    renderLiveMic();

    if (silenceTimer) clearTimeout(silenceTimer);
    silenceTimer = setTimeout(() => {
      if (isRecordingAudio) stopVoiceRecording();
    }, 6000);

  } catch (err) {
    console.error("Mic access error:", err);
    appendMessage("assistant", `Microphone Notice: ${err.message}. Please allow mic access.`);
    resetToStandby();
  }
}

async function stopVoiceRecording() {
  if (!isRecordingAudio) return;
  isRecordingAudio = false;
  if (silenceTimer) clearTimeout(silenceTimer);

  setAssistantState("thinking", "PROCESSING VOICE...");

  if (scriptProcessor) {
    scriptProcessor.disconnect();
    scriptProcessor = null;
  }
  if (recordingStream) {
    recordingStream.getTracks().forEach(t => t.stop());
    recordingStream = null;
  }

  let totalLength = audioBuffers.reduce((acc, b) => acc + b.length, 0);
  if (totalLength < 1600) {
    resetToStandby();
    return;
  }

  let merged = new Float32Array(totalLength);
  let offset = 0;
  for (let b of audioBuffers) {
    merged.set(b, offset);
    offset += b.length;
  }

  let audioBuffer = recordingContext.createBuffer(1, totalLength, recordingContext.sampleRate);
  audioBuffer.getChannelData(0).set(merged);
  let wavBlob = bufferToWav(audioBuffer);

  let formData = new FormData();
  formData.append("file", wavBlob, "voice.wav");

  try {
    const res = await fetch("/api/voice_upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (data.transcript) {
      appendMessage("user", data.transcript);
    }
    if (data.response) {
      setAssistantState("speaking");
      appendMessage("assistant", data.response, data.tool_called);
      if (data.audio_url) {
        playAudioResponse(data.audio_url);
      } else {
        setTimeout(resetToStandby, 2500);
      }
    } else {
      resetToStandby();
    }
  } catch (err) {
    appendMessage("assistant", `Voice error: ${err.message}`);
    resetToStandby();
  }
}

function manualMicTrigger() {
  if (isRecordingAudio) {
    stopVoiceRecording();
  } else {
    startVoiceRecording();
  }
}

// Play Audio Response with Visualizer Hook
function playAudioResponse(url) {
  if (!audioPlayer) return;
  isSpeaking = true;
  audioPlayer.src = url;
  
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 64;
    const source = audioContext.createMediaElementSource(audioPlayer);
    source.connect(analyser);
    analyser.connect(audioContext.destination);
  }

  audioPlayer.play().catch(e => console.warn("Audio autoplay blocked:", e));

  const dataArray = new Uint8Array(analyser.frequencyBinCount);
  function renderLiveAudio() {
    if (!audioPlayer.paused && !audioPlayer.ended) {
      analyser.getByteFrequencyData(dataArray);
      drawVisualizerWave(dataArray);
      requestAnimationFrame(renderLiveAudio);
    } else {
      resetToStandby();
    }
  }

  audioPlayer.onplay = () => {
    cancelAnimationFrame(visualizerAnimationId);
    renderLiveAudio();
  };

  audioPlayer.onended = () => {
    resetToStandby();
    animateIdleVisualizer();
  };
}

// Send Text Query to Backend
async function sendCommand(queryText) {
  if (!queryText || !queryText.trim()) return;

  isProcessing = true;
  appendMessage("user", queryText);
  setAssistantState("thinking");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: queryText, enable_tts: true })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Server error (${response.status}): ${errText}`);
    }

    const data = await response.json();
    setAssistantState("speaking");
    appendMessage("assistant", data.response, data.tool_called);

    if (data.audio_url) {
      playAudioResponse(data.audio_url);
    } else {
      setTimeout(resetToStandby, 2000);
    }
  } catch (err) {
    appendMessage("assistant", `Alert: ${err.message}`);
    resetToStandby();
  }
}

// =======================================================
// 6. TELEMETRY & WEBSOCKET BRIDGE
// =======================================================
async function updateTelemetry() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    if (data.system) {
      if (hudBattery) hudBattery.textContent = `⚡ ${data.system.battery}`;
      if (hudCpu) hudCpu.textContent = `💻 CPU ${data.system.cpu_usage}`;
      if (hudClock) hudClock.textContent = (data.system.current_time || "").split(",")[0] || "ONLINE";
    }
  } catch (e) {
    const now = new Date();
    if (hudClock) hudClock.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  try {
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "native_event" && msg.data) {
          appendMessage("user", msg.data.user);
          appendMessage("assistant", msg.data.assistant, msg.data.tool_called);
          setAssistantState("speaking");
          setTimeout(resetToStandby, 2500);
        }
      } catch (e) {}
    };
    ws.onclose = () => setTimeout(connectWebSocket, 2000);
  } catch (e) {}
}

// Screen Vision Trigger
async function triggerScreenVision() {
  appendMessage("user", "👁️ [Screen Scan] Paru, scan my screen...");
  setAssistantState("thinking", "SCANNING SCREEN...");

  try {
    const res = await fetch("/api/vision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "Describe what is on my screen and highlight anything relevant or any errors." })
    });
    const data = await res.json();
    setAssistantState("speaking");
    appendMessage("assistant", data.response);

    if (data.audio_url) {
      playAudioResponse(data.audio_url);
    } else {
      setTimeout(resetToStandby, 2000);
    }
  } catch (err) {
    appendMessage("assistant", `Vision Error: ${err.message}`);
    resetToStandby();
  }
}

// =======================================================
// 8. CONTINUOUS LISTENING (HANDS-FREE VAD)
// =======================================================
let continuousListening = false;
let continuousStream = null;
let continuousAnalyser = null;
let vadCheckInterval = null;
let speechDetectedFrames = 0;
let silentFrames = 0;
const SPEECH_THRESHOLD = 30;  // Audio level threshold to detect speech
const SPEECH_FRAMES_NEEDED = 8;  // Consecutive frames needed to confirm speech
const SILENCE_FRAMES_NEEDED = 25; // Consecutive silent frames to end recording

function startContinuousListening() {
  if (continuousListening) return;
  
  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    continuousListening = true;
    continuousStream = stream;
    
    const actx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const source = actx.createMediaStreamSource(stream);
    continuousAnalyser = actx.createAnalyser();
    continuousAnalyser.fftSize = 512;
    source.connect(continuousAnalyser);
    
    const freqData = new Uint8Array(continuousAnalyser.frequencyBinCount);
    speechDetectedFrames = 0;
    silentFrames = 0;
    
    vadCheckInterval = setInterval(() => {
      if (isRecordingAudio || isProcessing || isSpeaking) return;
      
      continuousAnalyser.getByteFrequencyData(freqData);
      const avg = freqData.reduce((a, b) => a + b, 0) / freqData.length;
      
      if (avg > SPEECH_THRESHOLD) {
        speechDetectedFrames++;
        silentFrames = 0;
        if (speechDetectedFrames >= SPEECH_FRAMES_NEEDED && !isRecordingAudio) {
          speechDetectedFrames = 0;
          startVoiceRecording();
        }
      } else {
        silentFrames++;
        if (silentFrames > 3) speechDetectedFrames = 0;
      }
    }, 80);
    
    const label = document.getElementById("continuousLabel");
    if (label) label.textContent = "Hands-Free: ON";
    appendMessage("assistant", "Hands-free listening activated! I'm always listening — just speak naturally.");
    
  }).catch(err => {
    console.error("Continuous listen error:", err);
    appendMessage("assistant", "Mic access error. Please allow microphone access and try again.");
    const toggle = document.getElementById("continuousListenToggle");
    if (toggle) toggle.checked = false;
  });
}

function stopContinuousListening() {
  continuousListening = false;
  if (vadCheckInterval) clearInterval(vadCheckInterval);
  vadCheckInterval = null;
  if (continuousStream) {
    continuousStream.getTracks().forEach(t => t.stop());
    continuousStream = null;
  }
  const label = document.getElementById("continuousLabel");
  if (label) label.textContent = "Hands-Free: OFF";
}

// =======================================================
// 9. INITIALIZE ON DOM LOAD
// =======================================================
document.addEventListener("DOMContentLoaded", () => {
  initVisualizer();
  animateIdleVisualizer();
  initThreeOrb();
  connectWebSocket();
  updateTelemetry();
  setInterval(updateTelemetry, 4000);

  // Continuous Listening Toggle
  const continuousToggle = document.getElementById("continuousListenToggle");
  if (continuousToggle) {
    continuousToggle.addEventListener("change", () => {
      if (continuousToggle.checked) {
        startContinuousListening();
      } else {
        stopContinuousListening();
      }
    });
  }

  // Phone Remote Modal
  const btnRemoteLink = document.getElementById("btnRemoteLink");
  const remoteModal = document.getElementById("remoteModal");
  const btnCloseRemote = document.getElementById("btnCloseRemote");
  const remoteUrlDisplay = document.getElementById("remoteUrlDisplay");

  if (btnRemoteLink && remoteModal) {
    btnRemoteLink.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/status");
        const data = await res.json();
        const url = data.remote_url || `http://${window.location.hostname}:8765/remote`;
        remoteUrlDisplay.textContent = url;
      } catch (e) {
        remoteUrlDisplay.textContent = `http://${window.location.hostname}:8765/remote`;
      }
      remoteModal.classList.add("open");
    });
    if (btnCloseRemote) {
      btnCloseRemote.addEventListener("click", () => {
        remoteModal.classList.remove("open");
      });
    }
  }

  // Mic Button & Orb Click
  if (btnMic) btnMic.addEventListener("click", manualMicTrigger);
  if (orbWrapper) orbWrapper.addEventListener("click", manualMicTrigger);

  // Spacebar Hotkey
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target.tagName !== "INPUT") {
      e.preventDefault();
      manualMicTrigger();
    }
  });

  // Chat Form Submit
  if (chatForm) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const query = chatInput.value.trim();
      if (query) {
        sendCommand(query);
        chatInput.value = "";
      }
    });
  }

  // Quick Action Chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const cmd = chip.getAttribute("data-cmd");
      sendCommand(cmd);
    });
  });

  // Clear Feed
  if (btnClearFeed) {
    btnClearFeed.addEventListener("click", () => {
      feedMessages.innerHTML = "";
    });
  }

  // Screen Vision Button
  if (btnVision) btnVision.addEventListener("click", triggerScreenVision);

  // Settings Modal Handlers
  if (btnSettings) {
    btnSettings.addEventListener("click", () => {
      settingsModal.classList.add("open");
    });
  }
  if (btnCloseSettings) {
    btnCloseSettings.addEventListener("click", () => {
      settingsModal.classList.remove("open");
    });
  }
  if (btnCancelSettings) {
    btnCancelSettings.addEventListener("click", () => {
      settingsModal.classList.remove("open");
    });
  }

  if (btnSaveSettings) {
    btnSaveSettings.addEventListener("click", async () => {
      const apiKey = inputApiKey.value.trim();
      const voice = selectVoice.value;
      const userName = inputUserName.value.trim();
      const telegramToken = document.getElementById("inputTelegramToken") ? document.getElementById("inputTelegramToken").value.trim() : "";

      try {
        await fetch("/api/settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            gemini_api_key: apiKey,
            voice: voice,
            user_name: userName,
            telegram_bot_token: telegramToken
          })
        });
        appendMessage("assistant", "Configuration locked and secured. Settings applied!");
        settingsModal.classList.remove("open");
      } catch (e) {
        alert("Error saving settings: " + e.message);
      }
    });
  }
});

