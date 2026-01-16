import React, { useState, useRef, useEffect } from 'react';
import TextInput from "./Components/TextInput";
import Markdown from 'react-markdown'
import "./Styles/llm_chat.css";

export default function Llm_chat({ SCREEN_STATES, setScreenState, handleSearch, set_vacio }) {
    // Determine initial message based on prop
    const initialMessage = set_vacio
        ? "Lo siento, no encontré vacantes para esa área. ¿Quieres intentar otra búsqueda?"
        : "Hola, ¿en qué puedo ayudarte hoy?";

    const [messages, setMessages] = useState([
        { id: 1, text: initialMessage, sender: 'ai' }
    ]);
    const [inputValue, setInputValue] = useState("");
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleFetch = async () => {
        const res = await fetch("http://192.168.8.106:8000/users/Chat_llm/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                ususario_respuesta: inputValue,
            }),
        });

        if (res.ok) {
            const data = await res.json();
            if (data.IA_text) {
                setOfertas(data.datos);
                setScreenState(SCREEN_STATES.RESULTS);
            } else {
                setMessages(prev => [...prev, {
                    id: Date.now() + 1,
                    text: data.output,
                    sender: 'ai'
                }]);
            }
        }
    };

    const handleSendMessage = () => {
        if (!inputValue.trim()) return;

        const newMessage = {
            id: Date.now(),
            text: inputValue,
            sender: 'user'
        };

        setMessages(prev => [...prev, newMessage]);
        setInputValue("");

        handleFetch();
        // // Simulate AI response
        // setTimeout(() => {
        //     setMessages(prev => [...prev, {
        //         id: Date.now() + 1,
        //         text: "Entiendo. Estoy procesando tu solicitud...",
        //         sender: 'ai'
        //     }]);
        // }, 1000);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    };

    return (
        <div className="Chat-Container">
            <div className="Chat-Header">
                <h3 className="Chat-Title">Asistente Virtual</h3>
            </div>

            <div className="Chat-Messages">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`Message-Wrapper ${msg.sender === 'user' ? 'User' : 'AI'}`}
                    >
                        <div className="Message-Bubble">
                            <Markdown>
                                {msg.text}
                            </Markdown>
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Replaced custom input with shared TextInput component */}
            <div style={{ padding: '10px 20px', borderTop: '1px solid var(--border-light)' }}>
                <TextInput
                    inputText={inputValue}
                    setInputText={setInputValue}
                    setSearchButton={handleSendMessage}
                    onKeyDown={handleKeyDown}
                    textinputContainerWidth="100%"
                    textinputWidth="90%"
                />
            </div>
        </div>
    );
}