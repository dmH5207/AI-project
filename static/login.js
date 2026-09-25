(function () {
  var loginForm = document.getElementById("loginForm");
  var phoneInput = document.getElementById("phone");
  var passwordInput = document.getElementById("password");
  var loginRoleSelect = document.getElementById("loginRoleSelect");
  var togglePassword = document.getElementById("togglePassword");
  var loginBtn = document.getElementById("loginBtn");
  var loginMessage = document.getElementById("loginMessage");
  var loginSection = document.getElementById("loginSection");
  var registerSection = document.getElementById("registerSection");
  var toRegister = document.getElementById("toRegister");
  var toLogin = document.getElementById("toLogin");
  var registerForm = document.getElementById("registerForm");
  var regUsername = document.getElementById("regUsername");
  var regPhone = document.getElementById("regPhone");
  var regPassword = document.getElementById("regPassword");
  var regConfirm = document.getElementById("regConfirm");
  var regRole = document.getElementById("regRole");
  var registerBtn = document.getElementById("registerBtn");
  var registerMessage = document.getElementById("registerMessage");
  var forgotPasswordLink = document.getElementById("forgotPasswordLink");
  var forgotModal = document.getElementById("forgotModal");
  var forgotCancel = document.getElementById("forgotCancel");
  var forgotConfirm = document.getElementById("forgotConfirm");
  var forgotUsername = document.getElementById("forgotUsername");
  var forgotMessage = document.getElementById("forgotMessage");

  // ========= 手机号校验函数 + 实时输入监听 =========
  function t(key) { return window.t(key); }

  function getPhoneError(phone) {
    if (!phone) return t("phonePh");
    if (!/^1\d{10}$/.test(phone)) return window.currentLang === "en" ? "Invalid phone format" : "手机号格式错误";
    return "";
  }
  window.getPhoneError = getPhoneError;

  phoneInput.addEventListener("input", function () {
    var val = this.value.trim();
    var err = getPhoneError(val);
    if (err) {
      showMsg(loginMessage, err, "error");
    } else {
      showMsg(loginMessage, "", "");
    }
  });
  // ======================================================

  // ---------- 切换登录/注册 ----------

  toRegister.addEventListener("click", function (e) {
    e.preventDefault();
    loginSection.style.display = "none";
    registerSection.style.display = "";
  });

  toLogin.addEventListener("click", function (e) {
    e.preventDefault();
    registerSection.style.display = "none";
    loginSection.style.display = "";
  });

  // ---------- 密码显示/隐藏 · 线条图标切换 ----------

  var eyeOpenSVG =
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"/>' +
      '<circle cx="12" cy="12" r="3"/>' +
    '</svg>';

  var eyeClosedSVG =
    '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"/>' +
      '<path d="M3 3l18 18"/>' +
    '</svg>';

  // 初始状态：密码隐藏，按钮显示“闭眼”图标
  passwordInput.type = "password";
  togglePassword.innerHTML = eyeClosedSVG;
  togglePassword.setAttribute("aria-label", "显示密码");

  togglePassword.addEventListener("click", function () {
    if (passwordInput.type === "password") {
      passwordInput.type = "text";
      togglePassword.innerHTML = eyeOpenSVG;
      togglePassword.setAttribute("aria-label", "隐藏密码");
    } else {
      passwordInput.type = "password";
      togglePassword.innerHTML = eyeClosedSVG;
      togglePassword.setAttribute("aria-label", "显示密码");
    }
  });

  // ---------- 消息提示 ----------

  function showMsg(el, text, type) {
    el.textContent = text;
    el.className = "login-message " + type;
  }

  // ---------- 登录提交 ----------

  loginForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var phone = phoneInput.value.trim();
    var password = passwordInput.value;

    if (!/^1\d{10}$/.test(phone)) {
      showMsg(loginMessage, t("invalidPhone"), "error");
      return;
    }
    if (!password) {
      showMsg(loginMessage, t("enterPassword"), "error");
      return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = t("loggingIn");

    fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone: phone, password: password, role: loginRoleSelect.value })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(loginMessage, t("loginSuccess"), "success");
          setTimeout(function () {
            window.location.href = data.redirect || "/quiz";
          }, 800);
        } else {
          showMsg(loginMessage, data.message || t("loginFail"), "error");
          loginBtn.disabled = false;
          loginBtn.textContent = t("loginBtn");
        }
      })
      .catch(function () {
        showMsg(loginMessage, t("netErr"), "error");
        loginBtn.disabled = false;
        loginBtn.textContent = t("loginBtn");
      });
  });

  // ---------- 注册提交 ----------

  registerForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var username = regUsername.value.trim();
    var phone = regPhone.value.trim();
    var password = regPassword.value;
    var confirm = regConfirm.value;
    var role = regRole.value;

    if (!username) { showMsg(registerMessage, t("setAccount"), "error"); return; }
    if (!/^1\d{10}$/.test(phone)) { showMsg(registerMessage, getPhoneError(phone) || t("phoneHint"), "error"); return; }
    if (password.length < 6) { showMsg(registerMessage, t("errPwdLen"), "error"); return; }
    if (password !== confirm) { showMsg(registerMessage, t("errPwdMatch"), "error"); return; }

    registerBtn.disabled = true;
    registerBtn.textContent = t("registering");

    fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username, phone: phone, password: password, role: role })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(registerMessage, t("regSuccess"), "success");
          setTimeout(function () {
            registerSection.style.display = "none";
            loginSection.style.display = "";
          }, 1000);
        } else {
          showMsg(registerMessage, data.message || t("regFail"), "error");
        }
        registerBtn.disabled = false;
        registerBtn.textContent = t("registerBtn");
      })
      .catch(function () {
        showMsg(registerMessage, t("netErr"), "error");
        registerBtn.disabled = false;
        registerBtn.textContent = t("registerBtn");
      });
  });

  // ---------- 忘记密码 ----------

  forgotPasswordLink.addEventListener("click", function (e) {
    e.preventDefault();
    forgotModal.style.display = "flex";
    forgotUsername.value = "";
    forgotMessage.textContent = "";
    forgotMessage.className = "forgot-message";
  });

  forgotCancel.addEventListener("click", function () {
    forgotModal.style.display = "none";
  });

  forgotModal.addEventListener("click", function (e) {
    if (e.target === forgotModal) { forgotModal.style.display = "none"; }
  });

  forgotConfirm.addEventListener("click", function () {
    var username = forgotUsername.value.trim();
    if (!username) {
      forgotMessage.textContent = t("setAccount");
      forgotMessage.className = "forgot-message error";
      return;
    }
    forgotConfirm.disabled = true;
    forgotConfirm.textContent = t("submitting");
    fetch("/api/forgot_password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          forgotMessage.textContent = window.currentLang === "en" ? "Submitted, contact admin to reset" : "已提交，请联系管理员重置密码";
          forgotMessage.className = "forgot-message success";
        } else {
          forgotMessage.textContent = data.message || (window.currentLang === "en" ? "Submit failed" : "提交失败，请重试");
          forgotMessage.className = "forgot-message error";
        }
        forgotConfirm.disabled = false;
        forgotConfirm.textContent = t("submitBtn");
      })
      .catch(function () {
        forgotMessage.textContent = t("netErr");
        forgotMessage.className = "forgot-message error";
        forgotConfirm.disabled = false;
        forgotConfirm.textContent = t("submitBtn");
      });
  });
})();