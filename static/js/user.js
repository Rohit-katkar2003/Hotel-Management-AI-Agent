// static/js/user.js  (replaces chat.js)
const API = "/api/v1";
let threadId = localStorage.getItem('thread_id') ||
               ('thread_' + Date.now() + '_' + Math.random().toString(36).slice(2, 9));
localStorage.setItem('thread_id', threadId);

const chatMessages = document.getElementById('chat-messages');
const chatForm     = document.getElementById('chat-form');
const chatInput    = document.getElementById('chat-input');

function renderRooms(container, rooms) {
  if (!rooms?.length) return;
  const grid = document.createElement('div');
  grid.className = 'room-cards';
  grid.innerHTML = rooms.map(r => `
    <div class="room-card mini">
      <img src="${r.image}" alt="${r.type} room" loading="lazy">
      <div class="room-info">
        <h4>${r.type.toUpperCase()} · Room ${r.number}</h4>
        <p>$${r.price}/night · up to ${r.capacity} guest(s)</p>
        <button class="btn-book" data-room="${r.id}">Book this room</button>
      </div>
    </div>
  `).join('');
  container.appendChild(grid);

  grid.querySelectorAll('.btn-book').forEach(btn => {
    btn.addEventListener('click', () => {
      chatInput.value = `I'd like to book room ID ${btn.dataset.room}`;
      chatForm.dispatchEvent(new Event('submit'));
    });
  });
}

function addAiMessage(content, rooms = []) {
  const row = document.createElement('div');
  row.className = 'chat-message ai';
  row.innerHTML = `<div class="chat-avatar">🤖</div>`;
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';
  bubble.innerHTML = marked.parse(content || '');
  row.appendChild(bubble);
  chatMessages.appendChild(row);
  renderRooms(bubble, rooms);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener('submit', async e => {
  e.preventDefault();
  const text = chatInput.value.trim(); if (!text) return;
  chatInput.value = '';
  const userRow = document.createElement('div');
  userRow.className = 'chat-message user';
  userRow.innerHTML = `<div class="chat-avatar">👤</div><div class="chat-bubble">${text}</div>`;
  chatMessages.appendChild(userRow); chatMessages.scrollTop = chatMessages.scrollHeight;

  const loader = document.createElement('div');
  loader.className = 'chat-message ai'; loader.id = 'loading';
  loader.innerHTML = `<div class="chat-avatar">🤖</div><div class="chat-bubble"><span class="loading"></span></div>`;
  chatMessages.appendChild(loader);

  try {
    const r = await fetch(`${API}/chat/user`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: text, thread_id: threadId })
    });
    const data = await r.json();
    document.getElementById('loading')?.remove();
    addAiMessage(data.reply, data.rooms || []);
  } catch (err) {
    document.getElementById('loading')?.remove();
    addAiMessage(`⚠️ ${err.message}`);
  }
});