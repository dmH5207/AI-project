(function () {
  var DIM_ZH = ["AI基础认知", "AI工具使用", "提示词工程", "AI结果评估与优化", "AI伦理与安全", "人机协同解决问题"];
  var DIM_EN = ["AI Fundamentals", "AI Tools", "Prompt Engineering", "AI Evaluation & Optimization", "AI Ethics & Safety", "Human-AI Collaboration"];

  var chartInstances = {};

  var resetTargetUser = "";

  var CHART_SOURCES = [
    "/static/chart.umd.min.js",
    "https://cdn.bootcdn.net/ajax/libs/Chart.js/4.4.7/chart.umd.min.js",
    "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.7/chart.umd.min.js",
  ];

  function loadChartJS(sources, callback) {
    if (typeof Chart !== "undefined") {
      callback();
      return;
    }
    if (!sources.length) {
      var section = document.getElementById("tabCharts");
      if (section) {
        section.innerHTML = '<div class="card" style="text-align:center;color:#e74c3c;padding:40px">' + t("adminChartLoadFail") + '</div>';
      }
      return;
    }
    var s = document.createElement("script");
    s.src = sources[0];
    s.onload = function () {
      if (typeof Chart !== "undefined") {
        callback();
      } else {
        loadChartJS(sources.slice(1), callback);
      }
    };
    s.onerror = function () {
      loadChartJS(sources.slice(1), callback);
    };
    document.head.appendChild(s);
  }

  var COLORS = {
    dialog: "#4a8fd4",
    practice: "#43a047",
    objective: "#e67e22",
    palette: [
      "#4a8fd4", "#43a047", "#e67e22", "#e74c3c",
      "#9b59b6", "#1abc9c", "#f39c12", "#3498db",
    ],
  };

  var statsLoaded = false;
  var chartReady = false;

  function init() {
    if (window.applyLang) window.applyLang();
    updateTitle();
    setupLangToggle();
    setupTabs();
    loadUsers();
    setupModal();
    loadChartJS(CHART_SOURCES, function () {
      chartReady = true;
    });
    if (window.addEventListener) {
      window.addEventListener("langChanged", function () {
        updateTitle();
        loadUsers();
        if (statsLoaded) {
          destroyCharts();
          loadStats();
        }
      });
    }
  }

  function setupLangToggle() {
    var toggle = document.getElementById("langToggle");
    if (toggle && window.toggleLang) {
      toggle.addEventListener("click", function () {
        window.toggleLang();
      });
    }
  }

  function updateTitle() {
    document.title = t("adminTitle") + " - " + t("sysTitle");
  }

  function destroyCharts() {
    Object.keys(chartInstances).forEach(function (k) {
      if (chartInstances[k]) {
        chartInstances[k].destroy();
        chartInstances[k] = null;
      }
    });
  }

  function dimLabel(zh) {
    if (t("adminDialog") === "Dialog") {
      var idx = DIM_ZH.indexOf(zh);
      return idx >= 0 ? DIM_EN[idx] : zh;
    }
    return zh;
  }

  function setupTabs() {
    var btns = document.querySelectorAll(".tab-btn");
    btns.forEach(function (btn) {
      btn.addEventListener("click", function () {
        btns.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        document.querySelectorAll(".tab-content").forEach(function (s) {
          s.classList.remove("active");
        });
        var isCharts = btn.getAttribute("data-tab") === "charts";
        var id = isCharts ? "tabCharts" : "tabUsers";
        document.getElementById(id).classList.add("active");
        if (isCharts && !statsLoaded) {
          if (chartReady) {
            loadStats();
          } else {
            loadChartJS(CHART_SOURCES, function () {
              chartReady = true;
              loadStats();
            });
          }
        }
      });
    });
  }

  function loadUsers() {
    fetch("/api/admin/users")
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.success) {
          location.href = "/";
          return;
        }
        renderUsers(res.users);
      })
      .catch(function () { location.href = "/"; });
  }

  function renderUsers(users) {
    var tbody = document.getElementById("userTableBody");
    if (!users.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty-hint">' + t("adminNoUsers") + '</td></tr>';
      return;
    }
    var html = "";
    users.forEach(function (u) {
      var badge = u.reset_requested
        ? '<span class="badge badge-reset">' + t("adminResetReq") + '</span>'
        : '<span class="badge badge-ok">' + t("adminStatusOk") + '</span>';
      var roleText = u.role === "admin" ? t("adminRoleAdmin") : t("adminRoleStudent");
      html += "<tr>"
        + "<td>" + esc(u.username) + "</td>"
        + "<td>" + esc(u.phone || "-") + "</td>"
        + "<td>" + roleText + "</td>"
        + "<td>" + badge + "</td>"
        + '<td><button class="btn-reset" data-user="' + esc(u.username) + '">' + t("adminResetPwd") + '</button></td>'
        + "</tr>";
    });
    tbody.innerHTML = html;

    tbody.querySelectorAll(".btn-reset").forEach(function (btn) {
      btn.addEventListener("click", function () {
        resetTargetUser = btn.getAttribute("data-user");
        document.getElementById("resetTarget").textContent = resetTargetUser;
        document.getElementById("newPwdInput").value = "";
        document.getElementById("resetMsg").textContent = "";
        document.getElementById("resetModal").style.display = "flex";
      });
    });
  }

  function setupModal() {
    document.getElementById("resetCancel").addEventListener("click", function () {
      document.getElementById("resetModal").style.display = "none";
    });
    document.getElementById("resetConfirm").addEventListener("click", function () {
      var pwd = document.getElementById("newPwdInput").value.trim();
      if (pwd.length < 6) {
        document.getElementById("resetMsg").textContent = t("adminPwdMinLen");
        return;
      }
      fetch("/api/admin/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: resetTargetUser, new_password: pwd }),
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res.success) {
            document.getElementById("resetModal").style.display = "none";
            loadUsers();
          } else {
            document.getElementById("resetMsg").textContent = res.message;
          }
        });
    });
  }

  function showChartError(msg) {
    var grid = document.querySelector(".chart-grid");
    if (grid) {
      grid.style.opacity = "1";
      grid.style.pointerEvents = "auto";
    }
    var section = document.getElementById("tabCharts");
    section.innerHTML = '<div class="card" style="text-align:center;color:#e74c3c;padding:40px">' + esc(msg) + '</div>';
  }

  function loadStats() {
    var grid = document.querySelector(".chart-grid");
    if (grid) {
      grid.style.opacity = "0.4";
      grid.style.pointerEvents = "none";
    }
    fetch("/api/admin/stats")
      .then(function (r) {
        if (!r.ok) {
          return r.text().then(function (t) { throw new Error("HTTP " + r.status + ": " + t.substring(0, 200)); });
        }
        return r.json();
      })
      .then(function (res) {
        if (grid) {
          grid.style.opacity = "1";
          grid.style.pointerEvents = "auto";
        }
        if (!res.success) {
          showChartError(res.message || t("adminStatsFail"));
          return;
        }
        renderSummary(res.summary);
        renderModeCountChart(res.student_names, res.mode_counts);
        renderLastScoreChart(res.student_names, res.mode_last_scores);
        renderDimWrongChart(res.dim_names, res.dim_wrong_counts);
        renderRadarChart(res.student_names, res.dim_names, res.radar_data);
        statsLoaded = true;
      })
      .catch(function (e) {
        showChartError(t("adminRequestFail") + ": " + (e.message || t("adminUnknownErr")));
      });
  }

  function renderSummary(s) {
    var row = document.getElementById("summaryRow");
    row.innerHTML =
      makeSummaryItem(s.student_count, t("adminStudentCount")) +
      makeSummaryItem(s.total_dialog, t("adminDialogCount")) +
      makeSummaryItem(s.total_practice, t("adminPracticeCount")) +
      makeSummaryItem(s.total_wrong, t("adminWrongTotal"));
  }

  function makeSummaryItem(num, label) {
    return '<div class="summary-item"><div class="summary-num">' + num + "</div><div class=\"summary-label\">" + label + "</div></div>";
  }

  function renderModeCountChart(names, mc) {
    chartInstances["modeCount"] = new Chart(document.getElementById("chartModeCount"), {
      type: "bar",
      data: {
        labels: names,
        datasets: [
          { label: t("adminDialog"), data: mc.dialog, backgroundColor: COLORS.dialog },
          { label: t("adminPractice"), data: mc.practice, backgroundColor: COLORS.practice },
          { label: t("adminObjective"), data: mc.objective, backgroundColor: COLORS.objective },
        ],
      },
      options: chartOpts(t("adminTimesUnit")),
    });
  }

  function renderLastScoreChart(names, ms) {
    chartInstances["lastScore"] = new Chart(document.getElementById("chartLastScore"), {
      type: "bar",
      data: {
        labels: names,
        datasets: [
          { label: t("adminDialog"), data: ms.dialog, backgroundColor: COLORS.dialog },
          { label: t("adminPractice"), data: ms.practice, backgroundColor: COLORS.practice },
          { label: t("adminObjective"), data: ms.objective, backgroundColor: COLORS.objective },
        ],
      },
      options: chartOpts(t("adminScoreUnit")),
    });
  }

  function renderDimWrongChart(dims, counts) {
    var arr = dims.map(function (d, i) { return { dim: dimLabel(d), count: counts[d] || 0 }; });
    arr.sort(function (a, b) { return b.count - a.count; });
    chartInstances["dimWrong"] = new Chart(document.getElementById("chartDimWrong"), {
      type: "doughnut",
      data: {
        labels: arr.map(function (x) { return x.dim; }),
        datasets: [{
          data: arr.map(function (x) { return x.count; }),
          backgroundColor: COLORS.palette,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom", labels: { font: { size: 11 } } },
        },
      },
    });
  }

  function renderRadarChart(names, dims, radar) {
    var datasets = names.map(function (n, i) {
      return {
        label: n,
        data: radar[n] || [],
        borderColor: COLORS.palette[i % COLORS.palette.length],
        backgroundColor: COLORS.palette[i % COLORS.palette.length] + "33",
        pointRadius: 3,
      };
    });
    var dimLabels = dims.map(function (d) { return dimLabel(d); });
    chartInstances["radar"] = new Chart(document.getElementById("chartRadar"), {
      type: "radar",
      data: { labels: dimLabels, datasets: datasets },
      options: {
        responsive: true,
        scales: {
          r: { min: 0, max: 100, ticks: { stepSize: 20, font: { size: 10 } } },
        },
        plugins: {
          legend: { position: "bottom", labels: { font: { size: 11 } } },
        },
      },
    });
  }

  function chartOpts(unit) {
    return {
      responsive: true,
      scales: {
        y: { beginAtZero: true, ticks: { font: { size: 11 } } },
        x: { ticks: { font: { size: 11 } } },
      },
      plugins: {
        legend: { position: "bottom", labels: { font: { size: 11 } } },
        tooltip: { callbacks: { label: function (c) { return c.dataset.label + ": " + c.parsed.y + unit; } } },
      },
    };
  }

  function t(key) { return (window.t) ? window.t(key) : key; }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();