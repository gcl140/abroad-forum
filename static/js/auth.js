// Password visibility toggle
function togglePw(id) {
    const input = document.getElementById(id);
    const icon = document.getElementById('eye-' + id);
    if (!input) return;
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// Mobile menu toggle
document.querySelector('[aria-controls="mobile-menu"]').addEventListener("click", function () {
    document.getElementById("mobile-menu").classList.toggle("hidden");
});

// Auto-dismiss toasts after 6 seconds
document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
        document.querySelectorAll(".fixed.top-4.right-4 .overflow-hidden").forEach(function (el) {
            el.remove();
        });
    }, 6000);
});
