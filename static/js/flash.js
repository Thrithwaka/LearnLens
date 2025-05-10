// Add this script to the existing script section on your page
document.addEventListener('DOMContentLoaded', function() {
    // Contact form submission
    const contactForm = document.getElementById('contactForm');
    const formMessage = document.getElementById('formMessage');
    const alertBox = formMessage.querySelector('.alert');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(contactForm);
            
            // Show loading state
            const submitBtn = contactForm.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.textContent;
            submitBtn.textContent = 'Sending...';
            submitBtn.disabled = true;
            
            // Send form data
            fetch('/send_message', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Show success or error message
                if (data.status === 'success') {
                    alertBox.classList.add('alert-success');
                    alertBox.classList.remove('alert-danger');
                    contactForm.reset(); // Clear form
                } else {
                    alertBox.classList.add('alert-danger');
                    alertBox.classList.remove('alert-success');
                }
                
                alertBox.textContent = data.message;
                formMessage.style.display = 'block';
                
                // Reset button
                submitBtn.textContent = originalBtnText;
                submitBtn.disabled = false;
                
                // Hide message after 5 seconds
                setTimeout(() => {
                    formMessage.style.display = 'none';
                }, 5000);
            })
            .catch(error => {
                console.error('Error:', error);
                alertBox.classList.add('alert-danger');
                alertBox.classList.remove('alert-success');
                alertBox.textContent = 'An error occurred. Please try again later.';
                formMessage.style.display = 'block';
                
                // Reset button
                submitBtn.textContent = originalBtnText;
                submitBtn.disabled = false;
            });
        });
    }
});