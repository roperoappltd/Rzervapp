// SECURITY: user-controlled text (usernames, room names) must be escaped
// before it goes into innerHTML, otherwise it runs as markup (stored XSS).
function escapeHtml(value) {
  return String(value == null ? '' : value).replace(/[&<>"'`]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;', '`': '&#96;' }[c];
  });
}

// =======================================
// RECEIVE MESSAGE
// =======================================

socket.on('receive_message', function (data) {
  displayMessage(data);
});

// =======================================
// DISPLAY MESSAGE
// =======================================

function displayMessage(data) {
  const chat = document.getElementById('chatMessages');

  if (!chat) {
    console.error('Chat window missing');

    return;
  }

  const messageDiv = document.createElement('div');

  // Current user = right side

  if (String(data.sender_id) === String(currentUserId)) {
    messageDiv.className = 'message-host';
  } else {
    messageDiv.className = 'message-guest';
  }

  messageDiv.innerHTML = `

        <div class="message-user">
            ${escapeHtml(data.user)}
        </div>


        <div class="message-bubble">
            ${data.body}
        </div>


        <div class="message-time">
            ${data.created_at}
        </div>

    `;

  chat.appendChild(messageDiv);

  chat.scrollTop = chat.scrollHeight;
}

// =======================================
// CHAT HEADER USER
// =======================================

socket.on('chat_user', function (data) {
  const name = document.getElementById('chatUserName');

  const image = document.getElementById('chatUserImage');

  if (name) {
    name.innerText = data.username;
  }

  if (image) {
    // FIXED: was missing the /profile/ subdirectory -- user images
    // live at static/userpics/profile/<file>, not static/userpics/
    // directly (confirmed against how usprofile.html itself builds
    // this same path server-side).
    image.src = '/static/userpics/profile/' + data.image;
  }
});

// =======================================
// NEW MESSAGE NOTIFICATION
// =======================================

socket.on('new_notification', function (data) {
  console.log('Notification received:', data);

  updateChatBadge(data.count);
});

// =======================================
// CLEAR NOTIFICATION
// =======================================

socket.on('notification_clear', function () {
  updateChatBadge(0);
});

// ======================================
// CHAT SECURITY WARNING
// ======================================

socket.on('chat_warning', function (data) {
  const chat = document.getElementById('chatMessages');
  const warning = document.createElement('div');

  warning.className = 'alert alert-warning text-center';

  warning.innerHTML = `

        <i data-feather="alert-triangle"></i>
        ${data.message}
        `;

  chat.appendChild(warning);

  if (window.feather) {
    feather.replace();
  }
});
