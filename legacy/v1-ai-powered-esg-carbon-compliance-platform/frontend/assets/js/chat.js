document.addEventListener('DOMContentLoaded', () => {
    const chatForm = DOM.el('#chat-form');
    const chatInput = DOM.el('#chat-input');
    const chatHistory = DOM.el('#chat-history');
    const sendBtn = DOM.el('#send-btn');
    
    if(!chatForm) return;

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // 1. Add User Message
        appendMessage(message, 'user');
        chatInput.value = '';
        sendBtn.disabled = true;
        
        // 2. Add Typing Indicator
        const typingId = appendTypingIndicator();
        
        // 3. Call API
        try {
            // Using mock-chat.json for frontend simulation
            const response = await API.post('chat', {
                userId: 'user143',
                message: message
            }, 'mock-chat.json');
            
            // Artificial delay to show off typing animation since mock is instant
            await new Promise(r => setTimeout(r, 1000));
            
            // 4. Remove Typing Indicator and Add AI Response
            removeElement(typingId);
            if(response.success) {
                appendMessage(response.answer, 'ai');
            } else {
                appendMessage("Sorry, I encountered an error. Please try again.", 'ai');
            }
            
        } catch (error) {
            removeElement(typingId);
            appendMessage("Connection error. Please ensure the backend is running.", 'ai');
        } finally {
            sendBtn.disabled = false;
            chatInput.focus();
        }
    });
    
    function appendMessage(text, sender) {
        const row = document.createElement('div');
        row.className = sender === 'user' ? "flex gap-4 flex-row-reverse" : "flex gap-4";
        
        let avatar = '';
        let bubbleClass = '';
        
        if (sender === 'ai') {
            avatar = \`
                <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                    <span class="material-symbols-outlined text-on-primary text-sm">smart_toy</span>
                </div>
            \`;
            bubbleClass = 'bg-surface-container text-on-surface p-3 rounded-r-lg rounded-bl-lg max-w-[80%]';
        } else {
            avatar = \`
                <div class="w-8 h-8 rounded-full bg-outline-variant flex items-center justify-center shrink-0">
                    <span class="text-xs font-black">DU</span>
                </div>
            \`;
            bubbleClass = 'bg-primary text-on-primary p-3 rounded-l-lg rounded-br-lg max-w-[80%]';
        }
        
        row.innerHTML = \`
            \${avatar}
            <div class="\${bubbleClass}">
                <p class="text-xs font-medium leading-relaxed">\${text}</p>
            </div>
        \`;
        
        chatHistory.appendChild(row);
        scrollToBottom();
    }
    
    function appendTypingIndicator() {
        const id = 'typing-' + Date.now();
        const row = document.createElement('div');
        row.id = id;
        row.className = "flex gap-4";
        row.innerHTML = \`
            <div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center shrink-0">
                <span class="material-symbols-outlined text-on-primary text-sm">smart_toy</span>
            </div>
            <div class="bg-surface-container p-3 rounded-r-lg rounded-bl-lg max-w-[80%] flex items-center gap-1">
                <div class="w-1.5 h-1.5 bg-on-surface-variant rounded-full animate-bounce"></div>
                <div class="w-1.5 h-1.5 bg-on-surface-variant rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-1.5 h-1.5 bg-on-surface-variant rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
            </div>
        \`;
        chatHistory.appendChild(row);
        scrollToBottom();
        return id;
    }
    
    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
    
    function scrollToBottom() {
        chatHistory.scrollTo({
            top: chatHistory.scrollHeight,
            behavior: 'smooth'
        });
    }
});
