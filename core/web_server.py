import asyncio
import json
import time
from pathlib import Path
from aiohttp import web

class WebOverlayServer:
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.clients = set()
        
        self.web_root = Path(__file__).parent.parent / 'web'
        
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/ws', self.handle_websocket)
        self.app.router.add_get('/proxy/image', self.handle_proxy_image)
        self.app.router.add_static('/assets/', self.web_root)

    async def handle_index(self, request):
        index_path = self.web_root / 'templates' / 'index.html'
        return web.FileResponse(index_path)

    async def handle_proxy_image(self, request):
        import aiohttp
        url = request.query.get('url')
        if not url:
            return web.Response(status=400)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'Referer': 'https://live.bilibili.com/'}) as resp:
                data = await resp.read()
                return web.Response(body=data, content_type=resp.content_type)

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.clients.add(ws)
        try:
            async for msg in ws:
                pass
        finally:
            self.clients.remove(ws)
        return ws

    async def broadcast(self, data):
        msg_type = data.get('type', 'chat')
        if msg_type in ('danmaku', 'chat'):
            msg_type = 'chat'
            
        user_name = data.get('user') or data.get('uname') or data.get('userName') or '匿名用户'
        content = data.get('text') or data.get('content') or ''
        
        if msg_type == 'gift':
            content = f"赠送了 {data.get('num', 1)} 个 {data.get('gift_name', '礼物')}"
        elif msg_type == 'guard':
            content = f"成为了 {data.get('unit', '舰长')}"
        elif msg_type == 'enter':
            content = "进入了直播间"

        formatted = {
            "userName": user_name,
            "platform": "bilibili",
            "avatar": data.get('avatar', ''),
            "content": content,
            "timestamp": int(time.time() * 1000),
            "type": msg_type
        }
        
        if data.get('price'):
            try:
                formatted['price'] = float(data.get('price'))
            except Exception:
                pass
            
        message = json.dumps(formatted)
        for ws in list(self.clients):
            try:
                await ws.send_str(message)
            except Exception:
                pass

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        for _ in range(100):
            try:
                site = web.TCPSite(self.runner, self.host, self.port)
                await site.start()
                break
            except OSError:
                self.port += 1
                
        print(f"[WebServer] 悬浮窗 Web 页面运行在 http://{self.host}:{self.port}")
        return self.port

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
