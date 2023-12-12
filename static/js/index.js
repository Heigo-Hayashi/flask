

function startRecognition() {
    // Web Speech API for speech recognition
    const recognition = new webkitSpeechRecognition(); // For WebKit browsers (e.g., Chrome)
    // const recognition = new SpeechRecognition(); // For non-WebKit browsers (e.g., Firefox)

    recognition.lang = 'ja-JP';
    recognition.start();

    const btnRippleElement = document.querySelector('.btnripple2');
    btnRippleElement.classList.add('addRipple');


    recognition.onresult = function (event) {
        btnRippleElement.classList.remove('addRipple');
        const user_input = event.results[0][0].transcript;
        console.log("[User]");
        console.log(user_input);

        // Send user_input to the backend for processing
        fetch('/recognize_and_respond', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_input }),
        })
        .then(response => response.json())
        .then(data =>console.log(data));
    };
}