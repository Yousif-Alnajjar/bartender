// Poll interval (milliseconds)
const POLL_INTERVAL = 2000;

// Start polling when page loads
document.addEventListener('DOMContentLoaded', function() {
    updateStatus();
    setInterval(updateStatus, POLL_INTERVAL);
});

/**
 * Fetch current system status and update UI
 */
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        // Update pour status
        if (data.pouring && data.current_drink) {
            document.getElementById('pour-status').classList.remove('hidden');
            document.getElementById('current-drink').textContent = data.current_drink;
            disableAllButtons();
        } else {
            document.getElementById('pour-status').classList.add('hidden');
            enableAllButtons();
        }

        // Update refill status
        const refillingReservoirs = [];
        for (let i = 1; i <= 4; i++) {
            if (data.refilling[i]) {
                refillingReservoirs.push(`Reservoir ${i}`);
            }
        }

        if (refillingReservoirs.length > 0) {
            document.getElementById('refill-status').classList.remove('hidden');
            document.getElementById('refill-reservoirs').textContent = refillingReservoirs.join(', ');
        } else {
            document.getElementById('refill-status').classList.add('hidden');
        }

    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

/**
 * Order a drink
 */
async function pourDrink(drinkName) {
    try {
        const response = await fetch(`/api/pour/${encodeURIComponent(drinkName)}`, {
            method: 'POST'
        });

        if (response.ok) {
            console.log(`Ordered: ${drinkName}`);
            // Status polling will update UI automatically
        } else {
            const error = await response.json();
            alert(`Error: ${error.error}`);
        }

    } catch (error) {
        console.error('Error ordering drink:', error);
        alert('Failed to order drink. Please try again.');
    }
}

/**
 * Disable all drink buttons
 */
function disableAllButtons() {
    const buttons = document.querySelectorAll('.drink-btn');
    buttons.forEach(button => {
        button.disabled = true;
    });
}

/**
 * Enable all drink buttons
 */
function enableAllButtons() {
    const buttons = document.querySelectorAll('.drink-btn');
    buttons.forEach(button => {
        button.disabled = false;
    });
}
