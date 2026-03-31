// Reveal on scroll
(function () {
    const obs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('in-view');
        });
    }, { threshold: 0.12 });
    document.querySelectorAll('[data-animate]').forEach(el => obs.observe(el));
})();

// Mobile menu
const menuToggle = document.getElementById('menuToggle');
const menuClose  = document.getElementById('menuClose');
const mobileMenu = document.getElementById('mobileMenu');
const overlay    = document.getElementById('overlay');

function openMenu() {
    mobileMenu.classList.add('open');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeMenu() {
    mobileMenu.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
}

if (menuToggle && mobileMenu && overlay) {
    menuToggle.addEventListener('click', openMenu);
    if (menuClose) menuClose.addEventListener('click', closeMenu);
    overlay.addEventListener('click', closeMenu);
    document.querySelectorAll('.mobile-menu a').forEach(link => {
        link.addEventListener('click', closeMenu);
    });
}

// Smooth scroll for in-page anchors
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
        const href = a.getAttribute('href');
        if (href === '#') return;
        const target = document.querySelector(href);
        if (target) {
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Gold button press animation
document.querySelectorAll('.gold-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.animate(
            [{ transform: 'scale(1)' }, { transform: 'scale(.96)' }, { transform: 'scale(1)' }],
            { duration: 180 }
        );
    });
});

// Progressive image reveal
document.querySelectorAll('img').forEach(img => {
    img.style.opacity = '0';
    img.style.transform = 'translateY(6px)';
    img.style.transition = 'all 700ms cubic-bezier(.2,.9,.2,1)';
    if (img.complete) revealImg(img);
    else img.onload = () => revealImg(img);
});
function revealImg(i) {
    setTimeout(() => { i.style.opacity = '1'; i.style.transform = 'translateY(0)'; }, 120);
}

// Load stats from API
(function loadStats() {
    fetch('/api/stats/')
        .then(res => res.json())
        .then(data => {
            const usersEl = document.getElementById('stat-users');
            const postsEl = document.getElementById('stat-posts');
            if (usersEl && data.users != null) usersEl.textContent = data.users + '+';
            if (postsEl && data.posts != null) postsEl.textContent = data.posts + '+';
        })
        .catch(() => {
            // Fail silently; placeholders remain
        });
})();
