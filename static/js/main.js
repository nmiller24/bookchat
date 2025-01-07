// DOM Elements
const messagesDiv = document.getElementById('messages');
const statusDiv = document.getElementById('status');

// Function to update status
function updateStatus(message) {
    statusDiv.textContent = message;
}

// Function to load messages
async function loadMessages() {
    try {
        updateStatus('Loading messages...');
        const response = await fetch('/api/messages');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const messages = await response.json();
        
        // Display messages
        messagesDiv.innerHTML = messages.map(msg => `
            <div class="message">
                <p>${msg.content}</p>
                <small>Created: ${new Date(msg.created_at).toLocaleString()}</small>
            </div>
        `).join('');
        
        updateStatus('Messages loaded successfully!');
    } catch (error) {
        console.error('Error loading messages:', error);
        updateStatus('Error loading messages. Check console for details.');
    }
}

// Load messages when page loads
document.addEventListener('DOMContentLoaded', loadMessages);
