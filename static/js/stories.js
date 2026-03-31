document.addEventListener('DOMContentLoaded', function () {
  const grid = document.getElementById('stories-grid');
  const emptyState = document.getElementById('stories-empty');
  const tagButtons = document.querySelectorAll('[data-tag-btn]');
  let activeTag = new URLSearchParams(window.location.search).get('tag') || '';

  tagButtons.forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const tag = this.dataset.tag;
      if (tag === activeTag) return;
      fetchStories(tag);
    });
  });

  function fetchStories(tag) {
    setLoading(true);

    const url = '/api/stories/filter/' + (tag ? '?tag=' + encodeURIComponent(tag) : '');

    fetch(url)
      .then(res => res.json())
      .then(data => {
        activeTag = data.tag;
        updateTagButtons(activeTag);
        renderStories(data.stories);
        const newUrl = '/stories/' + (activeTag ? '?tag=' + activeTag : '');
        history.pushState({ tag: activeTag }, '', newUrl);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  function updateTagButtons(tag) {
    tagButtons.forEach(btn => {
      const isActive = btn.dataset.tag === tag;
      btn.classList.toggle('bg-maroon', isActive);
      btn.classList.toggle('text-white', isActive);
      btn.classList.toggle('border-maroon', isActive);
      btn.classList.toggle('bg-gray-800', !isActive);
      btn.classList.toggle('text-gray-300', !isActive);
      btn.classList.toggle('border-gray-700', !isActive);
      btn.classList.toggle('hover:border-maroon', !isActive);
    });
  }

  function renderStories(stories) {
    if (!stories.length) {
      grid.innerHTML = '';
      grid.classList.add('hidden');
      emptyState.classList.remove('hidden');
      return;
    }

    emptyState.classList.add('hidden');
    grid.classList.remove('hidden');
    grid.innerHTML = stories.map(story => {
      const coverHtml = story.cover_image
        ? `<div class="h-40 overflow-hidden">
             <img src="${story.cover_image}" alt="${escHtml(story.title)}"
                  class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
           </div>`
        : '';

      const avatarHtml = story.author_profile_picture
        ? `<img src="${story.author_profile_picture}" class="w-full h-full rounded-full object-cover">`
        : `<i class="fas fa-user" style="font-size:8px;"></i>`;

      return `
        <a href="/stories/${story.id}/"
           class="block bg-dark border border-gray-800 rounded-xl overflow-hidden hover:border-maroon transition group">
          ${coverHtml}
          <div class="p-4">
            <div class="flex items-center gap-2 mb-2">
              <span class="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-maroon border border-maroon/30">
                ${escHtml(story.tag_display)}
              </span>
              <span class="text-gray-500 text-xs">${timesince(story.created_at)} ago</span>
            </div>
            <h3 class="text-lg font-bold text-white group-hover:text-maroon transition">${escHtml(story.title)}</h3>
            <p class="text-gray-400 text-sm mt-1 line-clamp-2">${escHtml(story.summary)}</p>
            <div class="mt-3 flex items-center justify-between text-xs text-gray-500">
              <div class="flex items-center gap-2">
                <div class="w-5 h-5 rounded-full bg-maroon text-white flex items-center justify-center text-xs">
                  ${avatarHtml}
                </div>
                <span>${escHtml(story.author_nickname)}</span>
              </div>
              <span><i class="fas fa-eye mr-1"></i>${story.views}</span>
            </div>
          </div>
        </a>`;
    }).join('');
  }

  function setLoading(on) {
    grid.style.opacity = on ? '0.4' : '1';
    grid.style.pointerEvents = on ? 'none' : '';
  }

  function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
  }

  function timesince(isoString) {
    const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
    if (diff < 60) return diff + ' second' + (diff !== 1 ? 's' : '');
    const m = Math.floor(diff / 60);
    if (m < 60) return m + ' minute' + (m !== 1 ? 's' : '');
    const h = Math.floor(m / 60);
    if (h < 24) return h + ' hour' + (h !== 1 ? 's' : '');
    const days = Math.floor(h / 24);
    if (days < 30) return days + ' day' + (days !== 1 ? 's' : '');
    const months = Math.floor(days / 30);
    if (months < 12) return months + ' month' + (months !== 1 ? 's' : '');
    const years = Math.floor(months / 12);
    return years + ' year' + (years !== 1 ? 's' : '');
  }

  // Handle browser back/forward
  window.addEventListener('popstate', function (e) {
    const tag = (e.state && e.state.tag) || '';
    fetchStories(tag);
  });
});
