// Emiglio robot web control interface with virtual robot simulator

(function () {
  "use strict";

  const WS_URL = `ws://${location.host}/ws`;
  const SEND_INTERVAL_MS = 100;

  let ws = null;
  let sendTimer = null;
  let currentJoy = { x: 0, y: 0 };

  // -- DOM refs --
  const statusEl = document.getElementById("status");
  const readoutEl = document.getElementById("motor-readout");
  const canvas = document.getElementById("joystick");
  const ctx = canvas.getContext("2d");
  const stopBtn = document.getElementById("stop-btn");
  const talkBtn = document.getElementById("talk-btn");
  const testSpeakerBtn = document.getElementById("test-speaker-btn");
  const testMicBtn = document.getElementById("test-mic-btn");
  const voiceStatus = document.getElementById("voice-status");
  const chatLog = document.getElementById("chat-log");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");

  // Voice Lab DOM refs
  const vlSelect = document.getElementById("voicelab-select");
  const vlRefreshBtn = document.getElementById("voicelab-refresh");
  const vlName = document.getElementById("voicelab-name");
  const vlLabels = document.getElementById("voicelab-labels");
  const vlDesc = document.getElementById("voicelab-desc");
  const vlText = document.getElementById("voicelab-text");
  const vlPreviewBtn = document.getElementById("voicelab-preview-btn");
  const vlActivateBtn = document.getElementById("voicelab-activate-btn");
  const vlCustomId = document.getElementById("voicelab-custom-id");
  const vlStatus = document.getElementById("voicelab-status");
  const vlAudio = document.getElementById("voicelab-audio");

  // Voice Lab state
  let vlVoices = [];
  let vlActiveVoiceId = "";

  // Simulator DOM refs
  const simCanvas = document.getElementById("sim-canvas");
  const simCtx = simCanvas.getContext("2d");
  const simResetBtn = document.getElementById("sim-reset");
  const simTrailChk = document.getElementById("sim-trail");
  const gaugeFillLeft = document.getElementById("gauge-left");
  const gaugeFillRight = document.getElementById("gauge-right");
  const gaugeValLeft = document.getElementById("gauge-left-val");
  const gaugeValRight = document.getElementById("gauge-right-val");
  const eventListEl = document.getElementById("event-list");

  const CENTER = canvas.width / 2;
  const RADIUS = CENTER - 10;
  const KNOB_RADIUS = 25;

  // ========== Simulator ==========

  const SIM_SIZE = 500;
  const ROBOT_RADIUS = 14;
  const MAX_SPEED = 130; // px/s at motor=1.0
  const TURN_RATE = 3.5; // rad/s at full differential
  const WHEELBASE = 0.5;
  const TRAIL_MAX = 2000;
  const EVENT_LOG_MAX = 50;

  // Robot state
  const robot = {
    x: SIM_SIZE / 2,
    y: SIM_SIZE / 2,
    heading: -Math.PI / 2, // facing up
    motorLeft: 0,
    motorRight: 0,
    trail: [],
  };

  function resetRobot() {
    robot.x = SIM_SIZE / 2;
    robot.y = SIM_SIZE / 2;
    robot.heading = -Math.PI / 2;
    robot.motorLeft = 0;
    robot.motorRight = 0;
    robot.trail = [];
  }

  function updateRobot(dt) {
    const ml = robot.motorLeft;
    const mr = robot.motorRight;
    const v = ((ml + mr) / 2) * MAX_SPEED;
    const omega = ((ml - mr) / WHEELBASE) * TURN_RATE;

    robot.heading += omega * dt;
    robot.x += v * Math.cos(robot.heading) * dt;
    robot.y += v * Math.sin(robot.heading) * dt;

    // Clamp to arena
    const margin = ROBOT_RADIUS + 3;
    robot.x = Math.max(margin, Math.min(SIM_SIZE - margin, robot.x));
    robot.y = Math.max(margin, Math.min(SIM_SIZE - margin, robot.y));

    // Record trail when moving
    if (Math.abs(v) > 0.5 || Math.abs(omega) > 0.01) {
      robot.trail.push({ x: robot.x, y: robot.y });
      if (robot.trail.length > TRAIL_MAX) {
        robot.trail.splice(0, robot.trail.length - TRAIL_MAX);
      }
    }
  }

  function renderSimulator() {
    const c = simCtx;
    const S = SIM_SIZE;

    // Background
    c.fillStyle = "#0a0a1a";
    c.fillRect(0, 0, S, S);

    // Grid
    c.strokeStyle = "#152040";
    c.lineWidth = 1;
    for (let i = 50; i < S; i += 50) {
      c.beginPath();
      c.moveTo(i, 0);
      c.lineTo(i, S);
      c.stroke();
      c.beginPath();
      c.moveTo(0, i);
      c.lineTo(S, i);
      c.stroke();
    }

    // Border
    c.strokeStyle = "#0f3460";
    c.lineWidth = 2;
    c.strokeRect(1, 1, S - 2, S - 2);

    // Trail
    if (simTrailChk.checked && robot.trail.length > 1) {
      // Draw fading trail: split into segments for gradual alpha
      const len = robot.trail.length;
      const step = Math.max(1, Math.floor(len / 200)); // limit draw calls
      c.lineWidth = 2;
      c.lineCap = "round";
      for (let i = step; i < len; i += step) {
        const alpha = (i / len) * 0.5;
        c.strokeStyle = `rgba(0,212,255,${alpha})`;
        c.beginPath();
        c.moveTo(robot.trail[i - step].x, robot.trail[i - step].y);
        c.lineTo(robot.trail[i].x, robot.trail[i].y);
        c.stroke();
      }
    }

    // Goal marker (pulsing orange circle)
    if (goalMarker) {
      const pulse = 0.7 + 0.3 * Math.sin(Date.now() / 200);
      c.beginPath();
      c.arc(goalMarker.x, goalMarker.y, 30, 0, Math.PI * 2);
      c.strokeStyle = `rgba(255, 152, 0, ${pulse * 0.6})`;
      c.lineWidth = 2;
      c.stroke();
      c.beginPath();
      c.arc(goalMarker.x, goalMarker.y, 8, 0, Math.PI * 2);
      c.fillStyle = `rgba(255, 152, 0, ${pulse})`;
      c.fill();
    }

    // Robot
    drawRobot(c);
  }

  function drawRobot(c) {
    const R = ROBOT_RADIUS;

    c.save();
    c.translate(robot.x, robot.y);
    c.rotate(robot.heading);

    // Body shadow
    c.beginPath();
    c.arc(1, 1, R, 0, Math.PI * 2);
    c.fillStyle = "rgba(0,0,0,0.3)";
    c.fill();

    // Body
    c.beginPath();
    c.arc(0, 0, R, 0, Math.PI * 2);
    c.fillStyle = "#00d4ff";
    c.fill();
    c.strokeStyle = "#008faa";
    c.lineWidth = 2;
    c.stroke();

    // "E" label
    c.fillStyle = "#1a1a2e";
    c.font = "bold 12px system-ui";
    c.textAlign = "center";
    c.textBaseline = "middle";
    c.fillText("E", 0, 0);

    // Direction arrow (pointing right in robot frame = forward)
    c.beginPath();
    c.moveTo(R + 5, 0);
    c.lineTo(R - 3, -5);
    c.lineTo(R - 3, 5);
    c.closePath();
    c.fillStyle = "#fff";
    c.fill();

    // Wheels
    const ww = 10; // width
    const wh = 5; // height
    const wo = R + 3; // offset from center

    // Left wheel (top in robot local frame)
    c.fillStyle = wheelColor(robot.motorLeft);
    c.fillRect(-ww / 2, -wo - wh / 2, ww, wh);
    c.strokeStyle = "#333";
    c.lineWidth = 1;
    c.strokeRect(-ww / 2, -wo - wh / 2, ww, wh);

    // Right wheel (bottom in robot local frame)
    c.fillStyle = wheelColor(robot.motorRight);
    c.fillRect(-ww / 2, wo - wh / 2, ww, wh);
    c.strokeStyle = "#333";
    c.strokeRect(-ww / 2, wo - wh / 2, ww, wh);

    c.restore();
  }

  function wheelColor(power) {
    if (power > 0.05) return "#00c853";
    if (power < -0.05) return "#ff5252";
    return "#555";
  }

  // -- Motor gauges --
  function updateGauges(left, right) {
    setGauge(gaugeFillLeft, gaugeValLeft, left);
    setGauge(gaugeFillRight, gaugeValRight, right);
  }

  function setGauge(fillEl, valEl, value) {
    const pct = Math.abs(value) * 50; // 0-50% of track width
    if (value >= 0) {
      fillEl.style.left = "50%";
      fillEl.style.width = pct + "%";
      fillEl.className = "gauge-fill forward";
    } else {
      fillEl.style.left = 50 - pct + "%";
      fillEl.style.width = pct + "%";
      fillEl.className = "gauge-fill backward";
    }
    valEl.textContent = value.toFixed(2);
  }

  // -- Subsystem status --
  function updateSubsystems(data) {
    setDot("sub-motors", data.motors);
    setDot("sub-camera", data.camera);
    setDot("sub-audio", data.audio);
    setDot("sub-brain", data.brain);
  }

  function setDot(id, active) {
    const el = document.getElementById(id);
    if (el) el.className = "dot " + (active ? "on" : "off");
  }

  // -- Event log --
  function addEventEntry(event, detail) {
    const now = new Date();
    const ts =
      String(now.getHours()).padStart(2, "0") +
      ":" +
      String(now.getMinutes()).padStart(2, "0") +
      ":" +
      String(now.getSeconds()).padStart(2, "0");

    const div = document.createElement("div");
    div.className = "event-entry";
    div.innerHTML =
      `<span class="event-time">${ts}</span>` +
      `<span class="event-name">${escapeHtml(event)}</span>` +
      `<span class="event-detail">${escapeHtml(detail)}</span>`;

    eventListEl.appendChild(div);

    // Trim old entries
    while (eventListEl.children.length > EVENT_LOG_MAX) {
      eventListEl.removeChild(eventListEl.firstChild);
    }

    eventListEl.scrollTop = eventListEl.scrollHeight;
  }

  // -- Animation loop --
  let lastTime = null;

  function animate(timestamp) {
    if (lastTime === null) lastTime = timestamp;
    const dt = Math.min((timestamp - lastTime) / 1000, 0.1);
    lastTime = timestamp;

    updateRobot(dt);
    renderSimulator();

    requestAnimationFrame(animate);
  }

  // ========== WebSocket ==========

  function connect() {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      statusEl.textContent = "Connected";
      statusEl.className = "status connected";
      startSending();
      addEventEntry("system", "Connected to server");
      requestModelList();
    };
    ws.onclose = () => {
      statusEl.textContent = "Disconnected";
      statusEl.className = "status disconnected";
      stopSending();
      addEventEntry("system", "Disconnected");
      setTimeout(connect, 2000);
    };
    ws.onerror = () => ws.close();
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleServerMessage(data);
      } catch (e) {
        // ignore non-JSON
      }
    };
  }

  function handleServerMessage(data) {
    if (data.type === "status") {
      voiceStatus.textContent = data.message || "";
      if (data.message === "Ready" || data.message === "Error occurred") {
        talkBtn.disabled = false;
        talkBtn.classList.remove("listening");
      }
    } else if (data.type === "conversation_result") {
      if (data.transcript) {
        addChatMessage("You", data.transcript, "user");
      }
      if (data.reply) {
        addChatMessage("Emiglio", data.reply, "bot");
      }
      if (data.audio_base64) {
        const raw = atob(data.audio_base64);
        const bytes = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
        const blob = new Blob([bytes], { type: "audio/wav" });
        const url = URL.createObjectURL(blob);
        vlAudio.src = url;
        vlAudio.play();
        vlAudio.onended = () => URL.revokeObjectURL(url);
      }
      if (data.error && !data.transcript) {
        addChatMessage("System", data.error, "bot");
      }
      talkBtn.disabled = false;
      talkBtn.classList.remove("listening");
    } else if (data.type === "motor_state") {
      robot.motorLeft = data.left;
      robot.motorRight = data.right;
      updateGauges(data.left, data.right);
      updateReadout(data.left, data.right);
    } else if (data.type === "subsystem_status") {
      updateSubsystems(data);
    } else if (data.type === "event") {
      addEventEntry(data.event, data.detail || "");
    } else if (data.type === "training_status") {
      onTrainingStatus(data.running);
    } else if (data.type === "training_stats") {
      onTrainingStats(data);
    } else if (data.type === "training_episode") {
      onTrainingStats(data);
      startReplay(data.trajectory, data.goal);
    } else if (data.type === "model_list") {
      onModelList(data.models);
    } else if (data.type === "model_saved") {
      addEventEntry("training", "Model saved: " + data.name);
      requestModelList();
    }
  }

  function addChatMessage(label, text, cls) {
    const div = document.createElement("div");
    div.className = `chat-msg ${cls}`;
    div.innerHTML = `<span class="label">${label}:</span> ${escapeHtml(text)}`;
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  let joystickActive = false; // true while user is dragging the joystick

  function startSending() {
    if (sendTimer) return;
    sendTimer = setInterval(() => {
      if (!joystickActive) return; // don't flood (0,0) when idle
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(
          JSON.stringify({
            type: "joystick",
            x: currentJoy.x,
            y: currentJoy.y,
          })
        );
      }
    }, SEND_INTERVAL_MS);
  }

  function stopSending() {
    clearInterval(sendTimer);
    sendTimer = null;
  }

  function sendStop() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "stop" }));
    }
    currentJoy = { x: 0, y: 0 };
    drawJoystick(0, 0);
  }

  // -- Talk button --
  function sendTalk() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "talk" }));
      talkBtn.disabled = true;
      talkBtn.classList.add("listening");
      voiceStatus.textContent = "Connecting...";
    }
  }

  // -- Chat input --
  function sendText(text) {
    if (ws && ws.readyState === WebSocket.OPEN && text) {
      ws.send(JSON.stringify({ type: "text", text: text }));
      addChatMessage("You", text, "user");
    }
  }

  // ========== Joystick ==========

  function drawJoystick(knobX, knobY) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Base circle
    ctx.beginPath();
    ctx.arc(CENTER, CENTER, RADIUS, 0, Math.PI * 2);
    ctx.strokeStyle = "#0f3460";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Crosshairs
    ctx.beginPath();
    ctx.moveTo(CENTER, CENTER - RADIUS);
    ctx.lineTo(CENTER, CENTER + RADIUS);
    ctx.moveTo(CENTER - RADIUS, CENTER);
    ctx.lineTo(CENTER + RADIUS, CENTER);
    ctx.strokeStyle = "#1a2a4a";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Knob
    const px = CENTER + knobX * RADIUS;
    const py = CENTER - knobY * RADIUS;
    ctx.beginPath();
    ctx.arc(px, py, KNOB_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = "#00d4ff";
    ctx.fill();
  }

  function updateReadout(left, right) {
    readoutEl.textContent = `L: ${left.toFixed(2)} | R: ${right.toFixed(2)}`;
  }

  function getJoystickPos(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    let x = ((clientX - rect.left) / rect.width) * 2 - 1;
    let y = -(((clientY - rect.top) / rect.height) * 2 - 1);

    const dist = Math.sqrt(x * x + y * y);
    if (dist > 1) {
      x /= dist;
      y /= dist;
    }
    return { x, y };
  }

  function handleJoystickMove(clientX, clientY) {
    const joy = getJoystickPos(clientX, clientY);
    currentJoy = joy;
    drawJoystick(joy.x, joy.y);
  }

  // Mouse events
  let dragging = false;
  canvas.addEventListener("mousedown", (e) => {
    dragging = true;
    joystickActive = true;
    handleJoystickMove(e.clientX, e.clientY);
  });
  window.addEventListener("mousemove", (e) => {
    if (dragging) handleJoystickMove(e.clientX, e.clientY);
  });
  window.addEventListener("mouseup", () => {
    if (dragging) {
      dragging = false;
      joystickActive = false;
      currentJoy = { x: 0, y: 0 };
      drawJoystick(0, 0);
      // Send one explicit stop so robot halts
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "joystick", x: 0, y: 0 }));
      }
    }
  });

  // Touch events
  canvas.addEventListener("touchstart", (e) => {
    e.preventDefault();
    joystickActive = true;
    const t = e.touches[0];
    handleJoystickMove(t.clientX, t.clientY);
  });
  canvas.addEventListener("touchmove", (e) => {
    e.preventDefault();
    const t = e.touches[0];
    handleJoystickMove(t.clientX, t.clientY);
  });
  canvas.addEventListener("touchend", (e) => {
    e.preventDefault();
    joystickActive = false;
    currentJoy = { x: 0, y: 0 };
    drawJoystick(0, 0);
    // Send one explicit stop so robot halts
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "joystick", x: 0, y: 0 }));
    }
  });

  // Stop button
  stopBtn.addEventListener("click", sendStop);
  stopBtn.addEventListener("touchstart", (e) => {
    e.preventDefault();
    sendStop();
  });

  // Talk button
  talkBtn.addEventListener("click", sendTalk);

  // Test speaker button
  testSpeakerBtn.addEventListener("click", async () => {
    testSpeakerBtn.disabled = true;
    voiceStatus.textContent = "Playing test tone...";
    try {
      const resp = await fetch("/audio/test", { method: "POST" });
      const data = await resp.json();
      voiceStatus.textContent = data.ok ? data.message : `Speaker test failed: ${data.error}`;
      addEventEntry("audio", data.ok ? "Speaker test OK" : `Speaker test failed: ${data.error}`);
    } catch (e) {
      voiceStatus.textContent = `Speaker test error: ${e.message}`;
      addEventEntry("audio", `Speaker test error: ${e.message}`);
    } finally {
      testSpeakerBtn.disabled = false;
    }
  });

  // Test mic button
  testMicBtn.addEventListener("click", async () => {
    testMicBtn.disabled = true;
    voiceStatus.textContent = "Recording 3s...";
    try {
      const resp = await fetch("/mic/test", { method: "POST" });
      const data = await resp.json();
      if (data.ok) {
        const msg = `Mic: RMS=${data.rms}, peak=${data.peak}` +
          (data.played_back ? " (played back)" : " (no playback)") +
          ` — ${data.message}`;
        voiceStatus.textContent = msg;
        addEventEntry("audio", msg);
      } else {
        voiceStatus.textContent = `Mic test failed: ${data.error}`;
        addEventEntry("audio", `Mic test failed: ${data.error}`);
      }
    } catch (e) {
      voiceStatus.textContent = `Mic test error: ${e.message}`;
      addEventEntry("audio", `Mic test error: ${e.message}`);
    } finally {
      testMicBtn.disabled = false;
    }
  });

  // Chat form
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (text) {
      sendText(text);
      chatInput.value = "";
    }
  });

  // Camera feed and device selection
  const cameraFeed = document.getElementById("camera-feed");
  const cameraOverlay = document.getElementById("camera-overlay");
  const cameraSelect = document.getElementById("camera-select");

  if (cameraFeed) {
    cameraFeed.addEventListener("error", () => {
      cameraOverlay.classList.remove("hidden");
    });
  }

  async function loadCameraDevices() {
    try {
      const resp = await fetch("/camera/devices");
      const data = await resp.json();
      cameraSelect.innerHTML = "";
      if (data.devices && data.devices.length > 0) {
        data.devices.forEach((dev) => {
          const opt = document.createElement("option");
          opt.value = dev.index;
          opt.textContent = `${dev.name} (/dev/video${dev.index})`;
          if (dev.index === data.active_index) opt.selected = true;
          cameraSelect.appendChild(opt);
        });
      } else {
        const opt = document.createElement("option");
        opt.textContent = "No cameras found";
        opt.disabled = true;
        cameraSelect.appendChild(opt);
      }
    } catch {
      cameraSelect.innerHTML = "<option disabled>Error loading devices</option>";
    }
  }

  cameraSelect.addEventListener("change", async () => {
    const index = parseInt(cameraSelect.value, 10);
    if (isNaN(index)) return;
    cameraSelect.disabled = true;
    try {
      const resp = await fetch("/camera/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index }),
      });
      const data = await resp.json();
      if (data.ok) {
        // Reset the MJPEG stream by re-assigning src
        cameraFeed.src = "";
        cameraFeed.src = "/stream";
        cameraOverlay.classList.add("hidden");
        addEventEntry("camera", `Switched to /dev/video${index}`);
      } else {
        addEventEntry("camera", `Switch failed: ${data.error}`);
      }
    } catch (e) {
      addEventEntry("camera", `Switch error: ${e.message}`);
    } finally {
      cameraSelect.disabled = false;
    }
  });

  loadCameraDevices();
  loadVoices();

  // ========== RL Training ==========

  const trainingToggleBtn = document.getElementById("training-toggle-btn");
  const trainingEnvTypeSel = document.getElementById("training-env-type");
  const trainingSpeedSel = document.getElementById("training-speed");
  const tsEpisode = document.getElementById("ts-episode");
  const tsReward = document.getElementById("ts-reward");
  const tsGoals = document.getElementById("ts-goals");
  const tsDist = document.getElementById("ts-dist");
  const rewardCanvas = document.getElementById("reward-chart");
  const rewardCtx = rewardCanvas.getContext("2d");

  // Randomization controls
  const randEnabledChk = document.getElementById("rand-enabled");
  const randSliderRow = document.getElementById("rand-slider-row");
  const randStrengthInput = document.getElementById("rand-strength");
  const randStrengthVal = document.getElementById("rand-strength-val");

  // Model management
  const modelSelect = document.getElementById("model-select");
  const modelRefreshBtn = document.getElementById("model-refresh-btn");
  const modelSaveBtn = document.getElementById("model-save-btn");
  const modelResumeBtn = document.getElementById("model-resume-btn");
  const modelInferenceBtn = document.getElementById("model-inference-btn");
  const modelMeta = document.getElementById("model-meta");

  let trainingRunning = false;
  let goalCount = 0;
  let rewardHistory = [];
  const REWARD_HISTORY_MAX = 100;

  // Goal marker for simulator overlay
  let goalMarker = null; // {x, y} or null

  // Replay state
  let replayTimer = null;
  let replayTrajectory = null;
  let replayIndex = 0;

  function getRandomizationStrength() {
    if (!randEnabledChk.checked) return 0.0;
    return parseInt(randStrengthInput.value, 10) / 100;
  }

  function toggleTraining() {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (trainingRunning) {
      ws.send(JSON.stringify({ type: "training_stop" }));
    } else {
      const interval = parseInt(trainingSpeedSel.value, 10);
      ws.send(JSON.stringify({
        type: "training_start",
        total_timesteps: 100000,
        demo_interval: interval,
        learning_rate: 0.0003,
        randomization_strength: getRandomizationStrength(),
        env_type: trainingEnvTypeSel.value,
      }));
    }
  }

  function onTrainingStatus(running) {
    trainingRunning = running;
    if (running) {
      trainingToggleBtn.textContent = "Stop Training";
      trainingToggleBtn.classList.add("running");
      modelSaveBtn.disabled = false;
      goalCount = 0;
      rewardHistory = [];
    } else {
      trainingToggleBtn.textContent = "Start Training";
      trainingToggleBtn.classList.remove("running");
      modelSaveBtn.disabled = true;
      stopReplay();
      requestModelList();
    }
  }

  function onTrainingStats(data) {
    tsEpisode.textContent = data.episode;
    tsReward.textContent = data.reward.toFixed(3);
    tsDist.textContent = data.dist_to_goal >= 0 ? data.dist_to_goal.toFixed(0) : "-";
    if (data.goal_reached) {
      goalCount++;
      tsGoals.textContent = goalCount;
    }
    rewardHistory.push(data.reward);
    if (rewardHistory.length > REWARD_HISTORY_MAX) {
      rewardHistory.shift();
    }
    drawRewardChart();
  }

  function startReplay(trajectory, goal) {
    stopReplay();
    if (!trajectory || trajectory.length === 0) return;
    goalMarker = { x: goal[0], y: goal[1] };
    replayTrajectory = trajectory;
    replayIndex = 0;
    robot.trail = [];

    // Pace to ~2s total regardless of trajectory length
    const interval = Math.max(5, Math.floor(2000 / trajectory.length));
    replayTimer = setInterval(() => {
      if (replayIndex >= replayTrajectory.length) {
        stopReplay();
        return;
      }
      const pt = replayTrajectory[replayIndex];
      robot.x = pt[0];
      robot.y = pt[1];
      robot.trail.push({ x: pt[0], y: pt[1] });
      replayIndex++;
    }, interval);
  }

  function stopReplay() {
    if (replayTimer) {
      clearInterval(replayTimer);
      replayTimer = null;
    }
    replayTrajectory = null;
  }

  function drawRewardChart() {
    const c = rewardCtx;
    const W = rewardCanvas.width;
    const H = rewardCanvas.height;
    c.clearRect(0, 0, W, H);
    c.fillStyle = "#16213e";
    c.fillRect(0, 0, W, H);

    if (rewardHistory.length < 2) return;

    const minR = Math.min(...rewardHistory);
    const maxR = Math.max(...rewardHistory);
    const range = maxR - minR || 1;
    const pad = 4;

    // Zero line
    if (minR < 0 && maxR > 0) {
      const zy = H - pad - ((0 - minR) / range) * (H - 2 * pad);
      c.strokeStyle = "#334";
      c.lineWidth = 1;
      c.beginPath();
      c.moveTo(0, zy);
      c.lineTo(W, zy);
      c.stroke();
    }

    // Reward curve
    c.strokeStyle = "#00d4ff";
    c.lineWidth = 1.5;
    c.beginPath();
    for (let i = 0; i < rewardHistory.length; i++) {
      const x = (i / (rewardHistory.length - 1)) * W;
      const y = H - pad - ((rewardHistory[i] - minR) / range) * (H - 2 * pad);
      if (i === 0) c.moveTo(x, y);
      else c.lineTo(x, y);
    }
    c.stroke();
  }

  trainingToggleBtn.addEventListener("click", toggleTraining);
  trainingSpeedSel.addEventListener("change", () => {
    if (ws && ws.readyState === WebSocket.OPEN && trainingRunning) {
      const interval = parseInt(trainingSpeedSel.value, 10);
      ws.send(JSON.stringify({ type: "training_config", demo_interval: interval }));
    }
  });

  // ========== Skills ==========

  const skillBtns = document.querySelectorAll(".skill-btn");
  const skillSpeedInput = document.getElementById("skill-speed");
  const skillSpeedVal = document.getElementById("skill-speed-val");
  const skillDurationInput = document.getElementById("skill-duration");
  const skillDurationVal = document.getElementById("skill-duration-val");

  function getSkillSpeed() {
    return parseInt(skillSpeedInput.value, 10) / 100;
  }

  function getSkillDuration() {
    return parseInt(skillDurationInput.value, 10) / 10;
  }

  skillSpeedInput.addEventListener("input", () => {
    skillSpeedVal.textContent = getSkillSpeed().toFixed(1);
  });

  skillDurationInput.addEventListener("input", () => {
    skillDurationVal.textContent = getSkillDuration().toFixed(1) + "s";
  });

  function sendSkill(name) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const speed = getSkillSpeed();
      const duration = getSkillDuration();
      ws.send(JSON.stringify({
        type: "skill",
        name: name,
        speed: speed,
        duration: duration,
      }));
      addEventEntry("skill", `${name} (speed=${speed.toFixed(1)}, duration=${duration.toFixed(1)}s)`);

      // Disable all skill buttons during execution, re-enable after duration + buffer
      skillBtns.forEach((btn) => {
        btn.disabled = true;
        if (btn.dataset.skill === name) btn.classList.add("executing");
      });
      setTimeout(() => {
        skillBtns.forEach((btn) => {
          btn.disabled = false;
          btn.classList.remove("executing");
        });
      }, (duration + 0.5) * 1000);
    }
  }

  skillBtns.forEach((btn) => {
    btn.addEventListener("click", () => sendSkill(btn.dataset.skill));
  });

  // Randomization controls
  randEnabledChk.addEventListener("change", () => {
    if (randEnabledChk.checked) {
      randSliderRow.classList.remove("hidden");
    } else {
      randSliderRow.classList.add("hidden");
    }
  });
  randStrengthInput.addEventListener("input", () => {
    randStrengthVal.textContent = (parseInt(randStrengthInput.value, 10) / 100).toFixed(2);
  });

  // Model management
  function requestModelList() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "model_list" }));
    }
  }

  function onModelList(models) {
    modelSelect.innerHTML = "";
    if (!models || models.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "No models";
      opt.disabled = true;
      modelSelect.appendChild(opt);
      modelResumeBtn.disabled = true;
      modelInferenceBtn.disabled = true;
      modelMeta.classList.add("hidden");
      return;
    }
    models.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.name;
      const date = new Date(m.timestamp * 1000);
      const dateStr = date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      opt.textContent = m.name + " (" + dateStr + ")";
      modelSelect.appendChild(opt);
    });
    modelResumeBtn.disabled = false;
    modelInferenceBtn.disabled = false;
    _lastModelList = models;
    updateModelMeta(models);
  }

  function updateModelMeta(models) {
    const name = modelSelect.value;
    const m = models ? models.find((x) => x.name === name) : null;
    if (!m) {
      modelMeta.classList.add("hidden");
      return;
    }
    const date = new Date(m.timestamp * 1000);
    const envLabel = m.env_type === "nav" ? "Nav" : "Legacy";
    modelMeta.innerHTML =
      envLabel + " | Steps: " + m.total_timesteps +
      " | Episodes: " + m.episodes +
      " | Reward: " + (m.mean_reward || 0).toFixed(2) +
      " | Goals: " + ((m.goal_rate || 0) * 100).toFixed(0) + "%" +
      (m.randomization_strength > 0 ? " | Rand: " + m.randomization_strength.toFixed(2) : "");
    modelMeta.classList.remove("hidden");
  }

  let _lastModelList = null;
  modelSelect.addEventListener("change", () => updateModelMeta(_lastModelList));

  modelRefreshBtn.addEventListener("click", requestModelList);

  modelSaveBtn.addEventListener("click", () => {
    const name = prompt("Model name:", "model_" + Date.now());
    if (!name) return;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "model_save", name: name }));
    }
  });

  modelResumeBtn.addEventListener("click", () => {
    const name = modelSelect.value;
    if (!name || trainingRunning) return;
    const interval = parseInt(trainingSpeedSel.value, 10);
    ws.send(JSON.stringify({
      type: "training_start",
      total_timesteps: 100000,
      demo_interval: interval,
      learning_rate: 0.0003,
      randomization_strength: getRandomizationStrength(),
      resume_from: name,
      env_type: trainingEnvTypeSel.value,
    }));
  });

  modelInferenceBtn.addEventListener("click", () => {
    const name = modelSelect.value;
    if (!name || trainingRunning) return;
    ws.send(JSON.stringify({
      type: "model_inference",
      name: name,
      episodes: 5,
    }));
  });

  // Simulator controls
  simResetBtn.addEventListener("click", () => {
    resetRobot();
    addEventEntry("simulator", "Position reset");
  });

  // ========== Voice Lab ==========

  function getEffectiveVoiceId() {
    const custom = vlCustomId.value.trim();
    return custom || vlSelect.value;
  }

  async function loadVoices() {
    vlStatus.textContent = "Loading voices...";
    try {
      const resp = await fetch("/voicelab/voices");
      const data = await resp.json();
      if (!data.ok) {
        vlStatus.textContent = data.error || "Failed to load voices";
        return;
      }
      vlVoices = data.voices || [];
      vlActiveVoiceId = data.active_voice_id || "";
      vlCustomId.value = "";

      vlSelect.innerHTML = "";
      if (vlVoices.length === 0) {
        const opt = document.createElement("option");
        opt.textContent = "No voices available";
        opt.disabled = true;
        vlSelect.appendChild(opt);
        vlStatus.textContent = "No voices found";
        return;
      }

      // Group by category
      const grouped = {};
      vlVoices.forEach((v) => {
        const cat = v.category || "other";
        if (!grouped[cat]) grouped[cat] = [];
        grouped[cat].push(v);
      });

      Object.keys(grouped).sort().forEach((cat) => {
        const group = document.createElement("optgroup");
        group.label = cat;
        grouped[cat].forEach((v) => {
          const opt = document.createElement("option");
          opt.value = v.voice_id;
          opt.textContent = v.name + (v.voice_id === vlActiveVoiceId ? " (active)" : "");
          if (v.voice_id === vlActiveVoiceId) opt.selected = true;
          group.appendChild(opt);
        });
        vlSelect.appendChild(group);
      });

      updateVoiceMeta();
      vlStatus.textContent = `${vlVoices.length} voices loaded`;
    } catch (e) {
      vlStatus.textContent = "Error loading voices: " + e.message;
    }
  }

  function updateVoiceMeta() {
    vlCustomId.value = "";
    const id = vlSelect.value;
    const voice = vlVoices.find((v) => v.voice_id === id);
    if (!voice) {
      vlName.textContent = "";
      vlLabels.innerHTML = "";
      vlDesc.textContent = "";
      vlActivateBtn.classList.remove("active-voice");
      return;
    }
    vlName.textContent = voice.name;
    vlLabels.innerHTML = "";
    if (voice.labels && typeof voice.labels === "object") {
      Object.entries(voice.labels).forEach(([key, val]) => {
        const tag = document.createElement("span");
        tag.className = "voicelab-label-tag";
        tag.textContent = val || key;
        vlLabels.appendChild(tag);
      });
    }
    vlDesc.textContent = voice.description || "";
    if (id === vlActiveVoiceId) {
      vlActivateBtn.classList.add("active-voice");
    } else {
      vlActivateBtn.classList.remove("active-voice");
    }
  }

  async function previewVoice() {
    const voiceId = getEffectiveVoiceId();
    const text = vlText.value.trim();
    if (!voiceId || !text) {
      vlStatus.textContent = "Select a voice and enter sample text";
      return;
    }
    vlPreviewBtn.disabled = true;
    vlStatus.textContent = "Synthesizing...";
    try {
      const resp = await fetch("/voicelab/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text, voice_id: voiceId }),
      });
      if (!resp.ok || resp.headers.get("content-type")?.includes("application/json")) {
        const err = await resp.json();
        vlStatus.textContent = err.error || "Preview failed";
        return;
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      vlAudio.src = url;
      vlAudio.play();
      vlStatus.textContent = "Playing preview...";
      vlAudio.onended = () => {
        vlStatus.textContent = "Preview complete";
        URL.revokeObjectURL(url);
      };
    } catch (e) {
      vlStatus.textContent = "Preview error: " + e.message;
    } finally {
      vlPreviewBtn.disabled = false;
    }
  }

  async function activateVoice() {
    const voiceId = getEffectiveVoiceId();
    if (!voiceId) return;
    vlActivateBtn.disabled = true;
    vlStatus.textContent = "Activating...";
    try {
      const resp = await fetch("/voicelab/activate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_id: voiceId }),
      });
      const data = await resp.json();
      if (data.ok) {
        vlActiveVoiceId = data.active_voice_id;
        // Update dropdown labels to reflect active state
        Array.from(vlSelect.options).forEach((opt) => {
          opt.textContent = opt.textContent.replace(" (active)", "");
          if (opt.value === vlActiveVoiceId) {
            opt.textContent += " (active)";
          }
        });
        vlActivateBtn.classList.add("active-voice");
        vlStatus.textContent = "Voice activated!";
        addEventEntry("voicelab", "Voice set to " + (vlVoices.find((v) => v.voice_id === voiceId)?.name || voiceId));
      } else {
        vlStatus.textContent = data.error || "Activation failed";
      }
    } catch (e) {
      vlStatus.textContent = "Activation error: " + e.message;
    } finally {
      vlActivateBtn.disabled = false;
    }
  }

  vlSelect.addEventListener("change", updateVoiceMeta);
  vlRefreshBtn.addEventListener("click", loadVoices);
  vlPreviewBtn.addEventListener("click", previewVoice);
  vlActivateBtn.addEventListener("click", activateVoice);

  // -- Init --
  drawJoystick(0, 0);
  updateGauges(0, 0);
  requestAnimationFrame(animate);
  connect();
})();
