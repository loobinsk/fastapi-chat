from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from chat_manager import ChatManager
import asyncio
import aio_pika
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    client_id: str
    message: str

chat_manager = ChatManager()

@app.on_event("startup")
async def startup():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    app.state.rabbitmq_connection = connection
    asyncio.create_task(chat_manager.consume_messages(connection))

@app.on_event("shutdown")
async def shutdown():
    await app.state.rabbitmq_connection.close()

@app.websocket("/ws/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    await chat_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = Message.parse_raw(data)
            await chat_manager.send_message(message_data)
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket)
