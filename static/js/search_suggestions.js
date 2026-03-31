(function () {
    const input = document.getElementById('desktop-search-input');
    const dropdown = document.getElementById('search-suggestions');
    if (!input || !dropdown) return;

    let debounceTimer = null;
    let activeIndex = -1;
    let currentResults = [];

    function show() { dropdown.classList.remove('hidden'); }
    function hide() { dropdown.classList.add('hidden'); activeIndex = -1; }

    const isLight = () => document.documentElement.getAttribute('data-theme') === 'light';

    function getColors() {
        return isLight()
            ? { bg: '#ffffff', hover: '#f0ede5', border: '#e0dbd0', text: '#1E2B3C', sub: '#687080', kbd: '#e0dbd0' }
            : { bg: '#111827', hover: '#1f2937', border: '#374151', text: '#f3f4f6', sub: '#9ca3af', kbd: '#374151' };
    }

    function render(results) {
        currentResults = results;
        activeIndex = -1;
        if (!results.length) { hide(); return; }

        const c = getColors();
        dropdown.style.cssText = `background:${c.bg};border-color:${c.border};`;

        const iconColor = { tag: '#800000', post: '#60a5fa', reply: '#34d399' };

        dropdown.innerHTML = results.map((r, i) => `
            <a href="${r.url}"
               data-index="${i}"
               class="suggestion-item"
               style="display:flex;align-items:center;gap:12px;padding:10px 16px;text-decoration:none;border-bottom:1px solid ${c.border};transition:background 0.15s;">
                <i class="fas ${r.type === 'tag' ? 'fa-hashtag' : r.type === 'reply' ? 'fa-reply' : 'fa-file-alt'}"
                   style="color:${iconColor[r.type] || iconColor.post};width:16px;text-align:center;flex-shrink:0;font-size:12px;"></i>
                <div style="min-width:0;">
                    <div style="color:${c.text};font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${r.label}</div>
                    ${r.sublabel ? `<div style="color:${c.sub};font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${r.sublabel}</div>` : ''}
                </div>
            </a>`).join('') +
            `<div style="padding:6px 16px;font-size:11px;color:${c.sub};text-align:right;">
                Press <kbd style="background:${c.kbd};color:${c.text};padding:1px 5px;border-radius:4px;font-size:10px;">Enter</kbd> for full results
            </div>`;

        // hover effect via JS since inline styles can't use :hover
        dropdown.querySelectorAll('.suggestion-item').forEach(el => {
            el.addEventListener('mouseenter', () => el.style.background = getColors().hover);
            el.addEventListener('mouseleave', () => {
                const idx = parseInt(el.dataset.index);
                el.style.background = idx === activeIndex ? getColors().hover : '';
            });
        });

        show();
    }

    function fetchSuggestions(q) {
        fetch(`/api/search-suggestions/?q=${encodeURIComponent(q)}`)
            .then(r => r.json())
            .then(data => render(data.results))
            .catch(() => hide());
    }

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        const q = input.value.trim();
        if (q.length < 2) { hide(); return; }
        debounceTimer = setTimeout(() => fetchSuggestions(q), 250);
    });

    // Keyboard nav
    input.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.suggestion-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, items.length - 1);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, -1);
        } else if (e.key === 'Escape') {
            hide(); return;
        } else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            items[activeIndex].click();
            return;
        } else {
            return;
        }

        items.forEach((el, i) => {
            el.classList.toggle('bg-gray-800', i === activeIndex);
        });

        if (activeIndex >= 0) {
            input.value = currentResults[activeIndex].label.replace(/^#/, '');
        }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) hide();
    });

    // Reopen on focus if there's already a value
    input.addEventListener('focus', () => {
        if (input.value.trim().length >= 2 && currentResults.length) show();
    });
})();
