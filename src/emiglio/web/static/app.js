// Emiglio robot web control interface

(function () {
  "use strict";

  const WS_URL = `ws://${location.host}/ws`;
  const SEND_INTERVAL_MS = 100;

  let ws = null;
  let sendTimer = null;
  let currentJoy = { x: 0, y: 0 };

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

  const CENTER = canvas.width / 2;
  const RADIUS = CENTER - 10;
  const KNOB_RADIUS = 25;

  // -- WebSocket --
  function connect() {
    ws = new WebSocket(WS_URL);
    ws.onopen = () => {
      statusEl.textContent = "Connected";
      statusEl.className = "status connected";
      startSending();
    };
    ws.onclose = () => {
      statusEl.textContent = "Disconnected";
      statusEl.className = "status disconnected";
      stopSending();
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
      // Re-enable talk button when ready
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
    updateReadout(0, 0);
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

  // -- Joystick rendering --
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
    const py = CENTER - knobY * RADIUS; // invert Y for screen coords
    ctx.beginPath();
    ctx.arc(px, py, KNOB_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = "#00d4ff";
    ctx.fill();
  }

  function updateReadout(left, right) {
    readoutEl.textContent = `L: ${left.toFixed(2)} | R: ${right.toFixed(2)}`;
  }

  // -- Joystick input --
  function getJoystickPos(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    let x = ((clientX - rect.left) / rect.width) * 2 - 1;
    let y = -(((clientY - rect.top) / rect.height) * 2 - 1); // invert Y

    // Clamp to unit circle
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

    // Arcade drive mixing (matches server-side logic)
    let left = joy.y + joy.x;
    let right = joy.y - joy.x;
    const maxVal = Math.max(Math.abs(left), Math.abs(right), 1);
    left /= maxVal;
    right /= maxVal;
    updateReadout(left, right);
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
      updateReadout(0, 0);
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
    updateReadout(0, 0);
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

  // -- Camera feed error handling --
  const cameraFeed = document.getElementById("camera-feed");
  const cameraOverlay = document.getElementById("camera-overlay");
  if (cameraFeed) {
    cameraFeed.addEventListener("error", () => {
      cameraOverlay.classList.remove("hidden");
    });
  }

  // -- Init --
  drawJoystick(0, 0);
  connect();
})();
