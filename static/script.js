function orderDrink(drinkName) {
    const statusEl = document.getElementById('status-message');
    const body = document.body;
    const progressContainer = document.getElementById('progress-bar-container');
    const progressBar = document.getElementById('progress-bar');

    if (body.classList.contains('pouring')) {
        return;
    }

    statusEl.textContent = `Starting ${drinkName}...`;
    body.classList.add('pouring');

    fetch('/pour', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ drink: drinkName }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            startProgress(data.duration, drinkName);
        } else if (data.status === 'busy') {
            statusEl.textContent = 'System Busy';
            setTimeout(() => {
                body.classList.remove('pouring');
                statusEl.textContent = 'Ready to serve';
            }, 2000);
        } else {
            statusEl.textContent = 'Error: ' + data.message;
            body.classList.remove('pouring');
        }
    })
    .catch((error) => {
        console.error('Error:', error);
        statusEl.textContent = 'Connection error';
        body.classList.remove('pouring');
    });
}

function startProgress(duration, drinkName) {
    const statusEl = document.getElementById('status-message');
    const progressContainer = document.getElementById('progress-bar-container');
    const progressBar = document.getElementById('progress-bar');
    const body = document.body;
    
    statusEl.textContent = `Pouring ${drinkName}...`;
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    
    const startTime = Date.now();
    const endTime = startTime + (duration * 1000);
    
    const interval = setInterval(() => {
        const now = Date.now();
        const remaining = endTime - now;
        const percentage = Math.min(100, 100 - (remaining / (duration * 1000) * 100));
        
        progressBar.style.width = `${percentage}%`;
        
        if (now >= endTime) {
            clearInterval(interval);
            progressBar.style.width = '100%';
            statusEl.textContent = 'Enjoy your drink!';
            
            setTimeout(() => {
                body.classList.remove('pouring');
                progressContainer.style.display = 'none';
                statusEl.textContent = 'Ready to serve';
                progressBar.style.width = '0%';
            }, 2000);
        }
    }, 50); // Update every 50ms for smooth animation
}
