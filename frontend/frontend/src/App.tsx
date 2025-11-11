import { useState } from 'react'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [maskedCount, setMaskedCount] = useState<number | null>(null)

  const onSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    setMaskedCount(null)
    const f = e.target.files?.[0] ?? null
    setFile(f)
  }

  const onUpload = async () => {
    if (!file) {
      setError('Please choose an image first')
      return
    }
    setLoading(true)
    setError(null)
    setMaskedCount(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${BACKEND_URL}/mask`, {
        method: 'POST',
        body: form,
      })
      if (!res.ok) {
        const maybeJson = await res
          .clone()
          .json()
          .catch(() => null as any)
        throw new Error(maybeJson?.detail || maybeJson?.error || `Upload failed (${res.status})`)
      }
      const blob = await res.blob()
      const countHeader = res.headers.get('X-Masked-Count')
      setMaskedCount(countHeader ? parseInt(countHeader) : null)

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      const base = file.name.replace(/\.[^.]+$/, '')
      a.href = url
      a.download = `masked_${base}.jpg`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      setError(e.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Mask NRIC/MRN in Image</h1>
      <p>Choose an image. We will detect and mask identifiers, then return a new image for download.</p>

      <div className="controls">
        <input type="file" accept="image/*" onChange={onSelect} />
        <button disabled={!file || loading} onClick={onUpload}>
          {loading ? 'Processing…' : 'Upload & Mask'}
        </button>
      </div>

      {file && (
        <p>
          Selected: <strong>{file.name}</strong>
        </p>
      )}

      {typeof maskedCount === 'number' && (
        <p>Masked regions: {maskedCount}</p>
      )}

      {error && <p className="error">{error}</p>}
    </div>
  )
}

export default App
