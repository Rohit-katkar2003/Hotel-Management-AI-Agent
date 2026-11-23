const API = "/api/v1";
let adminThread = localStorage.getItem('admin_thread') ||
                  ('admin_' + Date.now() + '_' + Math.random().toString(36).slice(2,9));
localStorage.setItem('admin_thread', adminThread);

const form = document.getElementById('admin-chat-form');
const input = document.getElementById('admin-chat-input');
const box = document.getElementById('admin-chat-messages');

form?.addEventListener('submit', async e => {
  e.preventDefault();
  const text = input.value.trim(); if (!text) return;
  input.value = '';
  const u = document.createElement('div');
  u.className = 'chat-message user';
  u.innerHTML = `<div class="chat-avatar">👤</div><div class="chat-bubble">${text}</div>`;
  box.appendChild(u);
  const r = await fetch(`${API}/chat/admin`, {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ message: text, thread_id: adminThread })
  });
  const data = await r.json();
  const a = document.createElement('div');
  a.className = 'chat-message ai';
  a.innerHTML = `<div class="chat-avatar">🤖</div>`;
  const b = document.createElement('div'); b.className = 'chat-bubble';
  b.innerHTML = marked.parse(data.reply);
  a.appendChild(b); box.appendChild(a);
  box.scrollTop = box.scrollHeight;
});