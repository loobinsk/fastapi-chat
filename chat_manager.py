import asyncio
from datetime import datetime
from fastapi import WebSocket
import aio_pika
from typing import List
from pydantic import BaseModel


class Message(BaseModel):
    client_id: str
    message: str

class TypingEvent(BaseModel):
    client_id: str
    typing: bool

class ChatManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.typing_states = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.typing_states:
            del self.typing_states[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_message(self, message: Message):
        channel = await self.connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message.json().encode()),
            routing_key="chat_queue"
        )

    async def consume_messages(self, connection):
        self.connection = connection
        channel = await connection.channel()
        queue = await channel.declare_queue("chat_queue", durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    message_data = Message.parse_raw(message.body.decode())
                    await self.broadcast(message_data.json())

    async def update_typing_status(self, websocket: WebSocket, typing: bool):
        self.typing_states[websocket] = typing
        typing_event = TypingEvent(client_id=self.get_client_id(websocket), typing=typing)
        await self.broadcast(typing_event.json())

    def get_client_id(self, websocket: WebSocket):
        return websocket.headers.get("sec-websocket-key")  # Assuming client_id is derived from websocket headers

    async def handle_typing_event(self, websocket: WebSocket, event: dict):
        typing = event.get("typing", False)
        await self.update_typing_status(websocket, typing)

    async def notify_typing_status(self, websocket: WebSocket):
        while True:
            try:
                if websocket in self.typing_states:
                    typing = self.typing_states[websocket]
                    typing_event = TypingEvent(client_id=self.get_client_id(websocket), typing=typing)
                    await websocket.send_json(typing_event.json())
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in notify_typing_status: {e}")

    async def start_notify_task(self, websocket: WebSocket):
        try:
            await self.notify_typing_status(websocket)
        except asyncio.CancelledError:
            pass
        finally:
            self.disconnect(websocket)
