document.addEventListener("DOMContentLoaded", () => {
    const chatWindow = document.getElementById("chat-window");
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");

    const clientId = "client_" + Math.floor(Math.random() * 1000);
    const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

    let typing = false;
    let typingTimeout;

    function sendMessage(message) {
        if (message.trim() !== "") {
            const messageData = {
                client_id: clientId,
                message: message
            };
            ws.send(JSON.stringify(messageData));
            messageInput.value = "";
        }
    }

    sendButton.addEventListener("click", () => {
        sendMessage(messageInput.value);
    });

    messageInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage(messageInput.value);
        }
    });

    // Отслеживание начала набора сообщения
    messageInput.addEventListener("input", () => {
        typing = true;
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            typing = false;
        }, 1000);
        sendTypingStatus();
    });

    function sendTypingStatus() {
        const typingData = {
            client_id: clientId,
            typing: typing
        };
        ws.send(JSON.stringify(typingData));
    }

    ws.onmessage = function(event) {
        const eventData = JSON.parse(event.data);
        
        // Если сообщение о печати, обновляем интерфейс
        if (eventData.client_id !== clientId && eventData.typing) {
            showTypingIndicator(eventData.client_id);
        } else { // Иначе отображаем сообщение
            const messageElement = document.createElement("div");
            messageElement.classList.add("message");
            if (eventData.client_id === clientId) {
                messageElement.classList.add("self");
            }
            messageElement.textContent = eventData.message;
            chatWindow.appendChild(messageElement);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    };

    function showTypingIndicator(clientId) {
        let typingMessage = document.querySelector(`#typing-${clientId}`);
        if (!typingMessage) {
            typingMessage = document.createElement("div");
            typingMessage.id = `typing-${clientId}`;
            typingMessage.classList.add("typing");
            typingMessage.textContent = "Печатает сообщение...";
            chatWindow.appendChild(typingMessage);
        }
    }
});
