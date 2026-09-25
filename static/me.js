(function () {
  var profileName = document.getElementById("profileName");
  var profileRole = document.getElementById("profileRole");
  var profilePhone = document.getElementById("profilePhone");
  var profileRoleText = document.getElementById("profileRoleText");

  var changePwdBtn = document.getElementById("changePwdBtn");
  var switchLoginBtn = document.getElementById("switchLoginBtn");
  var logoutBtn = document.getElementById("logoutBtn");

  var changePwdModal = document.getElementById("changePwdModal");
  var oldPassword = document.getElementById("oldPassword");
  var newPassword = document.getElementById("newPassword");
  var confirmPassword = document.getElementById("confirmPassword");
  var pwdCancel = document.getElementById("pwdCancel");
  var pwdConfirm = document.getElementById("pwdConfirm");
  var pwdMessage = document.getElementById("pwdMessage");

  var logoutModal = document.getElementById("logoutModal");
  var logoutCancel = document.getElementById("logoutCancel");
  var logoutConfirm = document.getElementById("logoutConfirm");

  var langToggle = document.getElementById("langToggle");

  var currentUserRole = "";
  var avatarImg = document.getElementById("avatarImg");
  var avatarBox = document.getElementById("avatarBox");
  var avatarOverlay = document.getElementById("avatarOverlay");
  var avatarInput = document.getElementById("avatarInput");

  function t(key) { return window.t(key); }

  function roleMap(role) { return t(role) || role; }

  var origApplyLang = window.applyLang;
  window.applyLang = function () {
    origApplyLang();
    if (currentUserRole) {
      profileRole.textContent = roleMap(currentUserRole);
      profileRoleText.textContent = roleMap(currentUserRole);
    }
  };

  langToggle.addEventListener("click", function () {
    window.toggleLang();
  });

  window.applyLang();

  function showMsg(el, text, type) {
    el.textContent = text;
    el.className = "modal-message " + type;
  }

  function openModal(el) {
    el.classList.add("show");
  }

  function closeModal(el) {
    el.classList.remove("show");
  }

  fetch("/api/me/info")
    .then(function (res) { return res.json(); })
    .then(function (data) {
      if (data.success) {
        var d = data.data;
        currentUserRole = d.role;
        profileName.textContent = d.username;
        profileRole.textContent = roleMap(d.role);
        profilePhone.textContent = d.phone || "--";
        profileRoleText.textContent = roleMap(d.role);
        if (d.avatar) {
          avatarImg.src = d.avatar;
        }
      } else {
        window.location.href = "/";
      }
    })
    .catch(function () {
      window.location.href = "/";
    });

  avatarBox.addEventListener("click", function () {
    avatarInput.click();
  });

  avatarInput.addEventListener("change", function () {
    var file = avatarInput.files[0];
    if (!file) return;
    var allowedTypes = ["image/png", "image/jpeg", "image/gif", "image/webp"];
    if (allowedTypes.indexOf(file.type) === -1) {
      alert(t("avatarTypeErr") || "仅支持 png/jpg/gif/webp 格式");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      alert(t("avatarSizeErr") || "图片大小不能超过 2MB");
      return;
    }
    var formData = new FormData();
    formData.append("avatar", file);
    avatarOverlay.classList.add("uploading");
    fetch("/api/me/upload_avatar", {
      method: "POST",
      body: formData
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        avatarOverlay.classList.remove("uploading");
        if (data.success) {
          avatarImg.src = data.avatar + "?t=" + Date.now();
        } else {
          alert(data.message || t("netErr"));
        }
        avatarInput.value = "";
      })
      .catch(function () {
        avatarOverlay.classList.remove("uploading");
        alert(t("netErr"));
        avatarInput.value = "";
      });
  });

  changePwdBtn.addEventListener("click", function () {
    oldPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
    showMsg(pwdMessage, "", "");
    openModal(changePwdModal);
  });

  pwdCancel.addEventListener("click", function () {
    closeModal(changePwdModal);
  });

  pwdConfirm.addEventListener("click", function () {
    var oldPwd = oldPassword.value;
    var newPwd = newPassword.value;
    var confirmPwd = confirmPassword.value;

    if (!oldPwd) { showMsg(pwdMessage, t("errOldPwd"), "error"); return; }
    if (!newPwd) { showMsg(pwdMessage, t("errNewPwd"), "error"); return; }
    if (newPwd.length < 6) { showMsg(pwdMessage, t("errPwdLen"), "error"); return; }
    if (newPwd !== confirmPwd) { showMsg(pwdMessage, t("errPwdMatch"), "error"); return; }

    pwdConfirm.disabled = true;
    pwdConfirm.textContent = t("submitting");

    fetch("/api/me/change_password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(pwdMessage, t("pwdOk"), "success");
          setTimeout(function () { closeModal(changePwdModal); }, 1200);
        } else {
          showMsg(pwdMessage, data.message || t("netErr"), "error");
        }
        pwdConfirm.disabled = false;
        pwdConfirm.textContent = t("confirm");
      })
      .catch(function () {
        showMsg(pwdMessage, t("netErr"), "error");
        pwdConfirm.disabled = false;
        pwdConfirm.textContent = t("confirm");
      });
  });

  switchLoginBtn.addEventListener("click", function () {
    fetch("/api/logout", { method: "POST" })
      .then(function () { window.location.href = "/"; })
      .catch(function () { window.location.href = "/"; });
  });

  logoutBtn.addEventListener("click", function () {
    openModal(logoutModal);
  });

  logoutCancel.addEventListener("click", function () {
    closeModal(logoutModal);
  });

  logoutConfirm.addEventListener("click", function () {
    logoutConfirm.disabled = true;
    logoutConfirm.textContent = t("loggingOut");
    fetch("/api/logout", { method: "POST" })
      .then(function () { window.location.href = "/"; })
      .catch(function () { window.location.href = "/"; });
  });

  changePwdModal.addEventListener("click", function (e) {
    if (e.target === changePwdModal) closeModal(changePwdModal);
  });

  logoutModal.addEventListener("click", function (e) {
    if (e.target === logoutModal) closeModal(logoutModal);
  });
})();