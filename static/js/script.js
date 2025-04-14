document.addEventListener('DOMContentLoaded', function () {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    const navLinks = document.querySelector('.nav-links');

    hamburgerMenu.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });
});

document.querySelector('form').addEventListener('submit', function(event) {
    const password = document.querySelector('input[name="password"]').value;
    const confirmPassword = document.querySelector('input[name="confirm_password"]').value;

    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        event.preventDefault();
    }
});
