import asyncio
import json
import struct
import zlib
import re
import aiohttp
from PySide6.QtCore import QObject, Signal, QThread

OP_HEARTBEAT = 2
OP_HEARTBEAT_REPLY = 3
OP_SEND_SMS_REPLY = 5
OP_AUTH = 7
OP_AUTH_REPLY = 8

class BilibiliWSClient(QObject):
    connected_signal = Signal(str)
    disconnected_signal = Signal(str)
    danmaku_signal = Signal(dict)
    gift_signal = Signal(dict)
    superchat_signal = Signal(dict)
    guard_signal = Signal(dict)
    interact_signal = Signal(dict)
    popularity_signal = Signal(int)

    def __init__(self, room_id=0, cookie="", parent=None):
        super().__init__(parent)
        try:
            self.room_id = int(room_id)
        except (ValueError, TypeError):
            self.room_id = 0
        self.real_room_id = self.room_id
        self.cookie = cookie.strip()
        self.user_uid = 0
        self.buvid = ""
        self.is_running = False
        self.session = None
        self.ws = None
        self.avatar_cache = {}

    async def get_room_info(self):
        assert self.session is not None
        # 1. If cookie provided, get login user info & buvid
        if self.cookie:
            try:
                nav_url = "https://api.bilibili.com/x/web-interface/nav"
                async with self.session.get(nav_url) as resp:
                    if resp.status == 200:
                        nav_data = await resp.json()
                        if nav_data.get("code") == 0:
                            self.user_uid = nav_data["data"].get("mid", 0)
            except Exception as e:
                print(f"[WS] Nav error: {e}")

        # 2. Get real room ID
        url = f"https://api.live.bilibili.com/room/v1/Room/room_init?id={self.room_id}"
        async with self.session.get(url) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                self.real_room_id = data["data"]["room_id"]
            else:
                self.real_room_id = self.room_id

        # 3. Get danmu server info & token (xlive API for authenticated stream)
        danmu_info_url = f"https://api.live.bilibili.com/xlive/web-room/v1/dM/getDanmuInfo?id={self.real_room_id}&type=0"
        try:
            async with self.session.get(danmu_info_url) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    host_list = data["data"]["host_list"]
                    token = data["data"]["token"]
                    return host_list[0]["host"], host_list[0]["wss_port"], token
        except Exception:
            pass

        # Fallback to v1 API
        fallback_url = f"https://api.live.bilibili.com/room/v1/Danmu/getConf?room_id={self.real_room_id}&platform=pc&player=web"
        async with self.session.get(fallback_url) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                host_list = data["data"]["host_server_list"]
                token = data["data"]["token"]
                return host_list[0]["host"], host_list[0]["wss_port"], token

        return "broadcastlv.chat.bilibili.com", 443, ""

    def make_packet(self, opcode, payload=""):
        if isinstance(payload, str):
            body = payload.encode("utf-8")
        else:
            body = payload
        packet_len = 16 + len(body)
        header = struct.pack(">IHHII", packet_len, 16, 1, opcode, 1)
        return header + body

    async def start_async(self):
        self.is_running = True
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": f"https://live.bilibili.com/{self.room_id}"
            }
            if self.cookie:
                headers["Cookie"] = self.cookie

            async with aiohttp.ClientSession(headers=headers) as session:
                self.session = session
                host, port, token = await self.get_room_info()
                ws_url = f"wss://{host}:{port}/sub"
                
                async with session.ws_connect(ws_url) as ws:
                    self.ws = ws
                    auth_body = json.dumps({
                        "uid": self.user_uid,
                        "roomid": self.real_room_id,
                        "protover": 3,
                        "platform": "web",
                        "type": 2,
                        "key": token
                    })
                    await ws.send_bytes(self.make_packet(OP_AUTH, auth_body))
                    self.connected_signal.emit(str(self.real_room_id))

                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
                    try:
                        async for msg in ws:
                            if not self.is_running:
                                break
                            if msg.type == aiohttp.WSMsgType.BINARY:
                                self._parse_packet(msg.data)
                    finally:
                        heartbeat_task.cancel()
        except Exception as e:
            self.disconnected_signal.emit(str(e))
        finally:
            self.is_running = False
            self.disconnected_signal.emit("连接已关闭")

    async def _heartbeat_loop(self, ws):
        while self.is_running:
            try:
                hb_packet = struct.pack(">IHHII", 16, 16, 1, OP_HEARTBEAT, 1)
                await ws.send_bytes(hb_packet)
                await asyncio.sleep(30)
            except Exception:
                break

    def stop(self):
        self.is_running = False

    def _parse_packet(self, data):
        offset = 0
        total_len = len(data)
        while offset < total_len:
            if offset + 16 > total_len:
                break
            packet_len, header_len, ver, opcode, seq = struct.unpack(">IHHII", data[offset:offset+16])
            if packet_len < 16 or offset + packet_len > total_len:
                break
            body = data[offset+16:offset+packet_len]
            offset += packet_len

            if ver == 2:
                try:
                    decompressed = zlib.decompress(body)
                    self._parse_packet(decompressed)
                except Exception:
                    pass
                continue
            elif ver == 3:
                try:
                    import brotli
                    decompressed = brotli.decompress(body)
                    self._parse_packet(decompressed)
                except Exception:
                    pass
                continue

            if opcode == OP_HEARTBEAT_REPLY:
                if len(body) >= 4:
                    popularity = struct.unpack(">I", body[:4])[0]
                    self.popularity_signal.emit(popularity)
            elif opcode == OP_SEND_SMS_REPLY:
                try:
                    msg_json = json.loads(body.decode("utf-8"))
                    self._handle_command(msg_json)
                except Exception:
                    pass

    def _extract_avatar(self, data, uid):
        raw_str = json.dumps(data)
        match = re.search(r'"face"\s*:\s*"(https?://[^"]+)"', raw_str)
        if match:
            return match.group(1).replace(r'\/', '/')
        match = re.search(r'"uface"\s*:\s*"(https?://[^"]+)"', raw_str)
        if match:
            return match.group(1).replace(r'\/', '/')
        if uid in self.avatar_cache:
            return self.avatar_cache[uid]
        if uid and uid > 0:
            asyncio.create_task(self._fetch_avatar_async(uid))
        return ""

    async def _fetch_avatar_async(self, uid):
        if uid in self.avatar_cache:
            return self.avatar_cache[uid]
        try:
            url = f"https://api.bilibili.com/x/web-interface/card?mid={uid}"
            headers = {"User-Agent": "Mozilla/5.0"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        j = await resp.json()
                        face = j.get("data", {}).get("card", {}).get("face", "")
                        if face:
                            self.avatar_cache[uid] = face
                            return face
        except Exception:
            pass
        return ""

    def _handle_command(self, data):
        cmd = data.get("cmd", "")
        if cmd.startswith("DANMU_MSG"):
            info = data.get("info", [])
            user_info = info[2] if len(info) > 2 else []
            medal_info = info[3] if len(info) > 3 else []
            uid = user_info[0] if len(user_info) > 0 else 0
            
            danmaku_data = {
                "user": user_info[1] if len(user_info) > 1 else "匿名用户",
                "uid": uid,
                "text": info[1] if len(info) > 1 else "",
                "avatar": self._extract_avatar(data, uid),
                "level": info[4][0] if len(info) > 4 and isinstance(info[4], list) else 0,
                "medal_name": medal_info[1] if len(medal_info) > 1 else "",
                "medal_level": medal_info[0] if len(medal_info) > 0 else 0,
                "guard_level": info[7] if len(info) > 7 else 0,
                "type": "chat"
            }
            self.danmaku_signal.emit(danmaku_data)

        elif cmd == "SEND_GIFT":
            gdata = data.get("data", {})
            uid = gdata.get("uid", 0)
            gift_data = {
                "user": gdata.get("uname", "匿名"),
                "uid": uid,
                "avatar": self._extract_avatar(data, uid),
                "gift_name": gdata.get("giftName", "礼物"),
                "num": gdata.get("num", 1),
                "price": gdata.get("price", 0) / 1000,
                "coin_type": gdata.get("coin_type", "gold"),
                "type": "gift"
            }
            self.gift_signal.emit(gift_data)

        elif cmd in ("SUPER_CHAT_MESSAGE", "SUPER_CHAT_MESSAGE_JPN"):
            scdata = data.get("data", {})
            uinfo = scdata.get("user_info", {})
            uid = scdata.get("uid", 0)
            sc_data = {
                "user": uinfo.get("uname", "匿名"),
                "uid": uid,
                "avatar": uinfo.get("face", "") or self._extract_avatar(data, uid),
                "price": scdata.get("price", 0),
                "text": scdata.get("message", ""),
                "time": scdata.get("time", 30),
                "type": "superchat"
            }
            self.superchat_signal.emit(sc_data)

        elif cmd == "GUARD_BUY":
            gbdata = data.get("data", {})
            uid = gbdata.get("uid", 0)
            guard_data = {
                "user": gbdata.get("username", "匿名"),
                "uid": uid,
                "avatar": self._extract_avatar(data, uid),
                "gift_name": gbdata.get("gift_name", "大航海"),
                "num": gbdata.get("num", 1),
                "guard_level": gbdata.get("guard_level", 3),
                "type": "guard"
            }
            self.guard_signal.emit(guard_data)

        elif cmd in ("INTERACT_WORD", "LIKE_INFO_V3_CLICK"):
            idata = data.get("data", {})
            uid = idata.get("uid", 0)
            interact_data = {
                "user": idata.get("uname", "匿名"),
                "uid": uid,
                "avatar": self._extract_avatar(data, uid),
                "msg_type": idata.get("msg_type", 1),
                "type": "enter"
            }
            self.interact_signal.emit(interact_data)

class BilibiliWSThread(QThread):
    def __init__(self, client: BilibiliWSClient, parent=None):
        super().__init__(parent)
        self.client = client

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.client.start_async())
        finally:
            loop.close()
