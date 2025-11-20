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
            startProgress();
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
    // The backend process takes roughly 30 seconds based on test.py
    const duration = 30000; 
    const intervalTime = 100;
    const step = 100 / (duration / intervalTime);

    const interval = setInterval(() => {
        width += step;
        if (width >= 100) {
            width = 100;
        }
        fill.style.width = width + '%';
        
        // Poll status to see if actually finished
        checkStatus(interval);
        
    }, intervalTime);
}

function checkStatus(progressInterval) {
    fetch('/status')
    .then(response => response.json())
    .then(data => {
        if (!data.is_pouring) {
            clearInterval(progressInterval);
            document.querySelector('.progress-fill').style.width = '100%';
            setTimeout(() => {
                resetUI();
            }, 1000);
        }
    });
}

function resetUI() {
    const overlay = document.getElementById('overlay');
    const statusIndicator = document.getElementById('status-indicator');
    
    overlay.classList.add('hidden');
    document.querySelector('.progress-fill').style.width = '0%';
    
    statusIndicator.textContent = 'Ready';
    statusIndicator.classList.remove('busy');
    statusIndicator.classList.add('ready');
}

