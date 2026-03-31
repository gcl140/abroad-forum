(function () {
  const list = document.getElementById('activity-list');
  if (!list) return;

  const userId = list.dataset.userId;
  const loading = document.getElementById('activity-loading');
  const empty = document.getElementById('activity-empty');

  const colorMap = { blue: 'border-blue-500', green: 'border-green-500', yellow: 'border-yellow-500' };
  const iconMap  = { post: 'fa-question-circle', reply: 'fa-reply', rtr: 'fa-comments' };

  fetch('/api/activity/' + userId + '/')
    .then(r => r.json())
    .then(data => {
      loading.classList.add('hidden');
      if (!data.activity.length) {
        empty.classList.remove('hidden');
        return;
      }
      list.classList.remove('hidden');
      data.activity.forEach(item => {
        const border = colorMap[item.color] || 'border-gray-500';
        const icon   = iconMap[item.type]  || 'fa-circle';
        const titleHtml = item.url && item.title
          ? `<a href="${item.url}" class="font-medium text-white hover:underline text-sm block truncate">${item.title}</a>`
          : '';
        const div = document.createElement('div');
        div.className = 'border-l-4 ' + border + ' pl-3 py-2 rounded-r';
        div.innerHTML =
          '<div class="flex justify-between items-center text-xs text-gray-400 mb-1">' +
            '<span><i class="fas ' + icon + ' mr-1"></i>' + item.label + '</span>' +
            '<span class="italic">' + item.time + '</span>' +
          '</div>' +
          titleHtml +
          '<p class="text-xs text-gray-400 mt-0.5">' + item.snippet + '</p>';
        list.appendChild(div);
      });
    })
    .catch(() => {
      loading.classList.add('hidden');
      empty.classList.remove('hidden');
    });
})();
