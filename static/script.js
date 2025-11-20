function orderDrink(drinkName) {
    const statusEl = document.getElementById('status-message');
    const body = document.body;

    if (body.classList.contains('pouring')) {
        return;
    }

    statusEl.textContent = `Preparing ${drinkName}...`;
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
            statusEl.textContent = `Pouring ${drinkName}... (approx ${data.duration}s)`;
            
            // Wait for the duration plus a little buffer, or poll for status?
            // For this prototype, we'll just reset after the known duration.
            setTimeout(() => {
                statusEl.textContent = 'Drink ready! Enjoy.';
                body.classList.remove('pouring');
                setTimeout(() => {
                    statusEl.textContent = 'Ready to serve';
                }, 3000);
            }, data.duration * 1000);
        } else if (data.status === 'busy') {
            statusEl.textContent = 'System is busy. Please wait.';
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

