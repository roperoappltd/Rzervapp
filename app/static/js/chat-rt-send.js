// =================================
// SEND CHAT MESSAGE
// =================================

// FIXED: these were referenced below but never actually declared
// anywhere in the codebase. That threw a ReferenceError the instant
// this script loaded, which meant the submit listener below -- the
// one with the critical e.preventDefault() -- never attached to the
// form at all. Without it, pressing Enter/clicking Send triggered the
// form's native browser submit (a real page reload), which explains
// both symptoms together: the "white screen" (an actual navigation
// flash, not a blank chat window) and the message never arriving,
// since it never reached socket.emit() at all.
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');

if (chatForm && messageInput) {
  chatForm.addEventListener('submit', function (e) {
    e.preventDefault();

    // Get message text
    const message = messageInput.value.trim();

    // Prevent empty messages

    if (message === '') {
      return;
    }

    // Send message to Flask-SocketIO
    socket.emit('send_message', {
      conversation_id: currentConversation,
      body: message,
    });

    // Clear input box

    messageInput.value = '';
  });
}
