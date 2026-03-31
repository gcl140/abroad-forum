// Toggle update section visibility
document.getElementById('updateButton').addEventListener('click', function() {
  const updateSection = document.getElementById('updateSection');
  updateSection.classList.toggle('hidden');

  // Scroll to form when shown
  if (!updateSection.classList.contains('hidden')) {
    updateSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
});

// Profile picture preview
document.getElementById('id_profile_picture').addEventListener('change', function(e) {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function(event) {
      document.getElementById('profileImagePreview').src = event.target.result;
    };
    reader.readAsDataURL(file);
  }
});

// Style form inputs
document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('input[type="text"],input[type="tel"], input[type="email"], input[type="file"]');
  inputs.forEach(input => {
    input.classList.add('w-full', 'border', 'border-gray-300', 'rounded-md', 'py-2', 'px-3',
                       'focus:outline-none', 'focus:ring-1', 'focus:ring-black', 'focus:border-transparent');
  });
});
