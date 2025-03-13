from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import uvicorn

app = FastAPI()

# Load the HTML file into a string
with open("frontend.html", "r", encoding="utf-8") as file:
    chat_html = file.read()

# Active WebSocket connections
clients = set()
message_history = []  # Store chat messages

@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the chat client."""
    return chat_html

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time chat."""
    await websocket.accept()
    clients.add(websocket)

    # Send chat history to new connection
    for message in message_history:
        await websocket.send_json(message)

    try:
        while True:
            data = await websocket.receive_json()
            message_history.append(data)  # Save message
            # Broadcast message to all clients
            await asyncio.gather(*(client.send_json(data) for client in clients))
    except WebSocketDisconnect:
        clients.remove(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)