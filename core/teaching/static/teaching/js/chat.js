// Chat room functionality
class ChatRoom {
    constructor(config) {
        this.config = config;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('micButton').addEventListener('click', () => this.toggleRecording());
        document.getElementById('sendButton').addEventListener('click', () => this.sendMessage());
        document.getElementById('newChat').addEventListener('click', () => window.location.href = this.config.urls.newChat);
    }

    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            document.getElementById('micButton').classList.add('bg-red-500', 'recording');
        } catch (err) {
            console.error('Error accessing microphone:', err);
        }
    }

    stopRecording() {
        this.mediaRecorder.stop();
        this.isRecording = false;
        document.getElementById('micButton').classList.remove('bg-red-500', 'recording');

        this.mediaRecorder.onstop = () => {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = () => {
                const base64Audio = reader.result.split(',')[1];
                this.sendMessage(base64Audio);
            };
        };
    }

    sendMessage(audioData = null) {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message && !audioData) return;

        const data = {
            message: message,
            audio_data: audioData
        };

        fetch(this.config.urls.sendMessage, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.config.csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            this.appendMessage(data.user_message, 'user');
            this.appendMessage(data.assistant_message, 'assistant');
            messageInput.value = '';
        })
        .catch(error => console.error('Error:', error));
    }

    appendMessage(message, role) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${role === 'user' ? 'justify-end' : ''}`;
        
        let content = `
            <div class="max-w-2xl ${role === 'user' ? 'bg-blue-500 text-white' : 'bg-white'} rounded-lg p-4 shadow">
                <p>${message.content}</p>
        `;

        if (message.spelling_score !== undefined) {
            content += `
                <div class="mt-2 text-sm ${role === 'user' ? 'text-blue-100' : 'text-gray-600'}">
                    <p>Spelling Score: ${message.spelling_score}%</p>
                    <p>Original Text: ${message.original_text}</p>
                </div>
            `;
        }

        content += '</div>';
        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
} 