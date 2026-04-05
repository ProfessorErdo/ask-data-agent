import { useState, useEffect, useRef, useCallback } from 'react'
import './App.css'

// Progress sections based on BRD template
const progressSections = [
  { id: 'project', title: 'Project Overview', items: ['Name', 'Sponsor', 'Owner', 'Team', 'Timeline', 'Objective'] },
  { id: 'business', title: 'Business Background', items: ['Context', 'Pain Points', 'Business Value'] },
  { id: 'stakeholder', title: 'Stakeholder Analysis', items: ['Stakeholders', 'Interests', 'Expectations'] },
  { id: 'requirements', title: 'Core Requirements', items: ['Data Sources', 'Visualization', 'Insights', 'Non-functional'] },
  { id: 'constraints', title: 'Constraints & Risks', items: ['Resources', 'Timeline', 'Risks'] },
  { id: 'deliverables', title: 'Deliverables', items: ['List of deliverables'] }
]

// Keywords for detecting BRD fields in conversation
const fieldKeywords = {
  project: {
    Name: ['project name', 'called', 'named', 'title'],
    Sponsor: ['sponsor', 'sponsored by', 'funding', 'budget owner'],
    Owner: ['owner', 'lead', 'responsible', 'in charge', 'data analyst lead'],
    Team: ['team', 'members', 'team members', 'analyst', 'engineer', 'designer'],
    Timeline: ['timeline', 'schedule', 'start date', 'end date', 'deadline', 'milestone', 'by when'],
    Objective: ['objective', 'goal', 'purpose', 'aim', 'target', 'kpi', 'okr']
  },
  business: {
    Context: ['context', 'background', 'situation', 'current state', 'industry', 'business scenario'],
    'Pain Points': ['pain point', 'problem', 'issue', 'challenge', 'difficulty', 'struggle', 'frustrat'],
    'Business Value': ['value', 'benefit', 'impact', 'roi', 'improve', 'increase', 'reduce', 'drive']
  },
  stakeholder: {
    Stakeholders: ['stakeholder', 'stake holders', 'participant', 'involved', 'department', 'representative'],
    Interests: ['interest', 'concern', 'priorit', 'care about', 'focus on'],
    Expectations: ['expect', 'want', 'need', 'require', 'hope', 'deliver']
  },
  requirements: {
    'Data Sources': ['data source', 'database', 'data base', 'api', 'data feed', 'data stream', 'collect'],
    Visualization: ['visualization', 'visual', 'dashboard', 'chart', 'graph', 'report', 'display', 'view'],
    Insights: ['insight', 'analysis', 'analyze', 'findings', 'recommendation', 'trend'],
    'Non-functional': ['non-functional', 'performance', 'security', 'scalability', 'usability', 'accessibility']
  },
  constraints: {
    Resources: ['resource', 'budget', 'tool', 'license', 'personnel', 'staff'],
    Timeline: ['timeline', 'deadline', 'time constraint', 'urgency', 'quick'],
    Risks: ['risk', 'concern', 'uncertainty', 'potential issue', 'mitigation']
  },
  deliverables: {
    'List of deliverables': ['deliverable', 'deliver', 'output', 'result', 'document', 'prototype', 'final']
  }
}

