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
  const voiceStatus = document.getElementById("voice-status");
  const chatLog = document.getElementById("chat-log");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");

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

  function startSending() {
    if (sendTimer) return;
    sendTimer = setInterval(() => {
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
    handleJoystickMove(e.clientX, e.clientY);
  });
  window.addEventListener("mousemove", (e) => {
    if (dragging) handleJoystickMove(e.clientX, e.clientY);
  });
  window.addEventListener("mouseup", () => {
    if (dragging) {
      dragging = false;
      currentJoy = { x: 0, y: 0 };
      drawJoystick(0, 0);
    }
  });

  // Touch events
  canvas.addEventListener("touchstart", (e) => {
    e.preventDefault();
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
    currentJoy = { x: 0, y: 0 };
    drawJoystick(0, 0);
  });

  // Stop button
  stopBtn.addEventListener("click", sendStop);
  stopBtn.addEventListener("touchstart", (e) => {
    e.preventDefault();
    sendStop();
  });

  // Talk button
  talkBtn.addEventListener("click", sendTalk);

  // Chat form
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (text) {
      sendText(text);
      chatInput.value = "";
    }
  });

  // Camera feed error handling
  const cameraFeed = document.getElementById("camera-feed");
  const cameraOverlay = document.getElementById("camera-overlay");
  if (cameraFeed) {
    cameraFeed.addEventListener("error", () => {
      cameraOverlay.classList.remove("hidden");
    });
  }

  // Simulator controls
  simResetBtn.addEventListener("click", () => {
    resetRobot();
    addEventEntry("simulator", "Position reset");
  });

  // -- Init --
  drawJoystick(0, 0);
  updateGauges(0, 0);
  requestAnimationFrame(animate);
  connect();
})();
