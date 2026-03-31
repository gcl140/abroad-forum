// Profile Picture Preview
document.getElementById('profile-picture-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            const preview = document.getElementById('profile-picture-preview');
            if (preview.tagName === 'IMG') {
                preview.src = event.target.result;
            } else {
                const newImg = document.createElement('img');
                newImg.id = 'profile-picture-preview';
                newImg.className = 'w-32 h-32 rounded-full object-cover border-4 border-gray-700 shadow-lg';
                newImg.src = event.target.result;
                preview.parentNode.replaceChild(newImg, preview);
            }
        }
        reader.readAsDataURL(file);
    }
});

// Modal Functions
function openModal() {
    const modal = document.getElementById('profile-modal');
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    const modal = document.getElementById('profile-modal');
    modal.classList.add('hidden');
    window.history.back(); // Reload to reflect changes
    document.body.style.overflow = 'auto';
}

// Prevent modal close when clicking inside modal content
document.querySelector('.modal-content') && document.querySelector('.modal-content').addEventListener('click', function(e) {
    e.stopPropagation();
});

// University autocomplete
(function () {
    const search = document.getElementById('uni-search');
    const hidden = document.getElementById('uni-hidden');
    const dropdown = document.getElementById('uni-dropdown');
    if (!search) return;

    // Keep hidden input in sync with initial display value
    if (!hidden.value && search.value) hidden.value = search.value;

    let debounce;

    search.addEventListener('input', function () {
        const q = this.value.trim();
        hidden.value = q; // allow free-text too
        clearTimeout(debounce);
        if (q.length < 2) { dropdown.classList.add('hidden'); return; }

        debounce = setTimeout(() => {
            fetch('http://universities.hipolabs.com/search?name=' + encodeURIComponent(q))
                .then(r => r.json())
                .then(data => {
                    dropdown.innerHTML = '';
                    if (!data.length) { dropdown.classList.add('hidden'); return; }
                    data.slice(0, 10).forEach(uni => {
                        const li = document.createElement('li');
                        li.textContent = uni.name + (uni.country ? ' — ' + uni.country : '');
                        li.className = 'px-4 py-2 text-sm text-gray-200 hover:bg-gray-700 cursor-pointer';
                        li.addEventListener('mousedown', () => {
                            search.value = uni.name;
                            hidden.value = uni.name;
                            dropdown.classList.add('hidden');
                        });
                        dropdown.appendChild(li);
                    });
                    dropdown.classList.remove('hidden');
                })
                .catch(() => dropdown.classList.add('hidden'));
        }, 300);
    });

    search.addEventListener('blur', () => setTimeout(() => dropdown.classList.add('hidden'), 150));
    search.addEventListener('focus', () => { if (dropdown.children.length) dropdown.classList.remove('hidden'); });
})();
