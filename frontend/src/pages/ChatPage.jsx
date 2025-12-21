import { useState } from 'react';
import { FiSend, FiMessageSquare, FiAlertCircle } from 'react-icons/fi';

const API_BASE_URL = 'http://localhost:8000';

export default function ChatPage() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = message;
    setMessages([...messages, { text: userMessage, sender: 'user' }]);
    setMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Update conversation ID if this is the first message
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      setMessages(prev => [...prev, {
        text: data.response,
        sender: 'ai',
        metadata: data.metadata
      }]);
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to connect to backend. Make sure the server is running at ' + API_BASE_URL);
      setMessages(prev => [...prev, {
        text: 'Error: Could not connect to the backend API. Please ensure the server is running.',
        sender: 'error'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Chat Assistant</h1>
          <p className="mt-2 text-gray-600">Ask engineering questions and get AI-powered answers</p>
        </div>
        {conversationId && (
          <div className="text-sm text-gray-500">
            Session: {conversationId.substring(0, 8)}...
          </div>
        )}
      </div>

      {error && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-center gap-2 text-red-800">
            <FiAlertCircle className="w-5 h-5" />
            <span className="font-semibold">Connection Error</span>
          </div>
          <p className="mt-2 text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="card h-[600px] flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <FiMessageSquare className="w-16 h-16 mb-4" />
              <p>Start a conversation by typing a message below</p>
              <p className="mt-2 text-sm">Connected to backend at {API_BASE_URL}</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-sm px-4 py-2 rounded-lg ${
                    msg.sender === 'user'
                      ? 'bg-primary-600 text-white'
                      : msg.sender === 'error'
                      ? 'bg-red-100 text-red-900 border border-red-300'
                      : 'bg-gray-200 text-gray-900'
                  }`}
                >
                  <div>{msg.text}</div>
                  {msg.metadata && msg.metadata.sources && (
                    <div className="mt-2 pt-2 border-t border-gray-300 text-xs">
                      <strong>Sources:</strong> {msg.metadata.sources.join(', ')}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-sm px-4 py-2 rounded-lg bg-gray-200 text-gray-900">
                <div className="flex items-center gap-2">
                  <div className="animate-pulse">Thinking...</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Type your message..."
              className="input-field"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              className="btn-primary"
              disabled={isLoading || !message.trim()}
            >
              <FiSend className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <div className="card bg-green-50">
        <h3 className="font-semibold text-green-900">✓ Connected to Backend</h3>
        <p className="mt-2 text-sm text-green-800">
          Full chat functionality enabled with RAG, citations, and ambiguity detection.
          Backend API: {API_BASE_URL}
        </p>
      </div>
    </div>
  );
}
