(function(){
  let currentPage = 1;
  let isLoading = false;

  window.loadNotifications = function(page) {
    if (isLoading) return;
    isLoading = true;
    if (page === 1) {
      document.getElementById('notif-list').innerHTML = '';
      document.getElementById('notif-list').classList.add('hidden');
      document.getElementById('notif-loading').classList.remove('hidden');
      document.getElementById('notif-empty').classList.add('hidden');
      document.getElementById('notif-more-wrap').classList.add('hidden');
    }
    fetch('/api/notifications/?page=' + page)
      .then(r => r.json())
      .then(data => {
        isLoading = false;
        document.getElementById('notif-loading').classList.add('hidden');
        const list = document.getElementById('notif-list');
        if (data.notifications.length === 0 && page === 1) {
          document.getElementById('notif-empty').classList.remove('hidden');
          return;
        }
        list.classList.remove('hidden');
        data.notifications.forEach(n => {
          const div = document.createElement('div');
          div.className = 'px-4 py-3 text-sm hover:bg-[#F4F3EA] transition-colors ' +
            (n.is_read ? 'opacity-70' : 'bg-white');
          div.innerHTML = `
            <div class="flex items-start gap-2">
              <span class="mt-0.5 w-2 h-2 rounded-full flex-shrink-0 ${n.is_read ? 'bg-transparent' : 'bg-[#D3AC2B]'}"></span>
              <div class="flex-1 min-w-0">
                <p class="font-medium text-[#333D51] truncate">${n.title}</p>
                <p class="text-[#687080] mt-0.5 leading-snug">${n.message}</p>
                <span class="text-xs text-[#aab0bc] mt-1 block">${n.created_at}</span>
              </div>
            </div>`;
          list.appendChild(div);
        });
        currentPage = data.page;
        document.getElementById('notif-more-wrap').classList.toggle('hidden', !data.has_more);
      })
      .catch(() => { isLoading = false; });
  };

  window.loadMoreNotifications = function() {
    loadNotifications(currentPage + 1);
  };
})();
