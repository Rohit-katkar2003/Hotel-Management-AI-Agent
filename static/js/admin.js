// Grand Hotel Admin Dashboard
const API = "http://localhost:8000/api/v1";

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = item.getAttribute('href').substring(1);
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        document.getElementById(targetId).classList.add('active');
        if (targetId === 'overview') loadStats();
        if (targetId === 'bookings') refreshBookings();
        if (targetId === 'customers') refreshCustomers();
        if (targetId === 'rooms') refreshRooms();
    });
});

async function loadStats() {
    try {
        const response = await fetch(`${API}/stats`);
        if (!response.ok) throw new Error('Failed to fetch stats');
        const data = await response.json();
        document.getElementById('kpi-bookings').textContent = data.active_bookings || 0;
        document.getElementById('kpi-revenue').textContent = '$' + (data.total_revenue || 0).toFixed(2);
        document.getElementById('kpi-occupancy').textContent = (data.occupancy_rate || 0) + '%';
        document.getElementById('kpi-customers').textContent = data.customers || 0;
        updateCharts();
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateCharts() {
    const bookingsCtx = document.getElementById('bookings-chart');
    if (bookingsCtx) {
        new Chart(bookingsCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Bookings',
                    data: [3, 5, 2, 8, 4, 6, 3],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    const revenueCtx = document.getElementById('revenue-chart');
    if (revenueCtx) {
        new Chart(revenueCtx, {
            type: 'doughnut',
            data: {
                labels: ['Single', 'Double', 'Suite', 'Deluxe'],
                datasets: [{
                    data: [25, 35, 25, 15],
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }
}

// Bookings CRUD
async function refreshBookings() {
    const tbody = document.getElementById('bookings-table-body');
    tbody.innerHTML = '<tr><td colspan="8">Loading...</td></tr>';
    try {
        const response = await fetch(`${API}/bookings`);
        if (!response.ok) throw new Error('Failed to fetch');
        const bookings = await response.json();
        if (bookings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8">No bookings</td></tr>';
            return;
        }
        tbody.innerHTML = bookings.map(b => `
            <tr>
                <td>#${b.id}</td>
                <td>${b.customer_name || 'N/A'}</td>
                <td>${b.room_number || 'N/A'}</td>
                <td>${b.check_in}</td>
                <td>${b.check_out}</td>
                <td>$${b.total_amount.toFixed(2)}</td>
                <td><span class="status ${b.status}">${b.status.replace('_', ' ').toUpperCase()}</span></td>
                <td><button class="btn btn-secondary">View</button></td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="8">Error: ${e.message}</td></tr>`;
    }
}

async function refreshCustomers() {
    const tbody = document.getElementById('customers-table-body');
    tbody.innerHTML = '<tr><td colspan="5">Loading...</td></tr>';
    try {
        const response = await fetch(`${API}/customers`);
        if (!response.ok) throw new Error('Failed to fetch');
        const customers = await response.json();
        if (customers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No customers</td></tr>';
            return;
        }
        tbody.innerHTML = customers.map(c => `
            <tr>
                <td>#${c.id}</td>
                <td>${c.name}</td>
                <td>${c.email}</td>
                <td>${c.phone}</td>
                <td>-</td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5">Error: ${e.message}</td></tr>`;
    }
}

async function refreshRooms() {
    const container = document.getElementById('admin-rooms-container');
    container.innerHTML = '<div class="room-card"><p>Loading...</p></div>';
    try {
        const response = await fetch(`${API}/rooms`);
        if (!response.ok) throw new Error('Failed to fetch');
        const rooms = await response.json();
        if (rooms.length === 0) {
            container.innerHTML = '<div class="room-card"><p>No rooms</p></div>';
            return;
        }
        container.innerHTML = rooms.map(r => `
            <div class="room-card">
                <h4>Room ${r.room_number}</h4>
                <p>${r.room_type} • $${r.price_per_night}/night</p>
                <p>Capacity: ${r.capacity}</p>
                <p><span class="status ${r.status}">${r.status.toUpperCase()}</span></p>
            </div>
        `).join('');
    } catch (e) {
        container.innerHTML = `<div class="room-card"><p>Error: ${e.message}</p></div>`;
    }
}

function exportBookings() {
    alert('Exporting bookings to CSV...');
}

// Initialize dashboard
loadStats();