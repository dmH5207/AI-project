(function () {
  var wrongList = document.getElementById("wrongList");
  var emptyState = document.getElementById("emptyState");

  var masteredSet = {};
  var loaded = false;

  showLoading();
  loadWrongQuestions();

  setTimeout(function () {
    if (!loaded) {
      loaded = true;
      showEmpty();
    }
  }, 8000);

  function t(key) { return window.t(key); }

  function showLoading() {
    wrongList.innerHTML = '<div class="loading-card">' +
      '<div class="loading-spinner"></div>' +
      '<p>' + t("loadingWrong") + '</p>' +
    '</div>';
  }

  function loadWrongQuestions() {
    fetch("/api/wrong/list")
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.text();
      })
      .then(function (text) {
        var data;
        try { data = JSON.parse(text); } catch (e) { throw new Error("Invalid JSON"); }
        loaded = true;
        if (data && data.success && data.wrong_answers && data.wrong_answers.length > 0) {
          renderWrongList(data.wrong_answers);
        } else {
          showEmpty();
        }
      })
      .catch(function () {
        loaded = true;
        showEmpty();
      });
  }

  function renderWrongList(wrongItems) {
    emptyState.style.display = "none";
    wrongList.style.display = "";

    wrongItems.sort(function (a, b) {
      return (a.num || a.id || 0) - (b.num || b.id || 0);
    });

    wrongItems.forEach(function (item) {
      if (item.mastered) masteredSet[item.id || item.num] = true;
    });

    var html = '<div class="stats-bar">' +
      '<div class="stat-item"><span class="stat-num">' + wrongItems.length + '</span><span class="stat-label">' + t("wrongTotal") + '</span></div>' +
      '<div class="stat-item"><span class="stat-num green">' + getMasteredCount(wrongItems) + '</span><span class="stat-label">' + t("mastered") + '</span></div>' +
      '</div>';

    html += '<div class="wrong-list">';

    wrongItems.forEach(function (item, index) {
      var num = index + 1;
      var qid = item.id || item.question_id || num;
      var userAnswer = item.user_answer || item.wrong_answer || "未作答";
      var correctAnswer = item.correct_answer || item.answer || "";
      var question = item.question || item.text || "";
      var dimension = item.dimension || "综合";
      var time = item.time || "";
      var options = item.options || [];

      html += '<div class="wrong-card" data-id="' + qid + '">';

      html += '<div class="wrong-card-header">' +
        '<div class="wrong-number">' +
          '<span class="wrong-num-badge">' + num + '</span>' +
          '<span class="wrong-dimension">' + dimension + '</span>' +
        '</div>' +
        '<span class="wrong-time">' + time + '</span>' +
      '</div>';

      html += '<div class="wrong-card-body">' +
        '<p class="wrong-question">' + question + '</p>';

      if (options.length > 0) {
        html += '<div class="options-preview">';
        options.forEach(function (opt) {
          var isCorrect = (correctAnswer && opt.indexOf(correctAnswer + ".") === 0);
          var isWrong = (userAnswer && opt.indexOf(userAnswer + ".") === 0);
          var cls = "opt-preview";
          if (isCorrect) cls += " opt-correct";
          if (isWrong && !isCorrect) cls += " opt-wrong";
          html += '<div class="' + cls + '">' + opt + '</div>';
        });
        html += '</div>';
      }

      html += '<div class="answer-row">' +
          '<div class="answer-item wrong">' +
            '<span class="answer-tag error">' + t("myAnswer") + '</span>' +
            '<span class="answer-text">' + userAnswer + '</span>' +
          '</div>' +
          '<div class="answer-item correct">' +
            '<span class="answer-tag right">' + t("correctAnswer") + '</span>' +
            '<span class="answer-text">' + correctAnswer + '</span>' +
          '</div>' +
        '</div>' +
      '</div>';

      html += '<div class="expand-section">' +
        '<button class="expand-trigger" onclick="toggleExpand(this, ' + qid + ')">' +
          '<span>' + t("viewAnalysis") + '</span>' +
          '<svg class="expand-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>' +
        '</button>' +
        '<div class="expand-content" data-loaded="false">' +
          '<div class="analysis-block"><div class="analysis-title">' + t("loadingWrong") + '</div></div>' +
        '</div>' +
      '</div>';

      html += '</div>';
    });

    html += '</div>';
    wrongList.innerHTML = html;
  }

  function showEmpty() {
    wrongList.style.display = "none";
    emptyState.style.display = "";
  }

  function getMasteredCount(items) {
    return items.filter(function (item) {
      return item.mastered;
    }).length;
  }

  window.applyLang();

  window.addEventListener("langChanged", function () {
    loadWrongQuestions();
  });
})();

function toggleExpand(btn, qid) {
  var content = btn.nextElementSibling;
  var isOpen = content.classList.contains("show");

  if (isOpen) {
    content.classList.remove("show");
    btn.classList.remove("open");
    btn.querySelector("span").textContent = t("viewAnalysis");
  } else {
    content.classList.add("show");
    btn.classList.add("open");
    btn.querySelector("span").textContent = t("hideAnalysis");

    if (content.getAttribute("data-loaded") === "false") {
      loadAnalysis(qid, content);
    }
  }
}

