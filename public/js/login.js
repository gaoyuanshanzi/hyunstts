document.addEventListener("DOMContentLoaded", async () => {
  const form = document.getElementById("loginForm");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const submitBtn = document.getElementById("submitBtn");
  const btnText = submitBtn.querySelector(".btn-text");
  const btnSpinner = submitBtn.querySelector(".btn-spinner");
  const errorMessage = document.getElementById("errorMessage");

  // Check if already authenticated
  const token = localStorage.getItem("tts_auth_token");
  if (token) {
    try {
      const res = await fetch("/api/check-auth", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        window.location.href = "/";
        return;
      }
    } catch (e) {
      // Continue to login
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorMessage.classList.remove("hidden");
  }

  function hideError() {
    errorMessage.classList.add("hidden");
    errorMessage.textContent = "";
  }

  function setLoading(loading) {
    if (loading) {
      submitBtn.disabled = true;
      btnText.classList.add("hidden");
      btnSpinner.classList.remove("hidden");
    } else {
      submitBtn.disabled = false;
      btnText.classList.remove("hidden");
      btnSpinner.classList.add("hidden");
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideError();

    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!username || !password) {
      showError("아이디와 비밀번호를 모두 입력해주세요.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        if (data.token) {
          localStorage.setItem("tts_auth_token", data.token);
        }
        localStorage.setItem("tts_user", data.username || username);
        window.location.href = "/";
      } else {
        showError(data.error || "아이디 또는 비밀번호가 올바르지 않습니다.");
      }
    } catch (err) {
      console.error("Login Error:", err);
      showError("서버와의 통신에 실패했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setLoading(false);
    }
  });
});
