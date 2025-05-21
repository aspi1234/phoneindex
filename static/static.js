document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuButton = document.querySelector('[aria-controls="mobile-menu"]');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuOpenIcon = mobileMenuButton.querySelector('.block');
    const menuCloseIcon = mobileMenuButton.querySelector('.hidden');

    mobileMenuButton.addEventListener('click', () => {
        const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
        mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
        mobileMenu.classList.toggle('hidden');
        menuOpenIcon.classList.toggle('hidden');
        menuCloseIcon.classList.toggle('hidden');
    });

    // Profile dropdown toggle
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = userMenuButton.parentElement.querySelector('[role="menu"]');

    userMenuButton.addEventListener('click', () => {
        const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
        userMenuButton.setAttribute('aria-expanded', !isExpanded);
        userMenu.classList.toggle('hidden');
        
        if (!userMenu.classList.contains('hidden')) {
            userMenu.classList.remove('opacity-0', 'scale-95');
            userMenu.classList.add('opacity-100', 'scale-100');
        } else {
            userMenu.classList.add('opacity-0', 'scale-95');
            userMenu.classList.remove('opacity-100', 'scale-100');
        }
    });

    // Close menus when clicking outside
    document.addEventListener('click', (event) => {
        if (!mobileMenuButton.contains(event.target) && !mobileMenu.contains(event.target)) {
            mobileMenu.classList.add('hidden');
            menuOpenIcon.classList.remove('hidden');
            menuCloseIcon.classList.add('hidden');
            mobileMenuButton.setAttribute('aria-expanded', 'false');
        }
        
        if (!userMenuButton.contains(event.target) && !userMenu.contains(event.target)) {
            userMenu.classList.add('hidden', 'opacity-0', 'scale-95');
            userMenu.classList.remove('opacity-100', 'scale-100');
            userMenuButton.setAttribute('aria-expanded', 'false');
        }
    });
});