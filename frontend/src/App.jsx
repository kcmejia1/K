import { useState } from "react"

const PASSWORD = "kcsai2025"

function App() {
  const [authenticated, setAuthenticated] = useState(false)
  const [passwordInput, setPasswordInput] = useState("")
  const [passwordError, setPasswordError] = useState("")
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  const handleLogin = () => {
    if (passwordInput === PASSWORD) {
      setAuthenticated(true)
    } else {
      setPasswordError("Wrong password. Try again!")
    }
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = { role: "user", content: input }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput("")
    setLoading(true)

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input, history: messages })
      })
      const data = await response.json()
      setMessages([...newMessages, { role: "assistant", content: data.response }])
    } catch (error) {
      setMessages([...newMessages, { role: "assistant", content: "Error connecting to server." }])
    }

    setLoading(false)
  }

  if (!authenticated) {
    return (
      <div style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        fontFamily: "sans-serif",
        backgroundColor: "#f0f2f5"
      }}>
        <div style={{
          backgroundColor: "white",
          padding: "40px",
          borderRadius: "12px",
          boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
          width: "300px",
          textAlign: "center"
        }}>
          <h2>🤖 KC's AI Assistant</h2>
          <p style={{ color: "#666" }}>Enter password to continue</p>
          <input
            type="password"
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "8px",
              border: "1px solid #ddd",
              fontSize: "16px",
              marginBottom: "10px",
              boxSizing: "border-box"
            }}
            value={passwordInput}
            onChange={(e) => setPasswordInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            placeholder="Password"
          />
          {passwordError && <p style={{ color: "red", fontSize: "14px" }}>{passwordError}</p>}
          <button
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "8px",
              backgroundColor: "#0084ff",
              color: "white",
              border: "none",
              fontSize: "16px",
              cursor: "pointer"
            }}
            onClick={handleLogin}
          >
            Enter
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "20px", fontFamily: "sans-serif" }}>
      <h1>🤖 KC's AI Assistant</h1>

      <div style={{
        height: "500px",
        overflowY: "auto",
        border: "1px solid #ddd",
        borderRadius: "8px",
        padding: "16px",
        marginBottom: "16px",
        backgroundColor: "#f9f9f9"
      }}>
        {messages.length === 0 && (
          <p style={{ color: "#999", textAlign: "center" }}>Ask me anything...</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{
            display: "flex",
            justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
            marginBottom: "12px"
          }}>
            <div style={{
              maxWidth: "70%",
              padding: "10px 14px",
              borderRadius: "18px",
              backgroundColor: msg.role === "user" ? "#0084ff" : "#e4e4e4",
              color: msg.role === "user" ? "white" : "black"
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ textAlign: "left", color: "#999" }}>Thinking...</div>
        )}
      </div>

      <div style={{ display: "flex", gap: "8px" }}>
        <input
          style={{
            flex: 1,
            padding: "12px",
            borderRadius: "8px",
            border: "1px solid #ddd",
            fontSize: "16px"
          }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Ask me anything..."
        />
        <button
          style={{
            padding: "12px 20px",
            borderRadius: "8px",
            backgroundColor: "#0084ff",
            color: "white",
            border: "none",
            fontSize: "16px",
            cursor: "pointer"
          }}
          onClick={sendMessage}
          disabled={loading}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default App