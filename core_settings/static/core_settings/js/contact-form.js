document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form elements
            const submitButton = contactForm.querySelector('button[type="submit"]');
            const formFields = contactForm.querySelectorAll('input, textarea, button');
            const originalButtonText = submitButton.innerHTML;
            const formContainer = contactForm.closest('.contact-form-wrapper');
            
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Sending...';
            
            // Disable all form fields during submission
            formFields.forEach(field => field.disabled = true);
            
            // Get form data
            const formData = {
                name: contactForm.querySelector('[name="name"]').value.trim(),
                email: contactForm.querySelector('[name="email"]').value.trim(),
                subject: contactForm.querySelector('[name="subject"]').value.trim(),
                message: contactForm.querySelector('[name="message"]').value.trim()
            };
            
            // Clear any previous messages
            const messageContainer = document.getElementById('form-message');
            if (messageContainer) {
                messageContainer.innerHTML = '';
                messageContainer.className = 'alert';
            }
            
            // Send the form data to the server
            fetch('/api/contact/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success animation
                    showSuccessAnimation(formContainer);
                    // Reset the form
                    contactForm.reset();
                } else {
                    throw new Error(data.message || 'An error occurred. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('error', error.message || 'An error occurred while sending your message. Please try again later.');
            })
            .finally(() => {
                // Re-enable form fields
                formFields.forEach(field => field.disabled = false);
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
            });
            
        // Function to show success animation
        function showSuccessAnimation(container) {
            // Hide the form
            contactForm.style.display = 'none';
            
            // Create success message element
            const successMessage = document.createElement('div');
            successMessage.className = 'text-center py-5 success-animation';
            successMessage.innerHTML = `
                <div class="success-checkmark">
                    <div class="check-icon">
                        <span class="icon-line line-tip"></span>
                        <span class="icon-line line-long"></span>
                        <div class="icon-circle"></div>
                        <div class="icon-fix"></div>
                    </div>
                </div>
                <h3 class="mt-4 text-success">Thank You!</h3>
                <p class="text-muted">Your message has been sent successfully. We'll get back to you soon!</p>
                <button id="send-another" class="btn btn-primary mt-3">
                    <i class="fas fa-paper-plane me-2"></i>Send Another Message
                </button>
            `;
            
            // Add the success message to the container
            container.appendChild(successMessage);
            
            // Add event listener for the "Send Another" button
            document.getElementById('send-another').addEventListener('click', function() {
                // Remove success message
                container.removeChild(successMessage);
                // Show the form again
                contactForm.style.display = 'block';
            });
        }
        });
    }
    
    function showMessage(type, message) {
        const messageContainer = document.getElementById('form-message');
        if (messageContainer) {
            // Remove any existing alert classes
            messageContainer.className = 'alert';
            
            // Set the message and add appropriate classes
            messageContainer.textContent = message;
            messageContainer.classList.add(`alert-${type}`, 'animate__animated', 'animate__fadeIn');
            messageContainer.style.display = 'block';
            
            // Scroll to the message
            messageContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            // Hide the message after 5 seconds with fade out animation
            setTimeout(() => {
                messageContainer.classList.remove('animate__fadeIn');
                messageContainer.classList.add('animate__fadeOut');
                
                // Remove the element after animation completes
                setTimeout(() => {
                    messageContainer.style.display = 'none';
                    messageContainer.className = 'alert d-none';
                    messageContainer.classList.remove('animate__fadeOut');
                }, 500);
            }, 5000);
        }
    }
    
    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
