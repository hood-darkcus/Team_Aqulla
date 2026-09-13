import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8000/ws/frontend') as ws:
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            print(msg)

asyncio.run(test())