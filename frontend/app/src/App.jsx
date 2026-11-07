import { useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'
const languageExamples = {
  English: 'Show PM-KISAN beneficiaries by state',
  Hindi: 'राज्य के अनुसार पीएम-किसान लाभार्थियों की संख्या दिखाएं',
  Bengali: 'রাজ্য অনুযায়ী পিএম-কিষাণ সুবিধাভোগীর সংখ্যা দেখান',
  Tamil: 'மாநில வாரியாக பிஎம் கிசான் பயனாளர்களின் எண்ணிக்கையைக் காட்டுங்கள்',
  Telugu: 'రాష్ట్రాల వారీగా పీఎం కిసాన్ లబ్ధిదారుల సంఖ్యను చూపించండి',
  Marathi: 'राज्यानुसार पीएम-किसान लाभार्थ्यांची संख्या दाखवा',
  Hinglish: 'State ke hisaab se PM-KISAN beneficiaries dikhao',
}
const localizedAnswers = {
  English: (count) => `Found ${count} ${count === 1 ? 'record' : 'records'}. See the table below for the data.`,
  Hindi: (count) => `${count} रिकॉर्ड मिले। डेटा के लिए नीचे दी गई तालिका देखें।`,
  Bengali: (count) => `${count}টি রেকর্ড পাওয়া গেছে। তথ্যের জন্য নিচের সারণি দেখুন।`,
  Tamil: (count) => `${count} பதிவுகள் கிடைத்தன. தரவைக் காண கீழே உள்ள அட்டவணையைப் பார்க்கவும்.`,
  Telugu: (count) => `${count} రికార్డులు లభించాయి. డేటా కోసం దిగువ పట్టికను చూడండి.`,
  Marathi: (count) => `${count} नोंदी मिळाल्या. डेटासाठी खालील तक्ता पहा.`,
  Hinglish: (count) => `${count} records mile. Data ke liye neeche table dekhein.`,
}
const languageByCode = {
  en: 'English',
  hi: 'Hindi',
  bn: 'Bengali',
  ta: 'Tamil',
  te: 'Telugu',
  mr: 'Marathi',
  'hi-en': 'Hinglish',
}

function App() {
  const [selectedLanguage, setSelectedLanguage] = useState('English')
  const [query, setQuery] = useState(languageExamples.English)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryInput = useRef(null)

  const fetchJson = async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    })
    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.detail || data.error || 'Request failed')
    }

    return data
  }

  const handleRunQuery = async () => {
    if (!query.trim()) {
      setError('Enter a question to search the data.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await fetchJson(`${API_BASE_URL}/query`, {
        method: 'POST',
        body: JSON.stringify({ query }),
      })
      if (languageByCode[data.detected_language]) {
        setSelectedLanguage(languageByCode[data.detected_language])
      }
      setResult(data.execution_result || { columns: [], rows: [], row_count: 0 })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const columns = result?.columns || []
  const rows = result?.rows || []
  const resultCount = result?.row_count ?? rows.length

  const handleNewQuestion = () => {
    setQuery('')
    setResult(null)
    setError('')
    queryInput.current?.focus()
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">B</span>
          <div>
            <p className="eyebrow">IndicSQL data explorer</p>
            <h1>BharatQuery</h1>
          </div>
        </div>
      </header>

      <main className="dashboard">
        <section className="panel query-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Search public data</p>
              <h2>What would you like to find?</h2>
            </div>
            {result ? (
              <button type="button" className="new-question" onClick={handleNewQuestion}>
                New question
              </button>
            ) : null}
          </div>
          <div className="language-picker" aria-label="Choose a query language">
            {Object.keys(languageExamples).map((language) => (
              <button
                key={language}
                type="button"
                className={`language-chip${selectedLanguage === language ? ' selected' : ''}`}
                aria-pressed={selectedLanguage === language}
                onClick={() => {
                  setSelectedLanguage(language)
                  setQuery(languageExamples[language])
                }}
              >
                {language}
              </button>
            ))}
          </div>
          <textarea
            ref={queryInput}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows={4}
            placeholder="Type a new question about the available datasets…"
            aria-label={`Question in ${selectedLanguage}`}
          />
          <button
            type="button"
            className="primary"
            onClick={handleRunQuery}
            disabled={loading}
          >
            {loading ? 'Searching data…' : 'Search data'}
          </button>
        </section>

        <section className="panel results-panel" aria-live="polite">
          <div className="section-heading results-heading">
            <div>
              <p className="eyebrow">Results</p>
              <h2>Fetched data</h2>
            </div>
            {result ? (
              <span className="result-count">
                {resultCount} {resultCount === 1 ? 'record' : 'records'}
              </span>
            ) : null}
          </div>

          {error ? <div className="message error">{error}</div> : null}

          {result ? (
            <div className="answer-summary">
              <p className="eyebrow">Answer · {selectedLanguage}</p>
              <p>{localizedAnswers[selectedLanguage](resultCount)}</p>
              <div className="answer-divider" />
              <p className="eyebrow">English</p>
              <p>{localizedAnswers.English(resultCount)}</p>
            </div>
          ) : null}

          {result && columns.length > 0 && rows.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>{columns.map((column) => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr>
                </thead>
                <tbody>
                  {rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {columns.map((column, columnIndex) => (
                        <td key={`${column}-${columnIndex}`}>
                          {row[columnIndex] == null ? '—' : String(row[columnIndex])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : result ? (
            <p className="empty-state">No matching records were returned. Try a different question.</p>
          ) : (
            <p className="empty-state">Your fetched records will appear here.</p>
          )}
        </section>
      </main>
      <footer>IndicSQL · Government data, made easier to explore</footer>
    </div>
  )
}

export default App
