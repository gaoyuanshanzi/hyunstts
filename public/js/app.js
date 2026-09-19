document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const userDisplay = document.getElementById("userDisplay");
  const logoutBtn = document.getElementById("logoutBtn");
  const ttsTextInput = document.getElementById("ttsTextInput");
  const charCount = document.getElementById("charCount");
  const clearTextBtn = document.getElementById("clearTextBtn");
  const languageSelect = document.getElementById("languageSelect");
  const speedSlider = document.getElementById("speedSlider");
  const speedValue = document.getElementById("speedValue");
  const pitchSlider = document.getElementById("pitchSlider");
  const pitchValue = document.getElementById("pitchValue");
  const generateBtn = document.getElementById("generateBtn");
  const generateSpinner = document.getElementById("generateSpinner");
  const generateIcon = document.getElementById("generateIcon");
  const generateBtnText = document.getElementById("generateBtnText");
  const alertBox = document.getElementById("alertBox");
  const resultCard = document.getElementById("resultCard");
  const audioPlayer = document.getElementById("audioPlayer");
  const downloadBtn = document.getElementById("downloadBtn");
  const audioTimeBadge = document.getElementById("audioTimeBadge");
  const sampleChips = document.querySelectorAll(".sample-chip");

  let currentAudioUrl = null;

  // 1. Authentication Check
  async function verifyAuth() {
    const token = localStorage.getItem("tts_auth_token");
    const user = localStorage.getItem("tts_user");

    // If no token exists, redirect to login page immediately
    if (!token || !user) {
      window.location.href = "/login.html";
      return;
    }

    if (userDisplay) userDisplay.textContent = user;

    try {
      const res = await fetch("/api/check-auth", {
        headers: { "Authorization": `Bearer ${token}` }
      });

      // Only redirect if explicitly rejected by server (401)
      if (res.status === 401) {
        localStorage.removeItem("tts_auth_token");
        localStorage.removeItem("tts_user");
        window.location.href = "/login.html";
      }
    } catch (err) {
      console.warn("Auth check network error, maintaining local session:", err);
    }
  }
  verifyAuth();

  // 2. Logout Handler
  logoutBtn.addEventListener("click", async () => {
    const token = localStorage.getItem("tts_auth_token");
    try {
      await fetch("/api/logout", {
        method: "POST",
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      });
    } catch (e) {
      console.error(e);
    } finally {
      localStorage.removeItem("tts_auth_token");
      localStorage.removeItem("tts_user");
      window.location.href = "/login";
    }
  });

  // 3. Text Character Count & Clear Button
  function updateCharCount() {
    const len = ttsTextInput.value.length;
    charCount.textContent = `${len.toLocaleString()} / 5,000자`;
  }

  ttsTextInput.addEventListener("input", updateCharCount);

  clearTextBtn.addEventListener("click", () => {
    ttsTextInput.value = "";
    updateCharCount();
    ttsTextInput.focus();
  });

  // 4. Sliders Live Feedback
  speedSlider.addEventListener("input", (e) => {
    speedValue.textContent = `${parseFloat(e.target.value).toFixed(2)}x`;
  });

  pitchSlider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    pitchValue.textContent = val > 0 ? `+${val.toFixed(1)}` : val.toFixed(1);
  });

  // 5. Quick Sample Chips
  sampleChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const lang = chip.dataset.lang;
      const text = chip.dataset.text;
      ttsTextInput.value = text;
      if (lang) {
        languageSelect.value = lang;
      }
      updateCharCount();
    });
  });

  // 6. Alert Box Utility
  function showAlert(msg, type = "error") {
    alertBox.textContent = msg;
    alertBox.className = `alert-box ${type}`;
    alertBox.classList.remove("hidden");
  }

  function hideAlert() {
    alertBox.classList.add("hidden");
    alertBox.textContent = "";
  }

  // 7. Loading State Management
  function setLoading(loading) {
    if (loading) {
      generateBtn.disabled = true;
      generateSpinner.classList.remove("hidden");
      generateIcon.classList.add("hidden");
      generateBtnText.textContent = "음성 합성 중...";
    } else {
      generateBtn.disabled = false;
      generateSpinner.classList.add("hidden");
      generateIcon.classList.remove("hidden");
      generateBtnText.textContent = "음성 변환 시작 (Synthesize)";
    }
  }

  // 8. Generate TTS Audio Request
  generateBtn.addEventListener("click", async () => {
    hideAlert();

    const text = ttsTextInput.value.trim();
    if (!text) {
      showAlert("음성으로 변환할 텍스트를 입력해주세요.");
      ttsTextInput.focus();
      return;
    }

    const language = languageSelect.value;
    const gender = document.querySelector('input[name="voiceGender"]:checked')?.value || "FEMALE";
    const speed = parseFloat(speedSlider.value);
    const pitch = parseFloat(pitchSlider.value);

    setLoading(true);

    const token = localStorage.getItem("tts_auth_token");
    const headers = {
      "Content-Type": "application/json"
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      let response = await fetch("/api/tts", {
        method: "POST",
        headers: headers,
        body: JSON.stringify({ text, language, gender, speed, pitch })
      });

      // Retry alternative path if 404
      if (response.status === 404) {
        response = await fetch("/api/tts.py", {
          method: "POST",
          headers: headers,
          body: JSON.stringify({ text, language, gender, speed, pitch })
        });
      }

      if (response.status === 401) {
        showAlert("세션이 만료되었습니다. 다시 로그인해 주세요.");
        setTimeout(() => {
          window.location.href = "/login.html";
        }, 1200);
        return;
      }
        return;
      }

      if (!response.ok) {
        let errMessage = "음성 합성 요청에 실패했습니다.";
        try {
          const errData = await response.json();
          errMessage = errData.error || errMessage;
          if (errData.detail) {
            errMessage += `\n${errData.detail}`;
          }
        } catch (e) {
          errMessage = `서버 오류 (${response.status}): 잠시 후 다시 시도해주세요.`;
        }
        showAlert(errMessage, "error");
        return;
      }

      // Received MP3 Audio Blob
      const audioBlob = await response.blob();

      // Revoke previous blob URL to avoid memory leak
      if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
      }

      currentAudioUrl = URL.createObjectURL(audioBlob);

      // Setup audio player
      audioPlayer.src = currentAudioUrl;
      audioPlayer.load();

      // Setup Download Link
      const now = new Date();
      const dateStr = now.toISOString().slice(0, 10).replace(/-/g, "");
      const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, "");
      const langTag = language === "auto" ? "auto" : language;
      const filename = `tts_${langTag}_${dateStr}_${timeStr}.mp3`;

      downloadBtn.href = currentAudioUrl;
      downloadBtn.download = filename;

      // Update Timestamp
      const formattedTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      audioTimeBadge.textContent = `합성 완료: ${formattedTime}`;

      // Show Result Card & Auto-play
      resultCard.classList.remove("hidden");
      resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });

      try {
        await audioPlayer.play();
      } catch (playErr) {
        console.log("Auto-play prevented by browser policy:", playErr);
      }

    } catch (networkErr) {
      console.error("TTS Network Error:", networkErr);
      showAlert("서버 연결에 실패했습니다. 네트워크 상태를 확인해주세요.", "error");
    } finally {
      setLoading(false);
    }
  });

  // Initial char count update
  updateCharCount();
});
