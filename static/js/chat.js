// Grand Hotel AI Chat Interface
const API = "http://localhost:8000/api/v1";
let threadId = null;

// Generate thread ID if not already set
if (!localStorage.getItem('thread_id')) {
    threadId = 'thread_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('thread_id', threadId);
} else {
    threadId = localStorage.getItem('thread_id');
}

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');

// Add chat message to UI
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = role === 'ai' ? '🤖' : '👤';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';

    if (role === 'ai') {
        bubble.innerHTML = marked.parse(content);
    } else {
        bubble.textContent = content;
    }

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageDiv;
}

// Add loading indicator
function addLoading() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message ai';
    messageDiv.id = 'loading-message';

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = '<span class="loading"></span>';

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove loading indicator
function removeLoading() {
    const loading = document.getElementById('loading-message');
    if (loading) loading.remove();
}

// Send chat message
async function sendMessage(message) {
    addMessage('user', message);
    addLoading();

    try {
        const response = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                thread_id: threadId
            })
        });

        removeLoading();

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        addMessage('ai', data.reply);
    } catch (error) {
        removeLoading();
        addMessage('ai', `⚠️ Error: ${error.message}`);
    }
}

// Handle form submission
chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (message) {
        chatInput.value = '';
        sendMessage(message);
    }
});

// Load chat history on page load
async function loadChatHistory() {
    try {
        const response = await fetch(`${API}/chat/history/${threadId}`);
        if (!response.ok) return;

        const data = await response.json();
        if (data.messages && data.messages.length > 0) {
            // Clear welcome message
            chatMessages.innerHTML = '';

            for (const msg of data.messages) {
                if (msg.role === 'user') {
                    addMessage('user', msg.content);
                } else if (msg.role === 'ai') {
                    addMessage('ai', msg.content);
                }
            }
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
    }
}

// Initialize
loadChatHistory();