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

        const buttons = document.querySelectorAll('.drink-btn');

        // Update button states based on pouring status
        if (data.pouring && data.current_drink) {
            buttons.forEach(button => {
                const drinkName = button.getAttribute('data-drink');
                if (drinkName === data.current_drink) {
                    button.classList.add('pouring');
                    button.disabled = true;
                } else {
                    button.classList.remove('pouring');
                    button.disabled = true;
                }
            });
        } else {
            buttons.forEach(button => {
                button.classList.remove('pouring');
                button.disabled = false;
            });
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

