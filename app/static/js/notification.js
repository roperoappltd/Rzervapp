// ==========================================
// GLOBAL CHAT NOTIFICATION SYSTEM
// ==========================================

// ==========================================
// LOAD UNREAD COUNT
// ==========================================

async function loadUnreadCount() {
  try {
    const response = await fetch('/chat/unread-count');

    const data = await response.json();

    updateChatBadge(data.count);
  } catch (error) {
    console.error('Unread count error:', error);
  }
}

// ==========================================
// UPDATE NAVBAR BADGE
// ==========================================

function updateChatBadge(count) {
  const badge = document.getElementById('chatBadge');

  if (!badge) {
    return;
  }

  badge.innerText = count;

  if (count > 0) {
    badge.style.display = 'inline-block';
  } else {
    badge.style.display = 'none';
  }
}

// Load badge when page opens

loadUnreadCount();

// ==========================================
// REAL TIME NOTIFICATION UPDATE
// ==========================================

socket.on('new_notification', function (data) {
  console.log('New notification:', data);

  updateChatBadge(data.count);
});

socket.on('notification_clear', function () {
  updateChatBadge(0);
});

// ==========================================
// LOAD DROPDOWN MESSAGES
// ==========================================

async function loadUnreadMessages() {
  try {
    const response = await fetch('/chat/unread-messages');

    const messages = await response.json();

    const list = document.getElementById('chatNotificationList');

    const header = document.getElementById('chatNotificationHeader');

    if (!list) {
      console.error('chatNotificationList missing');

      return;
    }

    list.innerHTML = '';

    if (header) {
      header.innerText = `${messages.length} New Messages`;
    }

    if (messages.length === 0) {
      list.innerHTML = `
            <div class="p-3 text-muted">
                No new messages
            </div>
            `;
      return;
    }

    messages.forEach(function (message) {
      list.innerHTML += `

            <a href="#"
               class="list-group-item chat-notification-item"
               data-conversation="${message.conversation_id}">

                <div class="row g-0 align-items-center">

                    <div class="col-2">

                        <i
                        class="text-primary"
                        data-feather="message-circle">
                        </i>

                    </div>

                    <div class="col-10">

                        <div class="text-dark">
                            ${message.sender}
                        </div>

                        <div class="text-muted small">
                            ${message.body}
                        </div>

                        <div class="text-muted small mt-1">
                            ${message.time}
                        </div>

                    </div>
                </div>
            </a>
            `;
    });

    if (window.feather) {
      feather.replace();
    }
  } catch (error) {
    console.error('Unread messages error:', error);
  }
}

// ==========================================
// LOAD DROPDOWN WHEN ICON CLICKED
// ==========================================

const alertsDropdown = document.getElementById('alertsDropdown');

if (alertsDropdown) {
  alertsDropdown.addEventListener('click', function () {
    loadUnreadMessages();
  });
}

// ==========================================
// OPEN CHAT FROM DROPDOWN
// ==========================================

document.addEventListener('click', function (e) {
  const item = e.target.closest('.chat-notification-item');

  if (!item) {
    return;
  }

  e.preventDefault();

  const conversationId = item.dataset.conversation;

  console.log('Notification chat:', conversationId);

  if (typeof openChat === 'function') {
    openChat(conversationId);
  } else {
    console.error('openChat() is not available');
  }
});
