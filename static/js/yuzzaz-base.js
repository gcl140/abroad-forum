// Automatically remove toast messages after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    const toastMessages = document.querySelectorAll('.toast-message');
    toastMessages.forEach(toast => {
        setTimeout(() => {
            toast.remove(); // Remove the toast message after 5 seconds
        }, 5000); // 5000 milliseconds = 5 seconds
    });
});
