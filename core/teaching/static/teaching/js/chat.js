// Chat room functionality
class ChatRoom {
    constructor(config) {
        this.roomId = config.roomId;
        this.csrfToken = config.csrfToken;
        this.urls = config.urls;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.currentWord = null;
        this.socket = null;

        this.setupEventListeners();
        this.connectWebSocket();
    }

    connectWebSocket() {
        this.socket = new WebSocket(this.urls.wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket connection established');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chat_message') {
                this.appendMessage(data.message);
            }
        };

        this.socket.onclose = () => {
            console.log('WebSocket connection closed');
            // Try to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    setupEventListeners() {
        const micButton = document.getElementById('micButton');
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        const generateWordsButton = document.getElementById('generateWords');

        if (generateWordsButton) {
            generateWordsButton.addEventListener('click', () => this.generateWords());
        }

        if (micButton) {
            micButton.addEventListener('click', () => this.toggleRecording());
        }

        if (sendButton && messageInput) {
            sendButton.addEventListener('click', () => {
                const message = messageInput.value.trim();
                if (message) {
                    this.sendMessage(message);
                    messageInput.value = '';
                }
            });

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const message = messageInput.value.trim();
                    if (message) {
                        this.sendMessage(message);
                        messageInput.value = '';
                    }
                }
            });
        }
    }

    async generateWords() {
        try {
            const response = await fetch(this.urls.sendMessage, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ action: 'generate_words' })
            });

            if (!response.ok) {
                throw new Error('Failed to generate words');
            }

            const data = await response.json();
            console.log('Generated words:', data);
            
            if (data.assistant_message) {
                this.appendMessage(data.assistant_message);
                // Store the generated word for later use
                this.currentWord = data.assistant_message.content;
                // Update the input field
                const messageInput = document.getElementById('messageInput');
                if (messageInput) {
                    messageInput.value = this.currentWord;
                }
            }
        } catch (error) {
            console.error('Error generating words:', error);
            alert('Failed to generate words. Please try again.');
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            this.isRecording = true;

            const micButton = document.getElementById('micButton');
            if (micButton) {
                micButton.classList.add('recording');
                micButton.classList.add('border-red-500');
                const svg = micButton.querySelector('svg');
                if (svg) {
                    svg.classList.remove('text-gray-600');
                    svg.classList.add('text-red-500');
                }
            }

            this.mediaRecorder.addEventListener('dataavailable', (event) => {
                this.audioChunks.push(event.data);
            });

            this.mediaRecorder.addEventListener('stop', () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                this.sendAudioMessage(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            });

            this.mediaRecorder.start();
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Could not access microphone. Please ensure you have granted microphone permissions.');
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;

            const micButton = document.getElementById('micButton');
            if (micButton) {
                micButton.classList.remove('recording');
                micButton.classList.remove('border-red-500');
                const svg = micButton.querySelector('svg');
                if (svg) {
                    svg.classList.remove('text-red-500');
                    svg.classList.add('text-gray-600');
                }
            }
        }
    }

    async sendMessage(content) {
        try {
            const response = await fetch(this.urls.sendMessage, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({ 
                    content,
                    expected_word: this.currentWord // Include the expected word for comparison
                })
            });

            if (!response.ok) {
                throw new Error('Failed to send message');
            }

            const data = await response.json();
            console.log('Response data:', data);
            
            if (data.user_message) {
                this.appendMessage(data.user_message);
            }
            if (data.assistant_message) {
                this.appendMessage(data.assistant_message);
            }
            if (data.feedback_message) {
                this.appendMessage(data.feedback_message);
            }
            if (data.continuation_message) {
                this.appendMessage(data.continuation_message);
            }
            
            // Update progress bar if we have the data
            if (data.current_exchange_index !== undefined && data.total_exchanges) {
                this.updateProgress(data.current_exchange_index, data.total_exchanges);
            }

            // Update expected response if provided
            if (data.expected_response) {
                const expectedText = document.getElementById('expectedText');
                if (expectedText) {
                    expectedText.textContent = data.expected_response;
                }
            }

            // Handle conversation completion
            if (data.conversation_completed) {
                const topicSelection = document.getElementById('topicSelection');
                if (topicSelection) {
                    topicSelection.style.display = 'block';
                }
                const expectedResponse = document.getElementById('expectedResponse');
                if (expectedResponse) {
                    expectedResponse.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        }
    }

    updateProgress(currentIndex, totalExchanges) {
        const progressContainer = document.querySelector('.flex.items-center.space-x-2.text-sm.text-gray-600');
        if (!progressContainer) return;

        // Get the inner flex container that holds the numbers
        const numbersContainer = progressContainer.querySelector('.flex.items-center');
        if (!numbersContainer) return;

        // Update the numbers
        const spans = numbersContainer.getElementsByTagName('span');
        if (spans.length === 3) {
            spans[0].textContent = currentIndex + 1;  // Current index (font-medium)
            spans[1].textContent = '/';  // Separator (mx-1)
            spans[2].textContent = totalExchanges;  // Total (font-normal)
        }

        // Update the progress bar
        const progressBar = progressContainer.querySelector('.bg-blue-500');
        if (progressBar) {
            const percentage = ((currentIndex + 1) / totalExchanges) * 100;
            progressBar.style.width = `${percentage}%`;
        }
    }

    async sendAudioMessage(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob);
            if (this.currentWord) {
                formData.append('expected_word', this.currentWord);
            }

            const response = await fetch(this.urls.sendMessage, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.csrfToken
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error('Failed to send audio message');
            }

            const data = await response.json();
            
            // Update messages
            if (data.user_message) {
                this.appendMessage(data.user_message);
            }
            if (data.feedback_message) {
                this.appendMessage(data.feedback_message);
            }
            if (data.continuation_message) {
                this.appendMessage(data.continuation_message);
            }

            // Update progress bar if we have the data
            if (data.current_exchange_index !== undefined && data.total_exchanges) {
                this.updateProgress(data.current_exchange_index, data.total_exchanges);
            }

            // Update expected response if provided
            if (data.expected_response) {
                const expectedText = document.getElementById('expectedText');
                if (expectedText) {
                    expectedText.textContent = data.expected_response;
                }
            }

            // Handle conversation completion
            if (data.conversation_completed) {
                const topicSelection = document.getElementById('topicSelection');
                if (topicSelection) {
                    topicSelection.style.display = 'block';
                }
                const expectedResponse = document.getElementById('expectedResponse');
                if (expectedResponse) {
                    expectedResponse.style.display = 'none';
                }
            }
            
        } catch (error) {
            console.error('Error sending audio message:', error);
            alert('Failed to send audio message. Please try again.');
        }
    }

    appendMessage(message) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }

        console.log('Appending message:', message);

        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${message.role === 'user' ? 'justify-end' : ''}`;

        const messageContent = document.createElement('div');
        messageContent.className = `max-w-2xl ${message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white'} rounded-lg p-4 shadow`;

        const contentP = document.createElement('p');
        contentP.textContent = message.content;
        messageContent.appendChild(contentP);

        if (message.spelling_score !== undefined) {
            const detailsDiv = document.createElement('div');
            detailsDiv.className = `mt-2 text-sm ${message.role === 'user' ? 'text-blue-100' : 'text-gray-600'}`;

            const scoreP = document.createElement('p');
            scoreP.textContent = `Spelling Score: ${message.spelling_score}%`;
            detailsDiv.appendChild(scoreP);

            if (message.original_text) {
                const originalP = document.createElement('p');
                originalP.textContent = `Original Text: ${message.original_text}`;
                detailsDiv.appendChild(originalP);
            }

            if (message.expected_word) {
                const expectedP = document.createElement('p');
                expectedP.textContent = `Expected Word: ${message.expected_word}`;
                detailsDiv.appendChild(expectedP);
            }

            messageContent.appendChild(detailsDiv);
        }

        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom after adding new message
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
} 