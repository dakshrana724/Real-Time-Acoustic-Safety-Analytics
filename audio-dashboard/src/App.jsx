import { useState, useEffect, useRef } from 'react'
import { io } from 'socket.io-client'
import './App.css'

const socket = io('http://127.0.0.1:5000')

function App() {
  const [isConnected, setIsConnected] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [latestTranscript, setLatestTranscript] = useState('')
  const [alertInfo, setAlertInfo] = useState(null)
  const [systemLogs, setSystemLogs] = useState([])

  const recognitionRef = useRef(null)
  const explicitStopRef = useRef(false)

  // Helper to log system events dynamically on screen
  const addLog = (message) => {
    setSystemLogs((prev) => [ `[${new Date().toLocaleTimeString()}] ${message}`, ...prev.slice(0, 15) ])
  }

  useEffect(() => {
    socket.on('connect', () => {
      setIsConnected(true)
      addLog('Connected to Python WebSocket pipeline')
    })

    socket.on('disconnect', () => {
      setIsConnected(false)
      addLog('Disconnected from Python server')
    })

    // Catch processing callbacks from local ML or cloud cleared states
    socket.on('chunk_processed', (res) => {
      addLog(`Server Engine: ${res.info}`)
    })

    // Catch critical threat alerts from the Python pipeline
    socket.on('safety_alert', (res) => {
      setAlertInfo(res.info)
      addLog(`🚨 ALARM: ${res.info}`)
    })

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('chunk_processed')
      socket.off('safety_alert')
    }
  }, [])

  const initializeSpeechEngine = () => {
    // Cross-browser setup for Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Your browser does not support the Web Speech API. Please use Google Chrome or Microsoft Edge.')
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true         // Keep microphone open 24/7
    recognition.interimResults = false     // Wait until the full sentence is finished before transcribing
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      setIsListening(true)
      addLog('Microphone listening active (Hands-Free Mode)...')
    }

    recognition.onerror = (event) => {
      if (event.error !== 'no-speech') {
        addLog(`Speech Recognition Error: ${event.error}`)
      }
    }

    // Auto-Restart Loop: Reboots engine if the browser tries to silence it
    recognition.onend = () => {
      if (!explicitStopRef.current) {
        addLog('Re-indexing ambient noise environment...')
        recognition.start()
      } else {
        setIsListening(false)
        addLog('Microphone deactivated safely.')
      }
    }

    recognition.onresult = (event) => {
      const currentResultIndex = event.resultIndex
      const transcript = event.results[currentResultIndex][0].transcript.trim()
      
      if (transcript) {
        setLatestTranscript(transcript)
        addLog(`Spoken Context: "${transcript}"`)

        // Fire text across local network sockets to your Python classifier instantly
        if (socket.connected) {
          socket.emit('live_transcript', { text: transcript })
        }
      }
    }

    recognitionRef.current = recognition
    explicitStopRef.current = false
    recognition.start()
  }

  const startContinuousMonitoring = () => {
    setAlertInfo(null)
    initializeSpeechEngine()
  }

  const stopContinuousMonitoring = () => {
    explicitStopRef.current = true
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }

  return (
    <div className={`dashboard ${alertInfo ? 'panic-mode' : ''}`}>
      <h1>Acoustic Safety Analytics</h1>
      
      <div className="status-panel">
        <p>System Pipeline: 
          <span className={isConnected ? 'text-green' : 'text-red'}>
            {isConnected ? ' Active Localhost' : ' Offline'}
          </span>
        </p>
      </div>

      <div className="main-controls">
        {!isListening ? (
          <button onClick={startContinuousMonitoring} disabled={!isConnected} className="btn action-btn start-monitoring">
            Activate Continuous Background Monitoring
          </button>
        ) : (
          <button onClick={stopContinuousMonitoring} className="btn action-btn stop-monitoring">
            Deactivate Listening
          </button>
        )}
      </div>

      {alertInfo && (
        <div className="alert-banner">
          <h2>🚨 CRITICAL THREAT SIGNALS FLAGGED</h2>
          <p><strong>Verification Reason:</strong> {alertInfo}</p>
        </div>
      )}

      <div className="live-view">
        <div className="transcript-box">
          <h3>Latest Captured Ingestion:</h3>
          <p className="transcript-text">{latestTranscript || 'Awaiting vocalizations...'}</p>
        </div>

        <div className="log-box">
          <h3>Real-Time Pipeline Tracking:</h3>
          <div className="logs-container">
            {systemLogs.map((log, index) => (
              <div key={index} className="log-line">{log}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App