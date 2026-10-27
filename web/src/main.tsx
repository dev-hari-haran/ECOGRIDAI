import React, { Component, ErrorInfo, ReactNode } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Critical React Application Error:", error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: "100vh", backgroundColor: "#fefae0", padding: "24px", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "sans-serif" }}>
          <div style={{ maxWidth: "520px", width: "100%", backgroundColor: "#ffffff", borderRadius: "16px", padding: "24px", boxShadow: "0 10px 30px rgba(0,0,0,0.1)", border: "1px solid #e5e7eb" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#b93829", fontWeight: "bold", fontSize: "18px", marginBottom: "8px" }}>
              <span>⚠️</span>
              <span>Application Notice</span>
            </div>
            <p style={{ fontSize: "14px", color: "#4b5563", marginBottom: "16px" }}>
              A render exception was caught:
            </p>
            <div style={{ backgroundColor: "#fef3c7", padding: "12px", borderRadius: "8px", fontFamily: "monospace", fontSize: "12px", color: "#78350f", overflowX: "auto", marginBottom: "16px", border: "1px solid #fde68a" }}>
              {this.state.error?.message || "Render Error"}
              {this.state.error?.stack && (
                <pre style={{ marginTop: "8px", fontSize: "11px", whiteSpace: "pre-wrap" }}>
                  {this.state.error.stack}
                </pre>
              )}
            </div>
            <button
              onClick={() => {
                try {
                  localStorage.clear()
                  sessionStorage.clear()
                } catch {
                  // ignore
                }
                window.location.reload()
              }}
              style={{ width: "100%", padding: "10px 16px", backgroundColor: "#283618", color: "#fefae0", borderRadius: "10px", border: "none", fontWeight: "600", fontSize: "14px", cursor: "pointer" }}
            >
              Reset Session & Reload Application
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

function mount() {
  const rootEl = document.getElementById('root')
  if (rootEl) {
    ReactDOM.createRoot(rootEl).render(
      <ErrorBoundary>
        <App />
      </ErrorBoundary>,
    )
  } else {
    window.addEventListener('DOMContentLoaded', mount)
  }
}

mount()