// Welcome message
const welcomeMessage = `Hello! I'm your Product Manager assistant. I'll help you create a Business Requirements Document (BRD) for your data analysis project.

I'll ask you questions about:
- Your project overview (name, team, timeline, objectives)
- Business background and pain points
- Stakeholders and their expectations
- Core requirements (data sources, visualizations, insights)
- Constraints and risks
- Expected deliverables

Let's get started! What is the name of your project?`

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [model, setModel] = useState('qwen')
  const [loading, setLoading] = useState(false)
  const [brdTemplate, setBrdTemplate] = useState('')
  const [collectedFields, setCollectedFields] = useState({
    project: new Set(),
    business: new Set(),
    stakeholder: new Set(),
    requirements: new Set(),
    constraints: new Set(),
    deliverables: new Set()
  })
  const messagesEndRef = useRef(null)

  // Load BRD template on mount
  useEffect(() => {
    fetch('/brd-template')
      .then(res => res.json())
      .then(data => setBrdTemplate(data.content))
      .catch(err => console.error('Failed to load template:', err))
  }, [])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Analyze user input for field detection
  const analyzeContent = useCallback((content) => {
    const lowerContent = content.toLowerCase()

    setCollectedFields(prev => {
      const newCollected = { ...prev }

      Object.keys(fieldKeywords).forEach(section => {
        Object.keys(fieldKeywords[section]).forEach(field => {
          const keywords = fieldKeywords[section][field]
          const isDetected = keywords.some(keyword => lowerContent.includes(keyword))
          if (isDetected) {
            newCollected[section] = new Set([...newCollected[section], field])
          }
        })
      })

      return newCollected
    })
  }, [])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Create updated messages array with user message
    const updatedMessages = [...messages, { role: 'user', content: userMessage }]

    // Add user message to state
    setMessages(updatedMessages)

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          model: model,
          history: updatedMessages
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      const aiMessage = { role: 'ai', content: data.response }

      setMessages(prev => [...prev, aiMessage])

      // Analyze user input for field detection
      analyzeContent(userMessage)
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Sorry, I encountered an error. Make sure Ollama is running with the qwen or gemma model.'
      }])
    }

    setLoading(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    if (window.confirm('Are you sure you want to clear the conversation? This cannot be undone.')) {
      setMessages([])
      setCollectedFields({
        project: new Set(),
        business: new Set(),
        stakeholder: new Set(),
        requirements: new Set(),
        constraints: new Set(),
        deliverables: new Set()
      })
    }
  }

  const handleExport = async () => {
    // Build BRD content by filling in the template
    let brdContent = brdTemplate || '# BRD Document\n\n'

    // Extract conversation summary
    const conversationSummary = messages
      .filter(m => m.role === 'user')
      .map(m => `- ${m.content}`)
      .join('\n')

    // Try to fill in sections based on collected fields
    const filledSections = []

    if (collectedFields.project.size > 0) {
      filledSections.push(`## Project Overview\nDetected: ${[...collectedFields.project].join(', ')}`)
    }
    if (collectedFields.business.size > 0) {
      filledSections.push(`## Business Background\nDetected: ${[...collectedFields.business].join(', ')}`)
    }
    if (collectedFields.stakeholder.size > 0) {
      filledSections.push(`## Stakeholder Analysis\nDetected: ${[...collectedFields.stakeholder].join(', ')}`)
    }
    if (collectedFields.requirements.size > 0) {
      filledSections.push(`## Core Requirements\nDetected: ${[...collectedFields.requirements].join(', ')}`)
    }
    if (collectedFields.constraints.size > 0) {
      filledSections.push(`## Constraints & Risks\nDetected: ${[...collectedFields.constraints].join(', ')}`)
    }
    if (collectedFields.deliverables.size > 0) {
      filledSections.push(`## Deliverables\nDetected: ${[...collectedFields.deliverables].join(', ')}`)
    }

    const summary = `# Draft BRD - ${new Date().toLocaleDateString()}

## Collected Information

${filledSections.length > 0 ? filledSections.join('\n\n') : 'No specific fields detected yet.'}

## Conversation Summary

${conversationSummary || 'No conversation yet.'}

---
*Generated by Ask Data - BRD Collection Chatbot*
`

    try {
      const response = await fetch('/export-brd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ brd_content: summary })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      alert(`BRD exported to: ${data.file_path}`)
    } catch (err) {
      console.error('Export error:', err)
      alert(`Failed to export BRD: ${err.message || 'Unknown error. Please check if the backend server is running.'}`)
    }
  }

  // Calculate progress percentage
  const calculateProgress = () => {
    let total = 0
    let completed = 0

    progressSections.forEach(section => {
      total += section.items.length
      completed += collectedFields[section.id]?.size || 0
    })

    return total > 0 ? Math.round((completed / total) * 100) : 0
  }

  const progressPercent = calculateProgress()

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <h1>Ask Data</h1>
          <span className="header-subtitle">BRD Collection Assistant</span>
        </div>
        <div className="header-controls">
          <select
            className="model-selector"
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="qwen">Qwen</option>
            <option value="gemma">Gemma</option>
          </select>
          <button className="clear-button" onClick={handleClear} title="Clear conversation">
            Clear
          </button>
        </div>
      </header>

      <main className="main-content">
        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="message ai welcome-message">
                <div className="message-header">AI Assistant</div>
                {welcomeMessage}
              </div>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-header">
                  {msg.role === 'user' ? 'You' : 'AI Assistant'}
                </div>
                <div className="message-content">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="loading">
                <div className="spinner"></div>
                Thinking...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <textarea
              className="chat-input"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              rows={1}
            />
            <button
              className="send-button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>

        <aside className="progress-sidebar">
          <div className="progress-header">
            <h3>BRD Progress</h3>
            <span className="progress-percent">{progressPercent}%</span>
          </div>

          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
          </div>

          {progressSections.map(section => {
            const completedCount = collectedFields[section.id]?.size || 0
            const totalCount = section.items.length
            const isComplete = completedCount === totalCount

            return (
              <div key={section.id} className={`progress-section ${isComplete ? 'complete' : ''}`}>
                <div className="progress-section-title">
                  <span className={`icon ${isComplete ? 'completed' : 'pending'}`}>
                    {isComplete ? '✓' : '○'}
                  </span>
                  <span className="section-name">{section.title}</span>
                  <span className="section-count">{completedCount}/{totalCount}</span>
                </div>
                <div className="progress-items">
                  {section.items.map((item, idx) => {
                    const isItemComplete = collectedFields[section.id]?.has(item)
                    return (
                      <div key={idx} className={`progress-item ${isItemComplete ? 'completed' : ''}`}>
                        <span className="item-bullet">{isItemComplete ? '●' : '○'}</span>
                        {item}
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}

          <div className="export-section">
            <button className="export-button" onClick={handleExport}>
              Export Draft BRD
            </button>
          </div>
        </aside>
      </main>
    </div>
  )
}

export default App