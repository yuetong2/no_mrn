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
      <h1>🔒 MRN/NRIC Masking Tool</h1>
      <p className="subtitle">
        Upload an image containing medical record numbers or identification numbers. 
        We'll automatically detect and mask them for privacy protection.
      </p>

      <div className={`upload-area ${file ? 'has-file' : ''}`}>
        <div className="file-input-wrapper">
          <input 
            type="file" 
            accept="image/*" 
            onChange={onSelect}
            id="file-input"
          />
          <label htmlFor="file-input" className="file-input-label">
            <svg className="upload-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span>
              {file ? 'Click to change file' : 'Click to upload or drag and drop'}
            </span>
            <span style={{ fontSize: '0.85rem', color: '#a0aec0' }}>
              PNG, JPG, JPEG up to 10MB
            </span>
          </label>
        </div>
      </div>

      {file && (
        <div className="file-info">
          <svg className="file-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <div>
            <strong>{file.name}</strong>
            <div style={{ fontSize: '0.85rem', color: '#718096' }}>
              {(file.size / 1024).toFixed(1)} KB
            </div>
          </div>
        </div>
      )}

      <button disabled={!file || loading} onClick={onUpload}>
        {loading ? (
          <>
            <span className="spinner"></span>
            <span style={{ marginLeft: '0.5rem' }}>Processing...</span>
          </>
        ) : (
          'Upload & Mask'
        )}
      </button>

      {typeof maskedCount === 'number' && (
        <div className="result-box success">
          <svg className="result-icon" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          <div>
            <strong>Success!</strong> Masked {maskedCount} region{maskedCount !== 1 ? 's' : ''}.
            <div style={{ fontSize: '0.9rem', marginTop: '0.25rem' }}>
              Your file has been downloaded.
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="result-box error">
          <svg className="result-icon" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <div>
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
