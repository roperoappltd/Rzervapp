// ==========================================
// GLOBAL SOCKET.IO CONNECTION
// ==========================================
//
// This file is loaded once from base.html.
//
// All other files use this same socket:
// - notification.js
// - chat-open-close.js
// - chat-socket.js
// - chat-send.js
//
// Do NOT create another io() connection
// in those files.
//

const socket = io();

// ==========================================
// CONNECTION STATUS (optional debugging)
// ==========================================

socket.on('connect', function () {
  console.log('Socket.IO connected:', socket.id);
});

socket.on('disconnect', function () {
  console.log('Socket.IO disconnected');
});
