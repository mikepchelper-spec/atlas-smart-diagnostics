import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

type Locale = 'es' | 'en'

type OperatingSystem =
  | 'windows_10'
  | 'windows_11'
  | 'macos'
  | 'linux_ubuntu'
  | 'linux_debian'
  | 'linux_fedora'
  | 'linux_mint'
  | 'linux_arch'
  | 'linux_other'

type Difficulty = 'basic' | 'intermediate' | 'advanced' | 'data_risk'
type Probability = 'high' | 'medium' | 'low'
type Confidence = 'low' | 'medium' | 'high'

type Cause = {
  title: string
  explanation: string
  confidence: Confidence
}

type SafeStep = {
  title: string
  detail: string
  risk: Difficulty
}

type StopSignal = {
  title: string
  detail: string
}

type DiagnosticResponse = {
  case_id: string
  summary: string
  likely_causes: Cause[]
  difficulty: Difficulty
  self_service_probability: Probability
  risk_notice: string
  before_touching: string[]
  safe_steps: SafeStep[]
  stop_and_contact: StopSignal[]
  customer_message: string
  whatsapp_prefill: string
  disclaimer: string
  model_provider: string
  knowledge_matches: string[]
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
const WHATSAPP_NUMBER = import.meta.env.VITE_ATLAS_WHATSAPP_NUMBER ?? '51999999999'

const operatingSystems: { value: OperatingSystem; label: string; group: string }[] = [
  { value: 'windows_11', label: 'Windows 11', group: 'Windows' },
  { value: 'windows_10', label: 'Windows 10', group: 'Windows' },
  { value: 'macos', label: 'macOS', group: 'Apple' },
  { value: 'linux_ubuntu', label: 'Ubuntu', group: 'Linux' },
  { value: 'linux_debian', label: 'Debian', group: 'Linux' },
  { value: 'linux_fedora', label: 'Fedora', group: 'Linux' },
  { value: 'linux_mint', label: 'Linux Mint', group: 'Linux' },
  { value: 'linux_arch', label: 'Arch Linux', group: 'Linux' },
  { value: 'linux_other', label: 'Other Linux distro / Otra distro Linux', group: 'Linux' },
]

const difficultyLabel: Record<Locale, Record<Difficulty, string>> = {
  es: {
    basic: 'Básico',
    intermediate: 'Intermedio',
    advanced: 'Avanzado',
    data_risk: 'Riesgo de datos',
  },
  en: {
    basic: 'Basic',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
    data_risk: 'Data risk',
  },
}

const probabilityLabel: Record<Locale, Record<Probability, string>> = {
  es: { high: 'Alta', medium: 'Media', low: 'Baja' },
  en: { high: 'High', medium: 'Medium', low: 'Low' },
}

const confidenceLabel: Record<Locale, Record<Confidence, string>> = {
  es: { high: 'alta', medium: 'media', low: 'baja' },
  en: { high: 'high', medium: 'medium', low: 'low' },
}

const copy = {
  es: {
    eyebrow: 'Atlas PC Support',
    title: 'Asistente de Diagnóstico IA',
    hero:
      'Describe el error, adjunta una captura opcional y recibe un triaje seguro antes de tocar tu PC.',
    trust: ['Sin cuenta', 'Pasos seguros primero', 'CTA a soporte si hay riesgo'],
    language: 'Idioma / Language',
    os: 'Sistema operativo',
    linux: 'Distro Linux',
    linuxPlaceholder: 'Ej. openSUSE, Pop!_OS, Zorin OS',
    issue: 'Texto del error o explicación',
    issuePlaceholder:
      'Ej. Mi laptop muestra pantalla azul con código CRITICAL_PROCESS_DIED después de actualizar Windows...',
    chars: 'caracteres',
    image: 'Foto o captura opcional',
    imageHelp: 'JPG, PNG o WebP. Máximo configurado por el servidor.',
    consent:
      'Entiendo que esto es orientación general. No haré formateos, borrado de particiones ni cambios riesgosos sin respaldo.',
    submit: 'Generar diagnóstico seguro',
    loading: 'Analizando…',
    error: 'No se pudo generar el diagnóstico. Intenta otra vez o contacta a Atlas PC Support.',
    how: 'Cómo interpreta Atlas el caso',
    howItems: [
      'Causas probables con nivel de confianza.',
      'Dificultad para usuario básico y riesgo de datos.',
      'Pasos seguros, reversibles y ordenados.',
      'Cuándo parar y pedir soporte profesional.',
    ],
    chat: 'Hablar por WhatsApp',
    result: 'Resultado inicial',
    case: 'Caso',
    probability: 'Probabilidad autoservicio',
    provider: 'Proveedor',
    before: 'Antes de tocar nada',
    causes: 'Causas probables',
    confidence: 'Confianza',
    steps: 'Pasos recomendados',
    stop: 'Detente y pide ayuda si aparece esto',
    send: 'Enviar caso a Atlas por WhatsApp',
    knowledge: 'Runbooks Atlas relacionados',
  },
  en: {
    eyebrow: 'Atlas PC Support',
    title: 'AI Diagnostic Assistant',
    hero:
      'Describe the error, attach an optional screenshot, and receive safe triage before changing your PC.',
    trust: ['No account', 'Safe steps first', 'Support CTA if risk appears'],
    language: 'Report language / Idioma',
    os: 'Operating system',
    linux: 'Linux distro',
    linuxPlaceholder: 'e.g. openSUSE, Pop!_OS, Zorin OS',
    issue: 'Error text or explanation',
    issuePlaceholder:
      'e.g. My laptop shows a blue screen with CRITICAL_PROCESS_DIED after a Windows update...',
    chars: 'characters',
    image: 'Optional photo or screenshot',
    imageHelp: 'JPG, PNG, or WebP. Maximum size is configured by the server.',
    consent:
      'I understand this is general guidance. I will not format, delete partitions, or make risky changes without a backup.',
    submit: 'Generate safe diagnosis',
    loading: 'Analyzing…',
    error: 'Could not generate the diagnosis. Try again or contact Atlas PC Support.',
    how: 'How Atlas interprets the case',
    howItems: [
      'Likely causes with confidence level.',
      'Difficulty for a basic user and data-risk level.',
      'Safe, reversible, ordered first steps.',
      'When to stop and request professional support.',
    ],
    chat: 'Chat on WhatsApp',
    result: 'Initial result',
    case: 'Case',
    probability: 'Self-service probability',
    provider: 'Provider',
    before: 'Before touching anything',
    causes: 'Likely causes',
    confidence: 'Confidence',
    steps: 'Recommended steps',
    stop: 'Stop and request help if this appears',
    send: 'Send case to Atlas on WhatsApp',
    knowledge: 'Related Atlas runbooks',
  },
}

function App() {
  const [locale, setLocale] = useState<Locale>('es')
  const [operatingSystem, setOperatingSystem] = useState<OperatingSystem>('windows_11')
  const [linuxDistribution, setLinuxDistribution] = useState('')
  const [issueText, setIssueText] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [accepted, setAccepted] = useState(false)
  const [result, setResult] = useState<DiagnosticResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const text = copy[locale]

  const canSubmit = useMemo(
    () => accepted && issueText.trim().length >= 10 && !loading,
    [accepted, issueText, loading],
  )

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)

    const formData = new FormData()
    formData.append('operating_system', operatingSystem)
    formData.append('linux_distribution', linuxDistribution)
    formData.append('issue_text', issueText)
    formData.append('locale', locale)
    if (image) {
      formData.append('image', image)
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/diagnose`, {
        method: 'POST',
        body: formData,
      })
      if (!response.ok) {
        throw new Error(await response.text())
      }
      setResult((await response.json()) as DiagnosticResponse)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : text.error)
    } finally {
      setLoading(false)
    }
  }

  function handleWhatsAppClick() {
    fetch(`${API_BASE_URL}/api/events/whatsapp-click`, { method: 'POST' }).catch(() => undefined)
  }

  const whatsappUrl = result
    ? `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(result.whatsapp_prefill)}`
    : `https://wa.me/${WHATSAPP_NUMBER}`

  return (
    <main className="atlas-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">{text.eyebrow}</p>
          <h1>{text.title}</h1>
          <p className="hero-copy">{text.hero}</p>
          <div className="language-toggle" aria-label={text.language}>
            <span>{text.language}</span>
            <button className={locale === 'es' ? 'active' : ''} type="button" onClick={() => setLocale('es')}>
              ES
            </button>
            <button className={locale === 'en' ? 'active' : ''} type="button" onClick={() => setLocale('en')}>
              EN
            </button>
          </div>
        </div>
        <div className="trust-panel" aria-label="Safety summary">
          {text.trust.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>

      <section className="layout-grid">
        <form className="diagnostic-form" onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="operating-system">{text.os}</label>
            <select
              id="operating-system"
              value={operatingSystem}
              onChange={(event) => setOperatingSystem(event.target.value as OperatingSystem)}
            >
              {['Windows', 'Apple', 'Linux'].map((group) => (
                <optgroup key={group} label={group}>
                  {operatingSystems
                    .filter((os) => os.group === group)
                    .map((os) => (
                      <option key={os.value} value={os.value}>
                        {os.label}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </div>

          {operatingSystem === 'linux_other' && (
            <div className="field-group">
              <label htmlFor="linux-distribution">{text.linux}</label>
              <input
                id="linux-distribution"
                value={linuxDistribution}
                onChange={(event) => setLinuxDistribution(event.target.value)}
                placeholder={text.linuxPlaceholder}
              />
            </div>
          )}

          <div className="field-group">
            <label htmlFor="issue-text">{text.issue}</label>
            <textarea
              id="issue-text"
              value={issueText}
              onChange={(event) => setIssueText(event.target.value)}
              placeholder={text.issuePlaceholder}
              rows={8}
              maxLength={6000}
            />
            <small>
              {issueText.length}/6000 {text.chars}
            </small>
          </div>

          <div className="field-group">
            <label htmlFor="image">{text.image}</label>
            <input
              id="image"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => setImage(event.target.files?.[0] ?? null)}
            />
            <small>{text.imageHelp}</small>
          </div>

          <label className="consent-box">
            <input type="checkbox" checked={accepted} onChange={(event) => setAccepted(event.target.checked)} />
            <span>{text.consent}</span>
          </label>

          <button className="primary-button" type="submit" disabled={!canSubmit}>
            {loading ? text.loading : text.submit}
          </button>

          {error && <p className="error-box">{error}</p>}
        </form>

        <aside className="info-card">
          <h2>{text.how}</h2>
          <ol>
            {text.howItems.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
          <a className="secondary-button" href={`https://wa.me/${WHATSAPP_NUMBER}`} target="_blank" rel="noreferrer">
            {text.chat}
          </a>
        </aside>
      </section>

      {result && (
        <section className="result-card" aria-live="polite">
          <div className="result-header">
            <div>
              <p className="eyebrow">{text.result}</p>
              <h2>{result.summary}</h2>
              <p className="case-id">
                {text.case}: <strong>{result.case_id}</strong>
              </p>
            </div>
            <div className={`risk-badge risk-${result.difficulty}`}>{difficultyLabel[locale][result.difficulty]}</div>
          </div>

          <div className="score-grid">
            <div>
              <span>{text.probability}</span>
              <strong>{probabilityLabel[locale][result.self_service_probability]}</strong>
            </div>
            <div>
              <span>{text.provider}</span>
              <strong>{result.model_provider}</strong>
            </div>
          </div>

          <p className="risk-notice">{result.risk_notice}</p>

          <ResultSection title={text.before} items={result.before_touching} />

          {result.knowledge_matches.length > 0 && (
            <ResultSection title={text.knowledge} items={result.knowledge_matches} />
          )}

          <section className="nested-section">
            <h3>{text.causes}</h3>
            <div className="cause-list">
              {result.likely_causes.map((cause) => (
                <article key={`${cause.title}-${cause.confidence}`}>
                  <span className="confidence">
                    {text.confidence} {confidenceLabel[locale][cause.confidence]}
                  </span>
                  <h4>{cause.title}</h4>
                  <p>{cause.explanation}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="nested-section">
            <h3>{text.steps}</h3>
            <div className="step-list">
              {result.safe_steps.map((step, index) => (
                <article key={`${step.title}-${index}`}>
                  <span>{index + 1}</span>
                  <div>
                    <h4>{step.title}</h4>
                    <p>{step.detail}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="nested-section stop-section">
            <h3>{text.stop}</h3>
            {result.stop_and_contact.map((signal) => (
              <article key={signal.title}>
                <h4>{signal.title}</h4>
                <p>{signal.detail}</p>
              </article>
            ))}
          </section>

          <div className="cta-panel">
            <p>{result.customer_message}</p>
            <a
              className="primary-button"
              href={whatsappUrl}
              target="_blank"
              rel="noreferrer"
              onClick={handleWhatsAppClick}
            >
              {text.send}
            </a>
          </div>

          <p className="disclaimer">{result.disclaimer}</p>
        </section>
      )}
    </main>
  )
}

function ResultSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="nested-section">
      <h3>{title}</h3>
      <ul className="check-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  )
}

export default App
