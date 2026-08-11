// =================================
// SEND CHAT MESSAGE
// =================================

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