function loadAnalysis(qid, container) {
  container.innerHTML = '<div class="analysis-block"><div class="loading-spinner" style="margin:0 auto;"></div><p style="text-align:center;color:#7a9bb8;font-size:13px;margin-top:10px;">' + t("aiAnalyzing") + '</p></div>';

  fetch("/api/wrong/analyze/" + qid, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lang: window.currentLang || "zh" })
  })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (data) {
      if (!data.success) throw new Error(data.message || "分析失败");

      var html = "";

      html += '<div class="analysis-block">' +
        '<div class="analysis-title">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>' +
          t("analysisTitle") +
        '</div>' +
        '<p class="analysis-text">' + data.analysis.replace(/\n/g, "<br>") + '</p>' +
      '</div>';

      var p = data.practice || {};
      html += '<div class="practice-block">' +
        '<div class="practice-title">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 7.2h7.6l-6 4.8 2.4 7.2-6.4-4.8-6.4 4.8 2.4-7.2-6-4.8h7.6z"/></svg>' +
          t("practiceTitle") +
        '</div>' +
        '<p class="practice-question">' + (p.question || "") + '</p>';

      if (p.options && p.options.length > 0) {
        html += '<div class="practice-options">';
        p.options.forEach(function (opt) {
          var letter = opt.charAt(0);
          html += '<div class="practice-opt" data-letter="' + letter + '" onclick="selectVariantAnswer(this, \'' + (p.answer || "") + '\')">' + opt + '</div>';
        });
        html += '</div>';
      }

      var isEn = window.currentLang === "en";
      html += '<div class="practice-hint" style="display:none;">' +
          '<div class="practice-hint-label">\uD83D\uDCA1 ' + (isEn ? "Reasoning" : "解题思路") + '</div>' +
          '<p class="practice-hint-text">' + (p.hint || "") + '</p>' +
        '</div>' +
      '</div>';

      html += '<div class="action-row">' +
        '<button class="master-btn" onclick="toggleMaster(this, ' + qid + ')">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' + t("markMastered") +
        '</button>' +
        '<button class="remove-btn" onclick="removeWrong(' + qid + ')">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 10v6M14 10v6"/></svg>' + t("remove") +
        '</button>' +
      '</div>';

      container.innerHTML = html;
      container.setAttribute("data-loaded", "true");
      container.setAttribute("data-answer", p.answer || "");
    })
    .catch(function () {
      container.innerHTML = '<div class="analysis-block">' +
        '<div class="analysis-title">' + t("analysisFail") + '</div>' +
        '<p class="analysis-text">' + t("retryLater") + '</p>' +
      '</div>';
    });
}

function toggleMaster(btn, id) {
  var isMastered = btn.classList.contains("mastered");

  if (isMastered) {
    btn.classList.remove("mastered");
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' + t("markMastered");
  } else {
    btn.classList.add("mastered");
    btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>' + t("alreadyMastered");
  }

  fetch("/api/wrong/master/" + id, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mastered: !isMastered })
  }).catch(function () {});
}

function removeWrong(id) {
  if (!confirm(t("removeConfirm"))) return;

  fetch("/api/wrong/remove/" + id, { method: "POST" })
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.success) {
        var card = document.querySelector('.wrong-card[data-id="' + id + '"]');
        if (card) {
          card.style.transition = "opacity 0.3s, transform 0.3s";
          card.style.opacity = "0";
          card.style.transform = "translateX(40px)";
          setTimeout(function () {
            card.remove();
            renumberCards();
            if (document.querySelectorAll(".wrong-card").length === 0) {
              document.getElementById("wrongList").style.display = "none";
              document.getElementById("emptyState").style.display = "";
            }
          }, 300);
        }
      }
    })
    .catch(function () {});
}

function renumberCards() {
  var cards = document.querySelectorAll(".wrong-card");
  cards.forEach(function (card, i) {
    var badge = card.querySelector(".wrong-num-badge");
    if (badge) badge.textContent = i + 1;
  });
}

function selectVariantAnswer(el, correctAnswer) {
  var container = el.closest(".expand-content");
  if (!container) return;

  var allOpts = container.querySelectorAll(".practice-opt");
  var alreadyAnswered = Array.from(allOpts).some(function (o) { return o.classList.contains("selected") || o.classList.contains("is-answer"); });
  if (alreadyAnswered) return;

  var letter = el.getAttribute("data-letter");
  var isCorrect = (letter === correctAnswer);

  allOpts.forEach(function (opt) {
    var l = opt.getAttribute("data-letter");
    if (l === correctAnswer) {
      opt.classList.add("is-answer");
    } else if (l === letter && !isCorrect) {
      opt.classList.add("is-wrong");
    }
    opt.style.pointerEvents = "none";
  });

  el.classList.add("selected");

  var hint = container.querySelector(".practice-hint");
  if (hint) hint.style.display = "";

  var isEn = window.currentLang === "en";
  var feedback = document.createElement("div");
  feedback.className = "variant-feedback " + (isCorrect ? "correct" : "wrong");
  feedback.textContent = isCorrect ? (isEn ? "\u2713 Correct!" : "\u2713 回答正确！") : (isEn ? "\u2717 Incorrect. The correct answer is " + correctAnswer : "\u2717 回答错误，正确答案是 " + correctAnswer);
  el.parentNode.appendChild(feedback);
}