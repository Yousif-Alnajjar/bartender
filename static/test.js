// Test page control logic

let pourActive = false;
let refillActive = false;

/**
 * Toggle pour operation
 */
async function togglePour() {
    const btn = document.getElementById('pour-btn');

    if (pourActive) {
        // Stop pour
        await fetch('/api/test/valve/stop', { method: 'POST' });
        pourActive = false;
        btn.classList.remove('active');
        btn.querySelector('.btn-text').textContent = 'Pour';
    } else {
        // Start pour
        await fetch('/api/test/valve/start', { method: 'POST' });
        pourActive = true;
        btn.classList.add('active');
        btn.querySelector('.btn-text').textContent = 'Stop Pour';
    }
}

/**
 * Toggle refill operation
 */
async function toggleRefill() {
    const btn = document.getElementById('refill-btn');

    if (refillActive) {
        // Stop refill
        await fetch('/api/test/pump/stop', { method: 'POST' });
        refillActive = false;
        btn.classList.remove('active');
        btn.querySelector('.btn-text').textContent = 'Refill';
    } else {
        // Start refill
        await fetch('/api/test/pump/start', { method: 'POST' });
        refillActive = true;
        btn.classList.add('active');
        btn.querySelector('.btn-text').textContent = 'Stop Refill';
    }
}

/**
 * Go back to main page
 */
function goHome() {
    window.location.href = '/';
}

// Poll status to sync button states
setInterval(async () => {
    try {
        const response = await fetch('/api/test/status');
        const data = await response.json();

        const pourBtn = document.getElementById('pour-btn');
        const refillBtn = document.getElementById('refill-btn');

        // Update pour button
        if (data.valve_active !== pourActive) {
            pourActive = data.valve_active;
            if (pourActive) {
                pourBtn.classList.add('active');
                pourBtn.querySelector('.btn-text').textContent = 'Stop Pour';
            } else {
                pourBtn.classList.remove('active');
                pourBtn.querySelector('.btn-text').textContent = 'Pour';
            }
        }

        // Update refill button
        if (data.pump_active !== refillActive) {
            refillActive = data.pump_active;
            if (refillActive) {
                refillBtn.classList.add('active');
                refillBtn.querySelector('.btn-text').textContent = 'Stop Refill';
            } else {
                refillBtn.classList.remove('active');
                refillBtn.querySelector('.btn-text').textContent = 'Refill';
            }
        }
    } catch (error) {
        console.error('Error fetching test status:', error);
    }
}, 1000);
