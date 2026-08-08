const container = document.getElementById('danmaku-container');

function connectWS() {
    const ws = new WebSocket(`ws://${location.host}/ws`);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            addDanmaku(data);
        } catch (e) {
            console.error("Parse error:", e);
        }
    };

    ws.onclose = () => {
        setTimeout(connectWS, 1500);
    };
}

function addDanmaku(data) {
    const item = document.createElement('div');
    item.className = `danmaku-item ${data.type || 'chat'}`;

    if (data.avatar) {
        const img = document.createElement('img');
        img.className = 'avatar';
        img.src = `/proxy/image?url=${encodeURIComponent(data.avatar)}`;
        item.appendChild(img);
    }

    const user = document.createElement('span');
    user.className = 'username';
    user.textContent = data.userName || '匿名用户';
    item.appendChild(user);

    const content = document.createElement('span');
    content.className = 'message-content';
    content.textContent = data.content || '';
    item.appendChild(content);

    container.appendChild(item);

    // Keep max 30 items
    while (container.children.length > 30) {
        container.removeChild(container.firstChild);
    }

    // Auto remove after 12s
    setTimeout(() => {
        if (item.parentNode) {
            item.style.opacity = '0';
            item.style.transition = 'opacity 0.5s ease';
            setTimeout(() => {
                if (item.parentNode) item.parentNode.removeChild(item);
            }, 500);
        }
    }, 12000);
}

connectWS();
