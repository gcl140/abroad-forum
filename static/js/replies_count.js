(function () {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${protocol}://${location.host}/ws/replies-counts/`;

  function connect() {
    const ws = new WebSocket(url);

    ws.onmessage = function (e) {
      const data = JSON.parse(e.data);
      document.querySelectorAll(`.replies-count[data-post-id="${data.post_id}"]`)
        .forEach(el => { el.textContent = data.count; });
    };

    ws.onclose = function () {
      // Reconnect after 3 seconds if connection drops
      setTimeout(connect, 3000);
    };
  }

  connect();
})();
