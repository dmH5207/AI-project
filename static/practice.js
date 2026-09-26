(function () {
  var progressText = document.getElementById("progressText");
  var taskArea = document.getElementById("taskArea");
  var reportArea = document.getElementById("reportArea");

  var taskTitle = document.getElementById("taskTitle");
  var taskDesc = document.getElementById("taskDesc");

  var stepDimension = document.getElementById("stepDimension");
  var stepQuestion = document.getElementById("stepQuestion");
  var answerInput = document.getElementById("answerInput");
  var submitBtn = document.getElementById("submitBtn");

  var feedbackCard = document.getElementById("feedbackCard");
  var feedbackText = document.getElementById("feedbackText");
  var nextStepBtn = document.getElementById("nextStepBtn");

  var reportComment = document.getElementById("reportComment");
  var reportHighlights = document.getElementById("reportHighlights");
  var reportSuggestions = document.getElementById("reportSuggestions");
  var reportScoreTable = document.getElementById("reportScoreTable");
  var reportRadar = document.getElementById("reportRadar");
  var backToModesBtn = document.getElementById("backToModesBtn");
  var retryBtn = document.getElementById("retryBtn");

  var stepDots = document.querySelectorAll(".step-dot");

  var totalSteps = 5;
  var currentStep = 0;   // 0 表示第 1 步（未提交）
  var isWaiting = false;

  // ---------- 更新步骤指示 ----------

  function updateStepDots(active, done) {
    stepDots.forEach(function (dot) {
      var n = parseInt(dot.dataset.step, 10);
      dot.classList.remove("active", "done");
      if (n < active) dot.classList.add("done");
      if (n === active) dot.classList.add("active");
    });
  }

  // ---------- 输入框 ----------

  answerInput.addEventListener("input", function () {
    submitBtn.disabled = !answerInput.value.trim() || isWaiting;
  });

  // ---------- 提交这一步 ----------

  submitBtn.addEventListener("click", function () {
    var text = answerInput.value.trim();
    if (!text || isWaiting) return;

    isWaiting = true;
    submitBtn.disabled = true;
    submitBtn.textContent = window.currentLang === "en" ? "AI reviewing..." : "AI 正在点评...";

    fetch("/api/practice/step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step: currentStep, answer: text, lang: window.currentLang || "zh" })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        isWaiting = false;
        submitBtn.textContent = window.currentLang === "en" ? "Submit" : "提交这一步";

        if (!data.success) {
          alert(data.message || (window.currentLang === "en" ? "Error occurred" : "出错了"));
          submitBtn.disabled = false;
          return;
        }

        // 显示反馈
        feedbackText.textContent = data.feedback;
        feedbackCard.style.display = "";

        // 更新进度
        if (data.finished) {
          nextStepBtn.textContent = window.currentLang === "en" ? "View Report" : "查看报告";
        } else {
          nextStepBtn.textContent = window.currentLang === "en" ? "Next Step" : "进入下一步";
        }

        // 禁止继续编辑
        answerInput.disabled = true;
        submitBtn.disabled = true;

        // 记下当前步号（用于下一步）
        currentStep = data.step;   // 已完成步数
      })
      .catch(function () {
        isWaiting = false;
        submitBtn.disabled = false;
        submitBtn.textContent = window.currentLang === "en" ? "Submit" : "提交这一步";
        alert(window.currentLang === "en" ? "Network error, please retry later" : "网络错误，请稍后重试");
      });
  });

  // ---------- 进入下一步 ----------

  nextStepBtn.addEventListener("click", function () {
    // 如果已经结束，直接出报告
    if (currentStep >= totalSteps) {
      showReport();
      return;
    }

    // 否则加载下一步
    loadStep(currentStep);
  });

  // ---------- 加载某一步 ----------

  function loadStep(index) {
    feedbackCard.style.display = "none";
    answerInput.disabled = false;
    answerInput.value = "";
    submitBtn.disabled = true;
    submitBtn.textContent = window.currentLang === "en" ? "Submit" : "提交这一步";

    fetch("/api/practice/step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step: index, fetch_only: true, lang: window.currentLang || "zh" })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          alert(data.message || (window.currentLang === "en" ? "Cannot load this step" : "无法加载该步骤"));
          return;
        }
        var isEn = window.currentLang === "en";
        stepDimension.textContent = (isEn ? "Dimension: " : "维度：") + ((isEn && data.dimension_en) ? data.dimension_en : data.dimension);
        stepQuestion.textContent = (isEn && data.question_en) ? data.question_en : data.question;
        progressText.textContent = (isEn ? "Step " : "第 ") + (index + 1) + " / " + totalSteps + (isEn ? "" : " 步");
        updateStepDots(index + 1);
        answerInput.focus();
      })
      .catch(function () {
        alert(window.currentLang === "en" ? "Network error" : "网络错误");
      });
  }

  // ---------- 加载任务（启动） ----------

  function startPractice() {
    fetch("/api/practice/start", { method: "POST" })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          alert(data.message || (window.currentLang === "en" ? "Cannot start practice" : "无法开始练习"));
          return;
        }
        taskTitle.textContent = (window.currentLang === "en" && data.task_title_en) ? data.task_title_en : data.task_title;
        taskDesc.textContent = (window.currentLang === "en" && data.task_desc_en) ? data.task_desc_en : data.task_desc;
        try { sessionStorage.setItem("practiceTask", JSON.stringify(data)); } catch (e) {}
        loadStep(0);
      })
      .catch(function () {
        alert(window.currentLang === "en" ? "Network error, please refresh" : "网络错误，请刷新重试");
      });
  }

  function refreshStepText(index) {
    fetch("/api/practice/step", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step: index, fetch_only: true, lang: window.currentLang || "zh" })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) return;
        var isEn = window.currentLang === "en";
        stepDimension.textContent = (isEn ? "Dimension: " : "维度：") + ((isEn && data.dimension_en) ? data.dimension_en : data.dimension);
        stepQuestion.textContent = (isEn && data.question_en) ? data.question_en : data.question;
        progressText.textContent = (isEn ? "Step " : "第 ") + (index + 1) + " / " + totalSteps + (isEn ? "" : " 步");
      });
  }

  if (window.addEventListener) {
    window.addEventListener("langChanged", function () {
      if (taskArea.style.display !== "none") {
        var task = null;
        try { task = JSON.parse(sessionStorage.getItem("practiceTask") || "null"); } catch (e) {}
        if (task) {
          var isEn0 = window.currentLang === "en";
          taskTitle.textContent = (isEn0 && task.task_title_en) ? task.task_title_en : task.task_title;
          taskDesc.textContent = (isEn0 && task.task_desc_en) ? task.task_desc_en : task.task_desc;
        }
        var isEn2 = window.currentLang === "en";
        if (answerInput.disabled && currentStep > 0 && currentStep <= totalSteps) {
          refreshStepText(currentStep - 1);
          submitBtn.textContent = isEn2 ? "Submit" : "提交这一步";
          if (currentStep >= totalSteps) {
            nextStepBtn.textContent = isEn2 ? "View Report" : "查看报告";
          } else {
            nextStepBtn.textContent = isEn2 ? "Next Step" : "进入下一步";
          }
        } else if (currentStep < totalSteps) {
          loadStep(currentStep);
        } else {
          progressText.textContent = isEn2 ? "All steps completed" : "所有步骤已完成";
          nextStepBtn.textContent = isEn2 ? "View Report" : "查看报告";
        }
      }
      if (reportArea.style.display !== "none") {
        showReport();
      }
    });
  }

  // ---------- 报告 ----------

  function showReport() {
    taskArea.style.display = "none";
    reportArea.style.display = "";

    fetch("/api/practice/end", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lang: window.currentLang || "zh" })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.success) {
          alert(window.currentLang === "en" ? "Failed to generate report" : "生成报告失败");
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

        window.scrollTo(0, 0);
      })
      .catch(function () { alert(window.currentLang === "en" ? "Network error" : "网络错误"); });
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

  // ---------- 雷达图 ----------

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
      '" fill="rgba(77, 191, 164, 0.25)" stroke="#4dbfa4" stroke-width="2" stroke-linejoin="round"/>';

    var dots = "";
    scores.forEach(function (s, i) {
      var ratio = s.weight ? (s.score / s.weight) : 0;
      var p = point(i, radius * ratio);
      dots += '<circle cx="' + p.x + '" cy="' + p.y + '" r="3.5" fill="#4dbfa4"/>';
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

  // ---------- 报告按钮 ----------

  backToModesBtn.addEventListener("click", function () {
    window.location.href = "/quiz";
  });

  retryBtn.addEventListener("click", function () {
    window.location.reload();
  });

  // ---------- 启动 ----------

  if (window.applyLang) window.applyLang();

  var langToggleEl = document.getElementById("langToggle");
  if (langToggleEl && window.toggleLang) {
    langToggleEl.addEventListener("click", function () {
      window.toggleLang();
    });
  }
  document.querySelectorAll(".lang-label").forEach(function (el) {
    el.addEventListener("click", function () {
      var lang = el.getAttribute("data-lang");
      if (lang && window.setLang) window.setLang(lang);
    });
  });

  startPractice();
})();