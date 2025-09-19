document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const loadingIndicator = document.getElementById('loading-indicator');
    const feedbackAlert = document.getElementById('feedback-alert');

    let sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    let currentQuery = '';
    let currentResponse = null;

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        currentQuery = message;
        appendMessage(message, 'user');
        chatInput.value = '';
        showLoading(true);

        try {
            const response = await fetch('/api/v2/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: sessionId }),
            });

            if (!response.ok) {
                throw new Error('Failed to get a response from the server.');
            }

            const data = await response.json();
            currentResponse = data; // Store the full response
            appendOffers(data.results);
        } catch (error) {
            console.error('Chat error:', error);
            appendMessage('Sorry, I encountered an error. Please try again.', 'bot');
        } finally {
            showLoading(false);
        }
    });

    // Append a message to the chat window
    function appendMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>${text}</p>`;
        
        messageDiv.appendChild(contentDiv);
        chatWindow.appendChild(messageDiv);
        scrollToBottom();
    }

    // Append a grid of offers
    function appendOffers(offers) {
        if (!offers || offers.length === 0) {
            appendMessage("I couldn't find any deals matching your search. Try a different query!", 'bot');
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>Here are the top deals I found for you:</p>`;

        const offersGrid = document.createElement('div');
        offersGrid.className = 'offers-grid';

        offers.forEach(offer => {
            const card = createOfferCard(offer);
            offersGrid.appendChild(card);
        });

        contentDiv.appendChild(offersGrid);
        messageDiv.appendChild(contentDiv);
        chatWindow.appendChild(messageDiv);
        scrollToBottom();
    }

    // Create a single offer card
    function createOfferCard(offer) {
        const card = document.createElement('div');
        card.className = 'offer-card';
        card.dataset.offerId = offer.offer_id;

        const categories = offer.categories.map(cat => `<span class="offer-category">${cat}</span>`).join('');

        card.innerHTML = `
            <a href="${offer.affiliate_url}" target="_blank" class="offer-image-container" style="display: contents;">
                <img src="${offer.image_url}" alt="${offer.title}" class="offer-image" onerror="this.src='/images/placeholder.jpg'">
                <span class="offer-campaign">${offer.campaign}</span>
            </a>
            <div class="offer-details">
                <h3 class="offer-title">${offer.title}</h3>
                ${offer.coupon_code ? `<div class="offer-coupon">${offer.coupon_code}</div>` : ''}
                <div class="offer-categories">${categories}</div>
            </div>
            <div class="offer-actions">
                <div class="feedback-buttons">
                    <button class="feedback-like" title="Like"><i class="fas fa-thumbs-up"></i></button>
                    <button class="feedback-dislike" title="Dislike"><i class="fas fa-thumbs-down"></i></button>
                </div>
                <a href="${offer.affiliate_url}" target="_blank" class="btn-get-deal">Get Deal</a>
            </div>
        `;

        // Add event listeners for feedback
        card.querySelector('.feedback-like').addEventListener('click', (e) => {
            e.stopPropagation();
            handleFeedback(offer.offer_id, 'like', card);
        });

        card.querySelector('.feedback-dislike').addEventListener('click', (e) => {
            e.stopPropagation();
            handleFeedback(offer.offer_id, 'dislike', card);
        });

        return card;
    }

    // Handle feedback submission
    async function handleFeedback(offerId, feedbackType, card) {
        try {
            await fetch('/api/v2/chat/feedback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_message: currentQuery,
                    bot_response: JSON.stringify(currentResponse),
                    feedback_type: feedbackType,
                    offer_id: offerId,
                }),
            });

            showFeedbackAlert();
            
            // Update UI to show feedback was given
            const likeBtn = card.querySelector('.feedback-like');
            const dislikeBtn = card.querySelector('.feedback-dislike');
            likeBtn.classList.remove('liked', 'disliked');
            dislikeBtn.classList.remove('liked', 'disliked');

            if (feedbackType === 'like') {
                likeBtn.classList.add('liked');
            } else {
                dislikeBtn.classList.add('disliked');
            }

        } catch (error) {
            console.error('Feedback error:', error);
        }
    }

    // Show/hide loading indicator
    function showLoading(isLoading) {
        loadingIndicator.style.display = isLoading ? 'flex' : 'none';
        if (isLoading) {
            chatWindow.appendChild(loadingIndicator);
            scrollToBottom();
        } else {
            if (chatWindow.contains(loadingIndicator)) {
                chatWindow.removeChild(loadingIndicator);
            }
        }
    }

    // Show feedback alert
    function showFeedbackAlert() {
        feedbackAlert.classList.add('show');
        setTimeout(() => {
            feedbackAlert.classList.remove('show');
        }, 2000);
    }

    // Auto-scroll to the bottom of the chat window
    function scrollToBottom() {
        chatWindow.parentElement.scrollTop = chatWindow.parentElement.scrollHeight;
    }
});
