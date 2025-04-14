// main.js

// Close alert messages
document.addEventListener('DOMContentLoaded', function() {
    // Automatically close alert messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.display = 'none';
        });
    }, 5000);
});

// Mobile navigation toggle (for responsive design)
document.addEventListener('DOMContentLoaded', function() {
    // This is a placeholder for future mobile navigation toggle functionality
    // to be implemented when needed
});