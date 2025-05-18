// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    const messageStatus = document.getElementById('messageStatus');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Clear previous status messages
            if (messageStatus) {
                messageStatus.innerHTML = '';
                messageStatus.className = '';
            }
            
            // Collect form data
            const formData = new FormData(contactForm);
            
            // Send the form data
            fetch('/send_message', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show success message
                    if (messageStatus) {
                        messageStatus.innerHTML = data.message;
                        messageStatus.className = 'success-message';
                    }
                    // Reset the form
                    contactForm.reset();
                } else {
                    // Show error message
                    if (messageStatus) {
                        messageStatus.innerHTML = data.message;
                        messageStatus.className = 'error-message';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Show generic error message
                if (messageStatus) {
                    messageStatus.innerHTML = 'Failed to send message. Please try again later.';
                    messageStatus.className = 'error-message';
                }
            });
        });
    }
});