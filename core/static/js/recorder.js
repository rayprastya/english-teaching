// static/js/recorder.js
let mediaRecorder;
let audioChunks = [];

const startBtn = document.getElementById("startRecord");
const stopBtn = document.getElementById("stopRecord");

startBtn.onclick = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);

  audioChunks = [];
  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);

  mediaRecorder.onstop = () => {
    const blob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append("audio", blob, "voice.wav");
    formData.append("word", document.getElementById("word").value);

    fetch("/room/", {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      document.getElementById("result").innerText =
        `You said: ${data.transcribed}, Score: ${data.score}%`;
    });
  };

  mediaRecorder.start();
};

stopBtn.onclick = () => {
  mediaRecorder.stop();
};

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    for (const cookie of document.cookie.split(";")) {
      if (cookie.trim().startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.trim().split("=")[1]);
      }
    }
  }
  return cookieValue;
}
