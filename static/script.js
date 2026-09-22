(function () {
  var loginForm = document.getElementById("loginForm");
  var phoneInput = document.getElementById("phone");
  var phoneHint = document.getElementById("phoneHint");
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
  var regPhoneHint = document.getElementById("regPhoneHint");
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

  /* ---------- 公共：手机号校验 ---------- */

  function getPhoneError(phone) {
    if (!phone) return "请输入手机号";
    if (/[^0-9]/.test(phone)) return "手机号只能输入数字";
    if (phone.length !== 11) return "手机号码需为11位数字";
    if (!/^1\d{10}$/.test(phone)) return "仅支持中国大陆手机号";
    return null;
  }

  function renderPhoneHint(hintEl, error, isTouched) {
    if (isTouched && error) {
      hintEl.textContent = error;
      hintEl.className = "field-hint error";
    } else {
      hintEl.textContent = "请输入中国大陆11位手机号码";
      hintEl.className = "field-hint";
    }
  }

  function bindPhoneRealtimeCheck(inputEl, hintEl) {
    var touched = false;
    function check() {
      renderPhoneHint(hintEl, getPhoneError(inputEl.value.trim()), touched);
    }
    ["focus", "input", "blur"].forEach(function (evt) {
      inputEl.addEventListener(evt, function () {
        touched = true;
        check();
      });
    });
  }

  bindPhoneRealtimeCheck(phoneInput, phoneHint);
  bindPhoneRealtimeCheck(regPhone, regPhoneHint);

  /* ---------- 切换登录/注册 ---------- */

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

  /* ---------- 密码显示/隐藏 · SVG 图标切换 ---------- */

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

  // 初始：密文 + 闭眼图标
  passwordInput.type = "password";
  togglePassword.innerHTML = eyeClosedSVG;

  togglePassword.addEventListener("click", function () {
    var isHidden = passwordInput.type === "password";
    passwordInput.type = isHidden ? "text" : "password";
    togglePassword.innerHTML = isHidden ? eyeOpenSVG : eyeClosedSVG;
    togglePassword.setAttribute("aria-label", isHidden ? "隐藏密码" : "显示密码");
  });

  /* ---------- 消息提示 ---------- */

  function showMsg(el, text, type) {
    el.textContent = text;
    el.className = "login-message " + type;
  }

  /* ---------- 登录提交 ---------- */

  loginForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var phone = phoneInput.value.trim();
    var password = passwordInput.value;

    var phoneError = getPhoneError(phone);
    if (phoneError) { showMsg(loginMessage, phoneError, "error"); return; }
    if (!password) { showMsg(loginMessage, "请输入密码", "error"); return; }

    loginBtn.disabled = true;
    loginBtn.textContent = "登录中...";

    fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone: phone, password: password, role: loginRoleSelect.value })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(loginMessage, "登录成功，正在跳转...", "success");
          setTimeout(function () {
            window.location.href = data.redirect || "/quiz";
          }, 800);
        } else {
          showMsg(loginMessage, data.message || "手机号或密码错误", "error");
          loginBtn.disabled = false;
          loginBtn.textContent = "登 录";
        }
      })
      .catch(function () {
        showMsg(loginMessage, "网络错误，请稍后重试", "error");
        loginBtn.disabled = false;
        loginBtn.textContent = "登 录";
      });
  });

  /* ---------- 注册提交 ---------- */

  registerForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var username = regUsername.value.trim();
    var phone = regPhone.value.trim();
    var password = regPassword.value;
    var confirm = regConfirm.value;
    var role = regRole.value;

    if (!username) { showMsg(registerMessage, "请设置账号", "error"); return; }

    var phoneError = getPhoneError(phone);
    if (phoneError) { showMsg(registerMessage, phoneError, "error"); return; }

    if (password.length < 6) { showMsg(registerMessage, "密码至少6位", "error"); return; }
    if (password !== confirm) { showMsg(registerMessage, "两次密码不一致", "error"); return; }

    registerBtn.disabled = true;
    registerBtn.textContent = "注册中...";

    fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username, phone: phone, password: password, role: role })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(registerMessage, "注册成功，请登录", "success");
          setTimeout(function () {
            registerSection.style.display = "none";
            loginSection.style.display = "";
          }, 1000);
        } else {
          showMsg(registerMessage, data.message || "注册失败", "error");
        }
        registerBtn.disabled = false;
        registerBtn.textContent = "注 册";
      })
      .catch(function () {
        showMsg(registerMessage, "网络错误，请稍后重试", "error");
        registerBtn.disabled = false;
        registerBtn.textContent = "注 册";
      });
  });

  /* ---------- 忘记密码 ---------- */

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
      forgotMessage.textContent = "请输入账号";
      forgotMessage.className = "forgot-message error";
      return;
    }
    forgotConfirm.disabled = true;
    forgotConfirm.textContent = "提交中...";
    fetch("/api/forgot_password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: username })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          forgotMessage.textContent = "已提交，请联系管理员重置密码";
          forgotMessage.className = "forgot-message success";
        } else {
          forgotMessage.textContent = data.message || "提交失败，请重试";
          forgotMessage.className = "forgot-message error";
        }
        forgotConfirm.disabled = false;
        forgotConfirm.textContent = "提交";
      })
      .catch(function () {
        forgotMessage.textContent = "网络错误，请稍后重试";
        forgotMessage.className = "forgot-message error";
        forgotConfirm.disabled = false;
        forgotConfirm.textContent = "提交";
      });
  });
})();