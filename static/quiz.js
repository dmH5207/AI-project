(function () {
  var modeArea = document.getElementById("modeArea");
  var modeGrid = document.getElementById("modeGrid");
  var greeting = document.getElementById("greeting");

  var quizArea = document.getElementById("quizArea");
  var resultArea = document.getElementById("resultArea");

  var progressText = document.getElementById("progressText");
  var progressFill = document.getElementById("progressFill");
  var dimensionLabel = document.getElementById("dimensionLabel");
  var questionText = document.getElementById("questionText");
  var optionsBox = document.getElementById("optionsBox");
  var nextBtn = document.getElementById("nextBtn");

  var scoreNum = document.getElementById("scoreNum");
  var resultDetail = document.getElementById("resultDetail");
  var toWrongBtn = document.getElementById("toWrongBtn");
  var restartBtn = document.getElementById("restartBtn");

  var currentMode = null;
  var currentQuestion = null;
  var currentIndex = 0;
  var totalQuestions = 0;
  var selectedAnswer = null;
  var correctCount = 0;

  var ICONS = {
    dialog:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M21 12a8 8 0 0 1-8 8H4l2-3a8 8 0 1 1 15-5z"/>' +
      '</svg>',
    practice:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M14 3l7 7-11 11H3v-7z"/>' +
        '<path d="M12 5l7 7"/>' +
      '</svg>',
    objective:
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
        '<path d="M9 11l3 3L22 4"/>' +
        '<path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>' +
      '</svg>'
  };

  // ---------- 拉模式列表 ----------

  function loadModes() {
    fetch("/api/modes", { method: "POST" })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          alert(data.message || t("loadFail"));
          return;
        }

        if (data.greeting) {
          if (data.greeting.notLoggedIn) {
            greeting.textContent = t("pleaseLogin");
          } else {
            greeting.textContent = t(data.greeting.timeKey) + "，" + data.greeting.display + "！" + t("greetingSuffix");
          }
        }

        modeGrid.innerHTML = "";
        data.modes.forEach(function (m) {
          var card = document.createElement("button");
          card.className = "mode-card";
          card.setAttribute("data-mode", m.key);

          var statHTML = "";
          if (m.count === 0) {
            statHTML = t("noRecord");
          } else if (m.last === null || m.last === undefined) {
            statHTML = t("practiced") + " <strong>" + m.count + "</strong> " + t("times");
          } else {
            statHTML = t("practiced") + " <strong>" + m.count + "</strong> " + t("times") + " · " + t("lastScore") + " <strong>" + m.last + "</strong> " + t("scoreUnit");
          }

          card.innerHTML =
            '<div class="mode-icon">' + ICONS[m.key] + '</div>' +
            '<div>' +
              '<div class="mode-title">' + t(m.nameKey) + '</div>' +
              '<div class="mode-desc">' + t(m.descKey) + '</div>' +
            '</div>' +
            '<div class="mode-stat">' + statHTML + '</div>';

          card.addEventListener("click", function () {
            if (m.key === "dialog") {
              window.location.href = "/dialog";
              return;
            }
            if (m.key === "practice") {
              window.location.href = "/practice";
              return;
            }
            currentMode = m.key;
            modeArea.style.display = "none";
            quizArea.style.display = "";
            startQuiz();
          });

          modeGrid.appendChild(card);
        });
      })
      .catch(function () {
        alert(t("networkRetry"));
      });
  }

  // ---------- 开始答题 ----------

  function startQuiz() {
    fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: currentMode })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          alert(data.message || t("cannotStart"));
          return;
        }
        totalQuestions = data.total;
        correctCount = 0;
        renderQuestion(data.question, 0);
      })
      .catch(function () {
        alert(t("networkRetry"));
      });
  }

  // ---------- 渲染题目 ----------

  function renderQuestion(q, index) {
    currentQuestion = q;
    currentIndex = index;
    selectedAnswer = null;

    progressText.textContent = (index + 1) + " / " + totalQuestions;
    progressFill.style.width = ((index + 1) / totalQuestions * 100) + "%";
    dimensionLabel.textContent = (q.dimension || "—") + " · " + t("dimension");
    questionText.textContent = q.question;

    optionsBox.innerHTML = "";
    q.options.forEach(function (opt, i) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "option-btn";
      btn.textContent = opt;
      btn.dataset.value = String.fromCharCode(65 + i);
      btn.addEventListener("click", function () {
        Array.prototype.forEach.call(optionsBox.children, function (el) {
          el.classList.remove("selected");
        });
        btn.classList.add("selected");
        selectedAnswer = btn.dataset.value;
        nextBtn.disabled = false;
      });
      optionsBox.appendChild(btn);
    });

    nextBtn.disabled = true;
    nextBtn.textContent = (index + 1 === totalQuestions) ? t("submit") : t("nextQ");
  }

  // ---------- 下一题 / 提交 ----------

  nextBtn.addEventListener("click", function () {
    if (!selectedAnswer) return;

    fetch("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: currentQuestion.id,
        answer: selectedAnswer,
        mode: currentMode
      })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.correct) correctCount++;

        if (currentIndex + 1 < totalQuestions) {
          return fetch("/api/next", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: currentMode, index: currentIndex + 1 })
          })
            .then(function (r) { return r.json(); })
            .then(function (d) {
              if (d.success) renderQuestion(d.question, currentIndex + 1);
            });
        } else {
          showResult();
        }
      })
      .catch(function () {
        alert(t("netErr"));
      });
  });

  // ---------- 即时报告 ----------

  function showResult() {
    fetch("/api/report_now", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: currentMode })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        quizArea.style.display = "none";
        resultArea.style.display = "";
        scoreNum.textContent = data.score;
        if (window.currentLang === "en") {
          resultDetail.textContent = data.total + " questions, " + data.correct + " correct";
        } else {
          resultDetail.textContent = "共 " + data.total + " 题，答对 " + data.correct + " 题";
        }
      })
      .catch(function () {
        alert(t("netErr"));
      });
  }

  // ---------- 报告区按钮 ----------

  toWrongBtn.addEventListener("click", function () {
    window.location.href = "/wrong";
  });

  restartBtn.addEventListener("click", function () {
    resultArea.style.display = "none";
    quizArea.style.display = "none";
    modeArea.style.display = "";
    currentMode = null;
    loadModes();
  });

  // ---------- 启动 ----------

  function t(key) { return window.t(key); }

  window.applyLang();
  loadModes();

  window.addEventListener("langChanged", function () {
    loadModes();
  });
})();