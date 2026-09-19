// HyunsTTS Main Application Logic (v20260920_v3)

(function () {
  let currentAudioUrl = null;

  // Global handler so button works even if listener binding was delayed
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
        if (generateBtnText) generateBtnText.textContent = "음성 합성 중...";
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

    let audioBlob = null;
    let requestSuccess = false;

    // 1. Try Primary /api/tts endpoint
    try {
      const response = await fetch("/api/tts", {
        method: "POST",
        headers: headers,
        body: payload
      });

      if (response.ok) {
        audioBlob = await response.blob();
        requestSuccess = true;
      } else if (response.status === 404) {
        // Try fallback file-path endpoint
        const retryRes = await fetch("/api/tts.py", {
          method: "POST",
          headers: headers,
          body: payload
        });
        if (retryRes.ok) {
          audioBlob = await retryRes.blob();
          requestSuccess = true;
        }
      }
    } catch (netErr) {
      console.warn("Backend TTS request failed, trying client speech fallback:", netErr);
    }

    // 2. Process Output if Audio Received
    if (requestSuccess && audioBlob && audioBlob.size > 100) {
      if (currentAudioUrl) {
        URL.revokeObjectURL(currentAudioUrl);
      }
      currentAudioUrl = URL.createObjectURL(audioBlob);

      if (audioPlayer) {
        audioPlayer.src = currentAudioUrl;
        audioPlayer.load();
        try {
          await audioPlayer.play();
        } catch (e) {
          console.log("Autoplay policy prevented audio, user can play manually:", e);
        }
      }

      if (downloadBtn) {
        const now = new Date();
        const dateStr = now.toISOString().slice(0, 10).replace(/-/g, "");
        const timeStr = now.toTimeString().slice(0, 8).replace(/:/g, "");
        downloadBtn.href = currentAudioUrl;
        downloadBtn.download = `tts_${language}_${dateStr}_${timeStr}.mp3`;
      }

      if (audioTimeBadge) {
        const now = new Date();
        audioTimeBadge.textContent = `완료: ${now.toLocaleTimeString()}`;
      }

      if (resultCard) {
        resultCard.classList.remove("hidden");
        resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }

      setLoading(false);
      return;
    }

    // 3. Client Web Speech API Fallback (Guarantees voice feedback in any environment)
    if ("speechSynthesis" in window) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = speed;
        utterance.pitch = Math.max(0.1, Math.min(2.0, (pitch + 20) / 20)); // normalize pitch
        
        const langMap = {
          "ko-KR": "ko-KR",
          "en-US": "en-US",
          "zh-CN": "zh-CN",
          "ja-JP": "ja-JP",
          "pt-BR": "pt-BR",
          "es-ES": "es-ES"
        };
        if (langMap[language]) {
          utterance.lang = langMap[language];
        }

        utterance.onend = () => {
          setLoading(false);
        };
        utterance.onerror = () => {
          setLoading(false);
        };

        window.speechSynthesis.speak(utterance);

        showAlert("서버 연결 대기 중으로 브라우저 로컬 고음질 음성 엔진으로 즉시 출력되었습니다.", "warning");
        if (resultCard) resultCard.classList.remove("hidden");
      } catch (speechErr) {
        console.error("Speech synthesis error:", speechErr);
        showAlert("음성 합성 요청에 실패했습니다. 네트워크 상태 또는 서버 배포 상태를 확인해주세요.", "error");
      }
    } else {
      showAlert("서버 응답을 기다리는 중입니다. 잠시 후 다시 시도해주세요.", "error");
    }

    setLoading(false);
  };

  // Setup DOM listeners when document is ready
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

    // 1. Session check
    const token = localStorage.getItem("tts_auth_token");
    const user = localStorage.getItem("tts_user") || "admin";
    if (userDisplay) userDisplay.textContent = user;

    if (!token && !localStorage.getItem("tts_user")) {
      window.location.href = "/login.html";
      return;
    }

    // 2. Character counter updater
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

    // 3. Slider displays
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

    // 4. Sample Chips
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

    // 5. Logout
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        localStorage.removeItem("tts_auth_token");
        localStorage.removeItem("tts_user");
        try {
          await fetch("/api/logout", { method: "POST" });
        } catch (e) {}
        window.location.href = "/login.html";
      });
    }

    // 6. Generate Button listener
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
