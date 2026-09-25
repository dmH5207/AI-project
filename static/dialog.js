(function () {
  var chatArea = document.getElementById("chatArea");
  var progressText = document.getElementById("progressText");
  var answerInput = document.getElementById("answerInput");
  var sendBtn = document.getElementById("sendBtn");
  var inputHint = document.getElementById("inputHint");

  var reportOverlay = document.getElementById("reportOverlay");
  var reportComment = document.getElementById("reportComment");
  var reportHighlights = document.getElementById("reportHighlights");
  var reportSuggestions = document.getElementById("reportSuggestions");
  var reportScoreTable = document.getElementById("reportScoreTable");
  var reportRadar = document.getElementById("reportRadar");
  var backToModesBtn = document.getElementById("backToModesBtn");
  var retryBtn = document.getElementById("retryBtn");

  var currentRound = 0;
  var totalRounds = 6;
  var isWaiting = false;

  // ---------- 消息渲染 ----------

  function addMessage(role, text) {
    var wrap = document.createElement("div");
    wrap.className = "msg " + role;

    var avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = role === "ai" ? "AI" : (window.currentLang === "en" ? "Me" : "我");

    var bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.textContent = text;

    wrap.appendChild(avatar);
    wrap.appendChild(bubble);
    chatArea.appendChild(wrap);
    scrollToBottom();
  }

  function addTyping() {
    var wrap = document.createElement("div");
    wrap.className = "msg ai typing";
    wrap.id = "typingMsg";
    wrap.innerHTML =
      '<div class="msg-avatar">AI</div>' +
      '<div class="msg-bubble">' +
        '<span class="dot"></span><span class="dot"></span><span class="dot"></span>' +
      '</div>';
    chatArea.appendChild(wrap);
    scrollToBottom();
  }

  function removeTyping() {
    var el = document.getElementById("typingMsg");
    if (el) el.remove();
  }

  function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  // ---------- 输入 ----------

  function updateSendBtn() {
    sendBtn.disabled = !answerInput.value.trim() || isWaiting;
  }

  answerInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
    updateSendBtn();
  });

  answerInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) send();
    }
  });

  sendBtn.addEventListener("click", send);

  // ---------- 发送 ----------

  function send() {
    var text = answerInput.value.trim();
    if (!text || isWaiting) return;

    addMessage("user", text);
    answerInput.value = "";
    answerInput.style.height = "auto";
    isWaiting = true;
    updateSendBtn();
    inputHint.textContent = t("aiThinking");
    setTimeout(function () { if (isWaiting) addTyping(); }, 200);

    fetch("/api/dialog/reply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer: text })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        isWaiting = false;
        removeTyping();
        inputHint.textContent = "";

        if (!data.success) {
          addMessage("ai", data.message || "出错了");
          updateSendBtn();
          return;
        }

        currentRound = data.round;
        addMessage("ai", data.reply);

        if (data.finished) {
          progressText.textContent = (window.currentLang === "en" ? "Done" : "已完成") + " · 6 / 6";
          inputHint.textContent = t("practiceDone");
          updateSendBtn();
          showReport();
        } else {
          progressText.textContent =
            t("round") + " " + (currentRound + 1) + " / " + totalRounds + " " + t("roundUnit") + " · " + data.dimension;
          updateSendBtn();
        }
      })
      .catch(function () {
        isWaiting = false;
        removeTyping();
        inputHint.textContent = "";
        addMessage("ai", t("netErr"));
        updateSendBtn();
      });
  }

  // ---------- 报告 ----------

  function showReport() {
    fetch("/api/dialog/end", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          alert(t("generateReportFail"));
          return;
        }

        reportComment.textContent = data.comment || "";

        reportHighlights.innerHTML = "";
        (data.highlights || []).forEach(function (h) {
          var li = document.createElement("li");
          li.textContent = h;
          reportHighlights.appendChild(li);
        });

        reportSuggestions.innerHTML = "";
        (data.suggestions || []).forEach(function (s) {
          var li = document.createElement("li");
          li.textContent = s;
          reportSuggestions.appendChild(li);
        });

        renderScoreTable(data.scores || [], data.total_score, data.max_score);
        renderRadar(data.scores || []);

        reportOverlay.classList.add("show");
      })
      .catch(function () { alert(t("netErr")); });
  }

  function renderScoreTable(scores, total, max) {
    if (!reportScoreTable) return;
    reportScoreTable.innerHTML = "";

    scores.forEach(function (s) {
      var row = document.createElement("div");
      row.className = "score-row";
      row.innerHTML =
        '<span class="score-dim">' + s.dimension + '</span>' +
        '<span class="score-num">' + s.score + ' / ' + s.weight + '</span>';
      reportScoreTable.appendChild(row);
    });

    var totalRow = document.createElement("div");
    totalRow.className = "score-row total";
    totalRow.innerHTML =
      '<span class="score-dim">' + (window.currentLang === "en" ? "Total" : "总分") + '</span>' +
      '<span class="score-num">' + (total || 0) + ' / ' + (max || 100) + '</span>';
    reportScoreTable.appendChild(totalRow);
  }

  // ---------- 雷达图（纯 SVG） ----------

  function renderRadar(scores) {
    if (!reportRadar || !scores.length) return;

    var size = 280;
    var cx = size / 2;
    var cy = size / 2;
    var radius = 90;
    var n = scores.length;

    function point(i, r) {
      var angle = (-Math.PI / 2) + (i * 2 * Math.PI / n);
      return {
        x: cx + Math.cos(angle) * r,
        y: cy + Math.sin(angle) * r
      };
    }

    var grid = "";
    [0.25, 0.5, 0.75, 1].forEach(function (ratio) {
      var pts = [];
      for (var i = 0; i < n; i++) {
        var p = point(i, radius * ratio);
        pts.push(p.x + "," + p.y);
      }
      grid += '<polygon points="' + pts.join(" ") + '" fill="none" stroke="#dce6f0" stroke-width="1"/>';
    });

    var axes = "";
    for (var i = 0; i < n; i++) {
      var p = point(i, radius);
      axes += '<line x1="' + cx + '" y1="' + cy + '" x2="' + p.x + '" y2="' + p.y + '" stroke="#dce6f0" stroke-width="1"/>';
    }

    var dataPts = [];
    scores.forEach(function (s, i) {
      var ratio = s.weight ? (s.score / s.weight) : 0;
      var p = point(i, radius * ratio);
      dataPts.push(p.x + "," + p.y);
    });
    var dataPolygon =
      '<polygon points="' + dataPts.join(" ") +
      '" fill="rgba(90, 159, 212, 0.25)" stroke="#5a9fd4" stroke-width="2" stroke-linejoin="round"/>';

    var dots = "";
    scores.forEach(function (s, i) {
      var ratio = s.weight ? (s.score / s.weight) : 0;
      var p = point(i, radius * ratio);
      dots += '<circle cx="' + p.x + '" cy="' + p.y + '" r="3.5" fill="#5a9fd4"/>';
    });

    var labels = "";
    scores.forEach(function (s, i) {
      var p = point(i, radius + 26);
      var anchor = "middle";
      if (p.x < cx - 10) anchor = "end";
      if (p.x > cx + 10) anchor = "start";
      labels +=
        '<text x="' + p.x + '" y="' + p.y + '" ' +
        'text-anchor="' + anchor + '" dominant-baseline="middle" ' +
        'font-size="11" fill="#5b7a99" font-family="inherit">' +
        s.dimension +
        '</text>';
    });

    reportRadar.innerHTML =
      '<svg viewBox="0 0 ' + size + ' ' + size + '" width="100%" height="' + size + '">' +
        grid + axes + dataPolygon + dots + labels +
      '</svg>';
  }

  backToModesBtn.addEventListener("click", function () {
    window.location.href = "/quiz";
  });

  retryBtn.addEventListener("click", function () {
    window.location.reload();
  });

  // ---------- 启动 ----------

  function startDialog() {
    addTyping();
    fetch("/api/dialog/start", { method: "POST" })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        removeTyping();
        if (!data.success) {
          addMessage("ai", data.message || t("cannotStartDialog"));
          return;
        }
        currentRound = 0;
        progressText.textContent = t("round") + " 1 / " + totalRounds + " " + t("roundUnit") + " · " + data.dimension;
        addMessage("ai", data.question);
        updateSendBtn();
      })
      .catch(function () {
        removeTyping();
        addMessage("ai", t("networkRetry"));
      });
  }

  function t(key) { return window.t(key); }

  window.applyLang();
  startDialog();
})();