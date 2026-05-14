import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

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
  { value: 'linux_other', label: 'Otra distro Linux', group: 'Linux' },
]

const difficultyLabel: Record<Difficulty, string> = {
  basic: 'Básico',
  intermediate: 'Intermedio',
  advanced: 'Avanzado',
  data_risk: 'Riesgo de datos',
}

const probabilityLabel: Record<Probability, string> = {
  high: 'Alta',
  medium: 'Media',
  low: 'Baja',
}

function App() {
  const [operatingSystem, setOperatingSystem] = useState<OperatingSystem>('windows_11')
  const [linuxDistribution, setLinuxDistribution] = useState('')
  const [issueText, setIssueText] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [accepted, setAccepted] = useState(false)
  const [result, setResult] = useState<DiagnosticResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

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
    formData.append('locale', 'es')
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
      setError(
        caught instanceof Error
          ? caught.message
          : 'No se pudo generar el diagnóstico. Intenta otra vez o contacta a Atlas PC Support.',
      )
    } finally {
      setLoading(false)
    }
  }

  const whatsappUrl = result
    ? `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(result.whatsapp_prefill)}`
    : `https://wa.me/${WHATSAPP_NUMBER}`

  return (
    <main className="atlas-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">Atlas PC Support</p>
          <h1>Asistente de Diagnóstico IA</h1>
          <p className="hero-copy">
            Describe el error, adjunta una captura opcional y recibe un triaje seguro antes de tocar tu PC.
          </p>
        </div>
        <div className="trust-panel" aria-label="Resumen de seguridad">
          <span>Sin cuenta</span>
          <span>Pasos seguros primero</span>
          <span>CTA a soporte si hay riesgo</span>
        </div>
      </section>

      <section className="layout-grid">
        <form className="diagnostic-form" onSubmit={handleSubmit}>
          <div className="field-group">
            <label htmlFor="operating-system">Sistema operativo</label>
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
              <label htmlFor="linux-distribution">Distro Linux</label>
              <input
                id="linux-distribution"
                value={linuxDistribution}
                onChange={(event) => setLinuxDistribution(event.target.value)}
                placeholder="Ej. openSUSE, Pop!_OS, Zorin OS"
              />
            </div>
          )}

          <div className="field-group">
            <label htmlFor="issue-text">Texto del error o explicación</label>
            <textarea
              id="issue-text"
              value={issueText}
              onChange={(event) => setIssueText(event.target.value)}
              placeholder="Ej. Mi laptop muestra pantalla azul con código CRITICAL_PROCESS_DIED después de actualizar Windows..."
              rows={8}
              maxLength={6000}
            />
            <small>{issueText.length}/6000 caracteres</small>
          </div>

          <div className="field-group">
            <label htmlFor="image">Foto o captura opcional</label>
            <input
              id="image"
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(event) => setImage(event.target.files?.[0] ?? null)}
            />
            <small>JPG, PNG o WebP. Máximo configurado por el servidor.</small>
          </div>

          <label className="consent-box">
            <input
              type="checkbox"
              checked={accepted}
              onChange={(event) => setAccepted(event.target.checked)}
            />
            <span>
              Entiendo que esto es orientación general. No haré formateos, borrado de particiones ni cambios
              riesgosos sin respaldo.
            </span>
          </label>

          <button className="primary-button" type="submit" disabled={!canSubmit}>
            {loading ? 'Analizando…' : 'Generar diagnóstico seguro'}
          </button>

          {error && <p className="error-box">{error}</p>}
        </form>

        <aside className="info-card">
          <h2>Cómo interpreta Atlas el caso</h2>
          <ol>
            <li>Causas probables con nivel de confianza.</li>
            <li>Dificultad para usuario básico y riesgo de datos.</li>
            <li>Pasos seguros, reversibles y ordenados.</li>
            <li>Cuándo parar y pedir soporte profesional.</li>
          </ol>
          <a className="secondary-button" href={`https://wa.me/${WHATSAPP_NUMBER}`} target="_blank" rel="noreferrer">
            Hablar por WhatsApp
          </a>
        </aside>
      </section>

      {result && (
        <section className="result-card" aria-live="polite">
          <div className="result-header">
            <div>
              <p className="eyebrow">Resultado inicial</p>
              <h2>{result.summary}</h2>
            </div>
            <div className={`risk-badge risk-${result.difficulty}`}>
              {difficultyLabel[result.difficulty]}
            </div>
          </div>

          <div className="score-grid">
            <div>
              <span>Probabilidad autoservicio</span>
              <strong>{probabilityLabel[result.self_service_probability]}</strong>
            </div>
            <div>
              <span>Proveedor</span>
              <strong>{result.model_provider}</strong>
            </div>
          </div>

          <p className="risk-notice">{result.risk_notice}</p>

          <ResultSection title="Antes de tocar nada" items={result.before_touching} />

          <section className="nested-section">
            <h3>Causas probables</h3>
            <div className="cause-list">
              {result.likely_causes.map((cause) => (
                <article key={`${cause.title}-${cause.confidence}`}>
                  <span className="confidence">Confianza {cause.confidence}</span>
                  <h4>{cause.title}</h4>
                  <p>{cause.explanation}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="nested-section">
            <h3>Pasos recomendados</h3>
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
            <h3>Detente y pide ayuda si aparece esto</h3>
            {result.stop_and_contact.map((signal) => (
              <article key={signal.title}>
                <h4>{signal.title}</h4>
                <p>{signal.detail}</p>
              </article>
            ))}
          </section>

          <div className="cta-panel">
            <p>{result.customer_message}</p>
            <a className="primary-button" href={whatsappUrl} target="_blank" rel="noreferrer">
              Enviar caso a Atlas por WhatsApp
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
