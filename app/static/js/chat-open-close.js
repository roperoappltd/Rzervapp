// ==========================================
// CHAT OPEN / CLOSE
// ==========================================

let currentConversation = null;

// ==========================================
// OPEN CHAT BUTTONS
// ==========================================

document.querySelectorAll('.chat-launch-btn').forEach(function (button) {
  button.addEventListener('click', function () {
    console.log('Chat button clicked');

    const conversationId = this.dataset.conversation;

    openChat(conversationId);
  });
});

// ==========================================
// GLOBAL OPEN CHAT FUNCTION
// Used by:
// - booking button
// - notification dropdown
// ==========================================

function openChat(conversationId) {
  console.log('Opening chat:', conversationId);

  currentConversation = conversationId;

  const chatModal = document.getElementById('chatModal');

  if (!chatModal) {
    console.error('chatModal missing');

    return;
  }

  // -----------------------------
  // Open popup
  // -----------------------------

  chatModal.classList.add('show');

  // -----------------------------
  // Join Socket.IO conversation room
  // -----------------------------

  socket.emit('join', {
    conversation_id: currentConversation,
  });

  // -----------------------------
  // Load saved messages
  // -----------------------------

  loadMessages(currentConversation);

  // -----------------------------
  // Mark messages as read
  // -----------------------------

  socket.emit('read_messages', {
    conversation_id: currentConversation,
  });
}

// ==========================================
// CLOSE CHAT
// ==========================================

const closeChat = document.getElementById('closeChat');

if (closeChat) {
  closeChat.addEventListener('click', function () {
    const chatModal = document.getElementById('chatModal');

    if (chatModal) {
      chatModal.classList.remove('show');
    }

    currentConversation = null;
  });
}

// ==========================================
// LOAD OLD DATABASE MESSAGES
// ==========================================

async function loadMessages(conversationId) {
  try {
    const response = await fetch(`/conversation/${conversationId}/messages`);

    const messages = await response.json();

    const chat = document.getElementById('chatMessages');

    if (!chat) {
      console.error('chatMessages missing');

      return;
    }

    chat.innerHTML = '';

    messages.forEach(function (message) {
      displayMessage(message);
    });
  } catch (error) {
    console.error('Loading messages failed:', error);
  }
}
