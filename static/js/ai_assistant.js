document.addEventListener('DOMContentLoaded', function() {
    const questionInput = document.getElementById('questionInput');
    const sendButton = document.getElementById('sendButton');
    const chatContainer = document.getElementById('chatContainer');
    const welcomeState = document.getElementById('welcomeState');
    const suggestionPills = document.querySelectorAll('.suggestion-pill');

    let isLoading = false;

    // Event listeners
    sendButton.addEventListener('click', handleSendMessage);
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Handle suggestion pill clicks
    suggestionPills.forEach(pill => {
        pill.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            questionInput.value = question;
            handleSendMessage();
        });
    });

    // Auto-resize input based on content
    questionInput.addEventListener('input', function() {
        updateSendButtonState();
    });

    function updateSendButtonState() {
        const hasText = questionInput.value.trim().length > 0;
        sendButton.disabled = !hasText || isLoading;
    }

    function handleSendMessage() {
        const question = questionInput.value.trim();
        if (!question || isLoading) return;

        // Hide welcome state
        if (welcomeState) {
            welcomeState.style.display = 'none';
        }

        // Add user message
        addUserMessage(question);

        // Clear input and show loading
        questionInput.value = '';
        updateSendButtonState();
        showTypingIndicator();

        // Send request to backend
        sendToBackend(question);
    }

    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="user-bubble">${escapeHtml(message)}</div>
        `;
        chatContainer.appendChild(messageDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        isLoading = true;
        updateSendButtonState();

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai-message';
        typingDiv.id = 'typingIndicator';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span>AI is thinking</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        chatContainer.appendChild(typingDiv);
        scrollToBottom();
    }

    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        isLoading = false;
        updateSendButtonState();
    }

    function addAIMessage(response) {
        hideTypingIndicator();

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';

        let aiContent = `<div class="ai-bubble">${formatResponse(response.answer)}`;

        // Add sources if available
        if (response.sources && response.sources.length > 0) {
            aiContent += '<div class="sources-section">';
            aiContent += '<div class="sources-header" onclick="toggleSources(this)">';
            aiContent += '<span>📚 Sources</span>';
            aiContent += '<span style="font-size: 11px; margin-left: auto;">▼</span>';
            aiContent += '</div>';
            aiContent += '<div class="sources-list" style="display: none;">';

            response.sources.forEach((source, index) => {
                // Safely handle content that might be undefined
                const contentText = source.content_snippet || source.content || 'No preview available';
                const safeContent = typeof contentText === 'string' ? contentText : 'No preview available';
                const snippet = safeContent.substring(0, 120);

                aiContent += `
                    <a href="/post/${source.post_id}/" class="source-item" target="_blank">
                        <div class="source-avatar">${index + 1}</div>
                        <div class="source-content">
                            <div class="source-title">${escapeHtml(source.title || 'Untitled')}</div>
                            <div class="source-snippet">${escapeHtml(snippet)}${snippet.length >= 120 ? '...' : ''}</div>
                            <div class="source-meta">by ${escapeHtml(source.author || 'Unknown')} • ${source.created_date || 'Unknown date'}</div>
                        </div>
                    </a>
                `;
            });

            aiContent += '</div>';
            aiContent += '</div>';
        }

        // Add reference links if available
        if (response.reference_posts && response.reference_posts.length > 0) {
            aiContent += '<div class="reference-links">';
            aiContent += '<div class="reference-links-label">';
            aiContent += '<span>🔗 Related Discussions</span>';
            aiContent += '</div>';
            aiContent += '<div class="reference-links-container">';

            response.reference_posts.forEach((postId, index) => {
                aiContent += `
                    <a href="/post/${postId}/" class="reference-link" target="_blank">
                        ${index + 1}
                    </a>
                `;
            });

            aiContent += '</div>';
            aiContent += '</div>';
        }

        aiContent += '</div>';
        messageDiv.innerHTML = aiContent;

        chatContainer.appendChild(messageDiv);
        scrollToBottom();
    }

    function showErrorMessage(error) {
        hideTypingIndicator();

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <strong>⚠️ Error:</strong> ${escapeHtml(error || 'Something went wrong. Please try again.')}
        `;
        chatContainer.appendChild(errorDiv);
        scrollToBottom();
    }

    function sendToBackend(question) {
        fetch('/api/ai-query/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({ question: question })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                addAIMessage(data);
            } else {
                showErrorMessage(data.error || 'Failed to get response');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage('Network error. Please check your connection and try again.');
        });
    }

    // Utility functions - make them globally accessible
    window.toggleSources = function(header) {
        const sourcesList = header.nextElementSibling;
        const arrow = header.querySelector('span:last-child');

        if (sourcesList.style.display === 'none') {
            sourcesList.style.display = 'block';
            arrow.textContent = '▲';
            arrow.style.transform = 'rotate(180deg)';
        } else {
            sourcesList.style.display = 'none';
            arrow.textContent = '▼';
            arrow.style.transform = 'rotate(0deg)';
        }
    }

    function formatResponse(text) {
        // Convert markdown-like formatting to HTML
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        });
    }

    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
               '';
    }

    // Initialize
    updateSendButtonState();

    // Focus input on load
    questionInput.focus();
});

// Add entrance animations
document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.ai-container');
    if (container) {
        container.style.opacity = '0';
        container.style.transform = 'translateY(20px)';

        requestAnimationFrame(() => {
            container.style.transition = 'all 0.5s ease-out';
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
        });
    }
});
