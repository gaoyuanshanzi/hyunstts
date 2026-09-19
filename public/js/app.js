// HyunsTTS Main Application Logic (v20260920_v5)

(function () {
  let currentAudioUrl = null;

  window.handleGenerateAudio = async function () {
    const textInput = document.getElementById("ttsTextInput");
    const langSelect = document.getElementById("languageSelect");
    const speedSlider = document.getElementById("speedSlider");
    const pitchSlider = document.getElementById("pitchSlider");
    const generateBtn = document.getElementById("generateBtn");
    const generateSpinner = document.getElementById("generateSpinner");
    const generateIcon = document.getElementById("generateIcon");
    const generateBtnText = document.getElementById("generateBtnText");
    const alertBox = document.getElementById("alertBox");
    const resultCard = document.getElementById("resultCard");
    const audioPlayer = document.getElementById("audioPlayer");
    const downloadBtn = document.getElementById("downloadBtn");
    const audioTimeBadge = document.getElementById("audioTimeBadge");

    function showAlert(msg, type = "error") {
      if (!alertBox) return;
      alertBox.textContent = msg;
      alertBox.className = `alert-box ${type}`;
      alertBox.classList.remove("hidden");
    }

    function hideAlert() {
      if (!alertBox) return;
      alertBox.classList.add("hidden");
      alertBox.textContent = "";
    }

    function setLoading(isLoading) {
      if (!generateBtn) return;
      generateBtn.disabled = isLoading;
      if (isLoading) {
        if (generateSpinner) generateSpinner.classList.remove("hidden");
        if (generateIcon) generateIcon.classList.add("hidden");
        if (generateBtnText) generateBtnText.textContent = "고음질 MP3 합성 중...";
      } else {
        if (generateSpinner) generateSpinner.classList.add("hidden");
        if (generateIcon) generateIcon.classList.remove("hidden");
        if (generateBtnText) generateBtnText.textContent = "음성 변환 시작 (Synthesize)";
      }
    }

    hideAlert();

    const text = (textInput ? textInput.value : "").trim();
    if (!text) {
      showAlert("음성으로 변환할 텍스트를 입력해주세요.", "warning");
      if (textInput) textInput.focus();
      return;
    }

    const language = langSelect ? langSelect.value : "auto";
    const gender = document.querySelector('input[name="voiceGender"]:checked')?.value || "FEMALE";
    const speed = speedSlider ? parseFloat(speedSlider.value) : 1.0;
    const pitch = pitchSlider ? parseFloat(pitchSlider.value) : 0.0;

    setLoading(true);

    const token = localStorage.getItem("tts_auth_token") || "auth_client_token";
    const headers = {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    };

    const payload = JSON.stringify({
      text,
      language,
      gender,
      speed,
      pitch
    });

    let rawBlob = null;
    let isSuccess = false;

    // Call /api/tts endpoint
    try {
      let response = await fetch("/api/tts", {
        method: "POST",
        headers: headers,
        body: payload
      });

      if (!response.ok && response.status === 404) {
        response = await fetch("/api/tts.py", {
          method: "POST",
          headers: headers,
          body: payload
        });
      }

      if (response.ok) {
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("json")) {
          const jsonErr = await response.json();
          showAlert(jsonErr.error || "음성 합성 실패", "error");
          setLoading(false);
          return;
        }

        rawBlob = await response.blob();
        if (rawBlob && rawBlob.size > 500) {
          isSuccess = true;
        }
      } else {
        let errMsg = "서버 응답 오류가 발생했습니다.";
        try {
          const errData = await response.json();
          errMsg = errData.error || errMsg;
        } catch (e) {}
        showAlert(errMsg, "error");
      }
    } catch (netErr) {
      console.error("TTS fetch network error:", netErr);
      showAlert("서버 연결에 실패했습니다. 네트워크를 확인해주세요.", "error");
    }

    // Process valid audio file
    if (isSuccess && rawBlob) {
      if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
      }

      // Create pure MP3 Blob
      const mp3Blob = new Blob([rawBlob], { type: "audio/mpeg" });
      currentAudioUrl = URL.createObjectURL(mp3Blob);

      if (audioPlayer) {
        audioPlayer.src = currentAudioUrl;
        audioPlayer.load();
        try {
          await audioPlayer.play();
        } catch (playErr) {
          console.log("Autoplay note:", playErr);
        }
      }

      const now = new Date();
      const dateStr = now.toISOString().slice(0, 10).replace(/-/g, "");
      const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, "");
      const safeLang = language === "auto" ? "auto" : language;
      const downloadFilename = `tts_${safeLang}_${dateStr}_${timeStr}.mp3`;

      if (downloadBtn) {
        downloadBtn.href = currentAudioUrl;
        downloadBtn.setAttribute("download", downloadFilename);
      }

      if (audioTimeBadge) {
        audioTimeBadge.textContent = `완료: ${now.toLocaleTimeString()}`;
      }

      if (resultCard) {
        resultCard.classList.remove("hidden");
        resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }

      setLoading(false);
      return;
    }

    // In case of error, hide corrupt result card
    if (resultCard) {
      resultCard.classList.add("hidden");
    }
    setLoading(false);
  };

  // Setup DOM listeners
  function initApp() {
    const textInput = document.getElementById("ttsTextInput");
    const charCount = document.getElementById("charCount");
    const clearBtn = document.getElementById("clearTextBtn");
    const speedSlider = document.getElementById("speedSlider");
    const speedValue = document.getElementById("speedValue");
    const pitchSlider = document.getElementById("pitchSlider");
    const pitchValue = document.getElementById("pitchValue");
    const sampleChips = document.querySelectorAll(".sample-chip");
    const logoutBtn = document.getElementById("logoutBtn");
    const userDisplay = document.getElementById("userDisplay");

    const token = localStorage.getItem("tts_auth_token");
    const user = localStorage.getItem("tts_user") || "admin";
    if (userDisplay) userDisplay.textContent = user;

    if (!token && !localStorage.getItem("tts_user")) {
      window.location.href = "/login.html";
      return;
    }

    function updateCount() {
      if (!textInput || !charCount) return;
      const count = textInput.value.length;
      charCount.textContent = `${count.toLocaleString()} / 5,000자`;
    }

    if (textInput) {
      ["input", "keyup", "change", "paste"].forEach(evt => {
        textInput.addEventListener(evt, () => setTimeout(updateCount, 10));
      });
      updateCount();
    }

    if (clearBtn && textInput) {
      clearBtn.addEventListener("click", () => {
        textInput.value = "";
        updateCount();
        textInput.focus();
      });
    }

    if (speedSlider && speedValue) {
      speedSlider.addEventListener("input", (e) => {
        speedValue.textContent = `${parseFloat(e.target.value).toFixed(2)}x`;
      });
    }

    if (pitchSlider && pitchValue) {
      pitchSlider.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        pitchValue.textContent = val > 0 ? `+${val.toFixed(1)}` : val.toFixed(1);
      });
    }

    sampleChips.forEach(chip => {
      chip.addEventListener("click", () => {
        const lang = chip.dataset.lang;
        const sampleText = chip.dataset.text;
        if (textInput && sampleText) {
          textInput.value = sampleText;
          updateCount();
        }
        const langSelect = document.getElementById("languageSelect");
        if (langSelect && lang) {
          langSelect.value = lang;
        }
      });
    });

    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("tts_auth_token");
        localStorage.removeItem("tts_user");
        window.location.href = "/login.html";
      });
    }

    const generateBtn = document.getElementById("generateBtn");
    if (generateBtn) {
      generateBtn.addEventListener("click", window.handleGenerateAudio);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
  } else {
    initApp();
  }
})();
