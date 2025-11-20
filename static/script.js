function selectDrink(drinkId, drinkName) {
    // Show overlay immediately
    const overlay = document.getElementById('overlay');
    const modalTitle = document.getElementById('modal-title');
    const statusIndicator = document.getElementById('status-indicator');
    
    overlay.classList.remove('hidden');
    modalTitle.textContent = `Pouring ${drinkName}`;
    statusIndicator.textContent = 'Busy';
    statusIndicator.classList.add('busy');
    statusIndicator.classList.remove('ready');

    // Start visual progress bar locally since we know it takes 30s
    startProgress();

    // Trigger blocking request
    fetch('/pour', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ drink_id: drinkId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Backend returned, meaning pour is done.
            finishProgress();
        } else {
            alert(data.message);
            resetUI();
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('Failed to communicate with bartender.');
        resetUI();
    });
}

function startProgress() {
    const fill = document.querySelector('.progress-fill');
    let width = 0;
    // The hardware takes roughly 30 seconds + small buffers
    const duration = 31000; 
    const intervalTime = 100;
    const step = 100 / (duration / intervalTime);

    window.pourInterval = setInterval(() => {
        width += step;
        if (width >= 95) {
            // Stall at 95% until server confirms completion
            width = 95;
        }
        fill.style.width = width + '%';
    }, intervalTime);
}

function finishProgress() {
    if (window.pourInterval) clearInterval(window.pourInterval);
    
    document.querySelector('.progress-fill').style.width = '100%';
    setTimeout(() => {
        resetUI();
    }, 1000);
}

function resetUI() {
    if (window.pourInterval) clearInterval(window.pourInterval);
    
    const overlay = document.getElementById('overlay');
    const statusIndicator = document.getElementById('status-indicator');
    
    overlay.classList.add('hidden');
    document.querySelector('.progress-fill').style.width = '0%';
    
    statusIndicator.textContent = 'Ready';
    statusIndicator.classList.remove('busy');
    statusIndicator.classList.add('ready');
}
