function startVoice() {

    if (!("webkitSpeechRecognition" in window)) {
        alert("Voice recognition is not supported.");
        return;
    }

    const recognition =
        new webkitSpeechRecognition();

    recognition.lang =
        document.getElementById("language").value;

    recognition.start();

    recognition.onresult = function(event) {

        const question =
            event.results[0][0].transcript;

        document.getElementById("question")
            .textContent = question;

        document.getElementById("answer")
            .textContent =
            "AI is processing your question...";
    };
}
