import React, { useState } from 'react'
import { DiagnosticError, DiagnosticErrorType } from '@/types'
import {
  CheckCircle2,
  Copy,
  Check,
  Info,
  Layers,
  Zap,
} from 'lucide-react'

interface ErrorBreakdownProps {
  errors?: DiagnosticError[]
  cefrLevel?: string
  actionableTips?: string[]
  userText?: string
  className?: string
}

export function ErrorBreakdown({
  errors = [],
  cefrLevel,
  actionableTips = [],
  userText,
  className = '',
}: ErrorBreakdownProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [selectedErrorIndex, setSelectedErrorIndex] = useState<number | null>(null)

  const handleCopyCorrection = (text: string, index: number) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(index)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const getErrorTypeBadge = (type: DiagnosticErrorType) => {
    const t = (type || '').toLowerCase()
    switch (t) {
      case 'grammar':
        return {
          label: 'Grammar',
          classes: 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800',
        }
      case 'collocation':
        return {
          label: 'Collocation',
          classes: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/50 dark:text-purple-300 dark:border-purple-800',
        }
      case 'semantic':
        return {
          label: 'Semantic',
          classes: 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800',
        }
      case 'tone':
        return {
          label: 'Tone & Register',
          classes: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800',
        }
      case 'spelling':
        return {
          label: 'Spelling',
          classes: 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/50 dark:text-sky-300 dark:border-sky-800',
        }
      default:
        return {
          label: type || 'Linguistic',
          classes: 'bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
        }
    }
  }

  const getSeverityBadge = (severity: string) => {
    const s = (severity || '').toLowerCase()
    switch (s) {
      case 'high':
        return {
          label: 'High Severity',
          classes: 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300',
        }
      case 'medium':
        return {
          label: 'Moderate',
          classes: 'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/40 dark:text-amber-300',
        }
      case 'low':
      default:
        return {
          label: 'Minor',
          classes: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300',
        }
    }
  }

  const getCefrDescription = (level?: string) => {
    const l = (level || 'B1').toUpperCase()
    switch (l) {
      case 'A1':
        return 'A1 · Beginner Level'
      case 'A2':
        return 'A2 · Elementary Level'
      case 'B1':
        return 'B1 · Intermediate Threshold'
      case 'B2':
        return 'B2 · Upper-Intermediate Fluency'
      case 'C1':
        return 'C1 · Advanced Effective Proficiency'
      case 'C2':
        return 'C2 · Mastery / Native-like Range'
      default:
        return `${level} · CEFR Aligned`
    }
  }

  // Render highlighted text with error spans
  const renderHighlightedText = () => {
    if (!userText || errors.length === 0) return null

    // Find all error matches in the user text
    interface SpanMatch {
      start: number
      end: number
      errorIndex: number
      error: DiagnosticError
    }

    const matches: SpanMatch[] = []
    errors.forEach((err, idx) => {
      if (!err.original_text) return
      const escaped = err.original_text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(escaped, 'gi')
      let match
      while ((match = regex.exec(userText)) !== null) {
        matches.push({
          start: match.index,
          end: match.index + match[0].length,
          errorIndex: idx,
          error: err,
        })
      }
    })

    // Sort matches by start position
    matches.sort((a, b) => a.start - b.start)

    // Build segments without overlapping conflicts
    const segments: React.ReactNode[] = []
    let lastIndex = 0

    matches.forEach((m, i) => {
      if (m.start < lastIndex) return // Skip overlapping match

      // Text before error
      if (m.start > lastIndex) {
        segments.push(
          <span key={`text-${i}`}>{userText.substring(lastIndex, m.start)}</span>
        )
      }

      // Highlighted error span
      const isSelected = selectedErrorIndex === m.errorIndex
      const errorText = userText.substring(m.start, m.end)

      segments.push(
        <mark
          key={`err-${i}`}
          onClick={() =>
            setSelectedErrorIndex(isSelected ? null : m.errorIndex)
          }
          className={`px-1.5 py-0.5 rounded cursor-pointer transition-all border font-medium ${
            isSelected
              ? 'bg-amber-200 dark:bg-amber-900/60 border-amber-400 dark:border-amber-600 ring-2 ring-amber-400'
              : 'bg-red-50 text-red-900 dark:bg-red-950/60 dark:text-red-200 border-red-200 dark:border-red-800 hover:bg-red-100'
          }`}
          title={`Error: ${m.error.explanation} (Click to inspect)`}
        >
          {errorText}
        </mark>
      )

      lastIndex = m.end
    })

    if (lastIndex < userText.length) {
      segments.push(
        <span key="text-end">{userText.substring(lastIndex)}</span>
      )
    }

    return (
      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-sm leading-relaxed text-slate-800 dark:text-slate-200 font-sans">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5" />
          <span>Highlighted Response Analysis</span>
        </div>
        <div>"{segments}"</div>
      </div>
    )
  }

  return (
    <div className={`space-y-4 ${className}`} data-testid="error-breakdown">
      {/* Header Bar with CEFR Level */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
            Linguistic Diagnostics & Error Breakdown
          </h3>
          {errors.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              {errors.length} {errors.length === 1 ? 'diagnostic error' : 'diagnostic errors'}
            </span>
          )}
        </div>

        {cefrLevel && (
          <div className="flex items-center gap-1.5 self-start sm:self-center">
            <span className="text-xs text-slate-500 font-medium">Estimated Proficiency:</span>
            <span
              className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800"
              title={getCefrDescription(cefrLevel)}
            >
              CEFR {cefrLevel.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Render Text Highlight Span if userText provided */}
      {renderHighlightedText()}

      {/* No Errors Clean State */}
      {errors.length === 0 && (
        <div
          data-testid="no-errors-state"
          className="p-5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-900/40 flex items-start gap-3.5"
        >
          <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-emerald-900 dark:text-emerald-300">
              No Linguistic Errors Detected
            </div>
            <p className="text-xs text-emerald-800/80 dark:text-emerald-300/80 mt-0.5 leading-relaxed">
              Your response demonstrated accurate grammar syntax, natural collocation pairings, appropriate tone, and correct spelling.
            </p>
          </div>
        </div>
      )}

      {/* Error Cards List */}
      {errors.length > 0 && (
        <div className="space-y-3" data-testid="errors-list">
          {errors.map((err, idx) => {
            const typeBadge = getErrorTypeBadge(err.error_type)
            const sevBadge = getSeverityBadge(err.severity)
            const isSelected = selectedErrorIndex === idx

            return (
              <div
                key={idx}
                onClick={() => setSelectedErrorIndex(isSelected ? null : idx)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-amber-50/40 dark:bg-amber-950/20 border-amber-300 dark:border-amber-700 shadow-sm'
                    : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                {/* Badges Bar */}
                <div className="flex items-center justify-between gap-2 mb-2.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${typeBadge.classes}`}
                    >
                      {typeBadge.label}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${sevBadge.classes}`}
                    >
                      {sevBadge.label}
                    </span>
                  </div>

                  <span className="text-[11px] text-slate-400 font-mono">
                    #{idx + 1}
                  </span>
                </div>

                {/* Error Span & Correction Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mb-2.5">
                  {/* Original Error Span */}
                  <div className="p-2.5 rounded-lg bg-red-50/70 dark:bg-red-950/30 border border-red-100 dark:border-red-900/40 text-xs">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-red-700 dark:text-red-400 block mb-1">
                      Original Text / Span
                    </span>
                    <span className="font-semibold text-red-900 dark:text-red-200 line-through decoration-red-400">
                      "{err.original_text}"
                    </span>
                  </div>

                  {/* Suggested Correction */}
                  <div className="p-2.5 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/40 text-xs flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 block mb-1">
                        Suggested Correction
                      </span>
                      <span className="font-bold text-emerald-950 dark:text-emerald-200">
                        "{err.suggested_correction}"
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCopyCorrection(err.suggested_correction, idx)
                      }}
                      title="Copy correction"
                      className="p-1 rounded text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors"
                    >
                      {copiedIndex === idx ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Linguistic Explanation */}
                <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                  {err.explanation}
                </p>
              </div>
            )
          })}
        </div>
      )}

      {/* Actionable Linguistic Recommendations */}
      {actionableTips && actionableTips.length > 0 && (
        <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30 space-y-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <h4 className="text-xs font-bold text-indigo-950 dark:text-indigo-200 uppercase tracking-wider">
              Actionable Linguistic Recommendations
            </h4>
          </div>

          <ul className="space-y-1.5 pl-5 list-disc text-xs text-indigo-950 dark:text-indigo-200 leading-relaxed">
            {actionableTips.map((tip, idx) => (
              <li key={idx}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ErrorBreakdown
