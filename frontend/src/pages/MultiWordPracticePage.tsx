import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Layers,
  Sparkles,
  CheckCircle2,
  ArrowRight,
  RefreshCw,
  Send,
  AlertCircle,
  HelpCircle,
  Trophy,
  ArrowLeft,
  Plus,
  BookOpen,
} from 'lucide-react'
import { practiceApi } from '@/api/practice'
import {
  MultiWordStartResponse,
  MultiWordAttemptResponse,
  MultiWordEligibleResponse,
  MultiWordTargetWord,
  WordEvaluationDetail,
} from '@/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'

export const MultiWordPracticePage: React.FC = () => {
  const navigate = useNavigate()

  // State
  const [eligibility, setEligibility] = useState<MultiWordEligibleResponse | null>(null)
  const [session, setSession] = useState<MultiWordStartResponse | null>(null)
  const [response, setResponse] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [evaluation, setEvaluation] = useState<MultiWordAttemptResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load eligibility & initialize
  const checkEligibilityAndStart = async () => {
    try {
      setLoading(true)
      setError(null)
      setEvaluation(null)
      setResponse('')

      const eligibleData = await practiceApi.getMultiWordEligible()
      setEligibility(eligibleData)

      if (eligibleData.is_eligible || eligibleData.total_words >= 3) {
        const startRes = await practiceApi.startMultiWord()
        setSession(startRes)
      } else {
        setSession(null)
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to start multi-word practice')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkEligibilityAndStart()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!session || !response.trim() || submitting) return

    try {
      setSubmitting(true)
      setError(null)
      const evalRes = await practiceApi.submitMultiWord(session.session_id, response.trim())
      setEvaluation(evalRes)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to evaluate response')
    } finally {
      setSubmitting(false)
    }
  }

  const handleInsertWord = (word: string) => {
    setResponse((prev) => {
      const trimmed = prev.trim()
      return trimmed ? `${trimmed} ${word} ` : `${word} `
    })
  }

  // Real-time detection of target words in response text
  const isWordUsedInText = (word: string): boolean => {
    if (!response.trim()) return false
    const lower = response.toLowerCase()
    const wordLower = word.toLowerCase()
    const stem = wordLower.slice(0, Math.min(4, wordLower.length))
    return lower.includes(wordLower) || lower.includes(stem)
  }

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center min-h-[60vh] space-y-4">
        <LoadingSpinner size="lg" />
        <p className="text-sm text-slate-500 font-medium">
          Generating realistic multi-word practice scenario...
        </p>
      </div>
    )
  }

  // Insufficient Words State
  if (eligibility && !eligibility.is_eligible && eligibility.total_words < 3) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-10 space-y-6">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/daily')}
          className="gap-2 text-slate-500"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Daily Routine
        </Button>

        <Card className="border-purple-200 dark:border-purple-900/40 bg-gradient-to-br from-purple-50/50 via-white to-indigo-50/30 dark:from-slate-900 dark:to-purple-950/20 shadow-lg text-center p-8">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-purple-100 dark:bg-purple-900/40 text-purple-600 dark:text-purple-400 flex items-center justify-center mb-4">
            <Layers className="w-8 h-8" />
          </div>

          <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white">
            Unlock "Use My Vocabulary"
          </h2>

          <p className="text-slate-600 dark:text-slate-300 max-w-lg mx-auto text-sm mt-2">
            "Use My Vocabulary" challenges you to synthesize <strong>3–5 active vocabulary words</strong> into a single cohesive response.
            You currently have <strong>{eligibility.eligible_count} of 3</strong> required words in practiced status.
          </p>

          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <Button
              variant="primary"
              onClick={() => navigate('/practice')}
              className="gap-2 bg-purple-600 hover:bg-purple-700 text-white font-bold"
            >
              <Sparkles className="w-4 h-4" />
              Practice Single Words
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/vocabulary')}
              className="gap-2"
            >
              <BookOpen className="w-4 h-4" />
              Learn New Words
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  if (error && !session) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ErrorState
          title="Could not start Multi-Word Practice"
          message={error}
          onRetry={checkEligibilityAndStart}
        />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/daily')}
          className="gap-2 text-slate-500"
        >
          <ArrowLeft className="w-4 h-4" />
          Daily Routine
        </Button>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={checkEligibilityAndStart}
            disabled={submitting}
            className="gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Scenario
          </Button>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-0.5 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-200 text-xs font-bold uppercase tracking-wider mb-2">
            <Layers className="w-3.5 h-3.5" />
            Synthesis Practice • Use My Vocabulary
          </div>
          <h1 className="text-2xl sm:text-3xl font-black">
            Multi-Word Contextual Challenge
          </h1>
          <p className="text-purple-200 text-sm mt-1">
            Weave all designated target words naturally into your written response to build active fluency.
          </p>
        </div>

        <div className="bg-white/10 px-4 py-3 rounded-xl border border-white/10 flex items-center gap-3 shrink-0">
          <Trophy className="w-6 h-6 text-amber-400" />
          <div>
            <div className="text-[10px] text-purple-200 font-bold uppercase tracking-wider">Reward</div>
            <div className="text-sm font-bold text-white">+20 XP on Success</div>
          </div>
        </div>
      </div>

      {session && (
        <div className="space-y-6">
          {/* Target Words Highlight Strip */}
          <Card className="border-purple-100 dark:border-purple-900/40 bg-purple-50/40 dark:bg-purple-950/20">
            <CardContent className="p-4 sm:p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                <div className="text-xs font-bold uppercase tracking-wider text-purple-800 dark:text-purple-300 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-purple-600" />
                  Target Vocabulary Words ({session.target_words.length})
                </div>
                <div className="text-xs text-slate-500">
                  Click a word or button to insert it into your response
                </div>
              </div>

              <div className="flex flex-wrap gap-2.5">
                {session.target_words.map((tw: MultiWordTargetWord) => {
                  const used = isWordUsedInText(tw.word)
                  return (
                    <div
                      key={tw.id}
                      className={`group inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border text-sm font-semibold transition-all shadow-sm ${
                        used
                          ? 'bg-emerald-50 border-emerald-300 text-emerald-900 dark:bg-emerald-950/50 dark:border-emerald-700 dark:text-emerald-200 ring-2 ring-emerald-500/20'
                          : 'bg-white border-purple-200 text-purple-950 dark:bg-slate-900 dark:border-purple-800 dark:text-purple-100 hover:border-purple-400'
                      }`}
                    >
                      <span>{tw.word}</span>
                      {tw.cefr_level && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 font-bold">
                          {tw.cefr_level}
                        </span>
                      )}
                      {used ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleInsertWord(tw.word)}
                          title="Insert word into response"
                          className="opacity-60 hover:opacity-100 text-purple-600 dark:text-purple-400"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Scenario Box */}
          <Card className="border-slate-200 dark:border-slate-800 shadow-md">
            <CardHeader className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-800 py-3.5">
              <CardTitle className="text-base font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-600" />
                The Communication Scenario
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="text-slate-900 dark:text-slate-100 text-base leading-relaxed">
                {session.scenario.situation}
              </div>

              <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40 text-sm text-indigo-950 dark:text-indigo-200 space-y-1">
                <div className="font-bold text-indigo-900 dark:text-indigo-300">
                  Your Task:
                </div>
                <div>{session.scenario.prompt}</div>
              </div>

              {session.scenario.context_hint && (
                <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 italic">
                  <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span>Tip: {session.scenario.context_hint}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Response Form */}
          {!evaluation && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between items-center text-xs font-semibold text-slate-500">
                  <span>Your Written Response</span>
                  <span>
                    Words Used:{' '}
                    {session.target_words.filter((w) => isWordUsedInText(w.word)).length} /{' '}
                    {session.target_words.length}
                  </span>
                </div>

                <textarea
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                  placeholder="Type your response here using all target vocabulary words..."
                  rows={6}
                  disabled={submitting}
                  className="w-full p-4 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all resize-y text-base font-normal placeholder:text-slate-400"
                />
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex items-center justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setResponse('')}
                  disabled={!response || submitting}
                >
                  Clear
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  disabled={!response.trim() || submitting}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-bold gap-2 shadow-md shadow-purple-900/20"
                >
                  {submitting ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Evaluating Multi-Word Response...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Submit & Evaluate</span>
                    </>
                  )}
                </Button>
              </div>
            </form>
          )}

          {/* Evaluation Results Section */}
          {evaluation && (
            <div className="space-y-6 animate-in fade-in duration-300">
              {/* Overall Evaluation Card */}
              <Card
                className={`border shadow-lg ${
                  evaluation.is_successful
                    ? 'border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/20 dark:bg-emerald-950/10'
                    : 'border-amber-200 dark:border-amber-900/50 bg-amber-50/20 dark:bg-amber-950/10'
                }`}
              >
                <CardHeader className="py-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      {evaluation.is_successful ? (
                        <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 flex items-center justify-center">
                          <CheckCircle2 className="w-6 h-6" />
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-600 flex items-center justify-center">
                          <AlertCircle className="w-6 h-6" />
                        </div>
                      )}
                      <div>
                        <CardTitle className="text-lg font-black">
                          {evaluation.is_successful
                            ? 'Synthesis Success!'
                            : 'Good Attempt — Needs Refinement'}
                        </CardTitle>
                        <p className="text-xs text-slate-500">
                          {evaluation.is_successful
                            ? `Earned +${evaluation.xp_earned} XP towards your daily goal and level progression.`
                            : 'Earned +5 XP for practicing. Try again to lock in full mastery.'}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-3xl font-black text-slate-900 dark:text-white">
                        {evaluation.scores.overall}
                        <span className="text-base font-normal text-slate-400">/10</span>
                      </div>
                      <div className="text-[10px] uppercase font-bold text-slate-400">Overall Score</div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="p-6 space-y-6">
                  {/* Score Breakdown Bars */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xs text-slate-500 font-semibold">Vocabulary</div>
                      <div className="text-xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                        {evaluation.scores.vocabulary_usage}/10
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xs text-slate-500 font-semibold">Grammar</div>
                      <div className="text-xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                        {evaluation.scores.grammar}/10
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xs text-slate-500 font-semibold">Context</div>
                      <div className="text-xl font-bold text-indigo-600 dark:text-indigo-400 mt-1">
                        {evaluation.scores.context}/10
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-center">
                      <div className="text-xs text-slate-500 font-semibold">Naturalness</div>
                      <div className="text-xl font-bold text-emerald-600 dark:text-emerald-400 mt-1">
                        {evaluation.scores.naturalness}/10
                      </div>
                    </div>
                  </div>

                  {/* Overall Feedback */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Linguistic Feedback
                    </h4>
                    <p className="text-slate-800 dark:text-slate-200 text-sm leading-relaxed bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                      {evaluation.feedback}
                    </p>
                  </div>

                  {/* Individual Target Word Evaluations */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Individual Target Word Breakdown
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {evaluation.word_evaluations.map((we: WordEvaluationDetail, idx: number) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 shadow-sm"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-base text-slate-900 dark:text-white capitalize">
                              {we.word}
                            </span>
                            <div className="flex items-center gap-1.5">
                              <span
                                className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                                  we.used
                                    ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                                    : 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300'
                                }`}
                              >
                                {we.used ? 'Used' : 'Missed'}
                              </span>
                              {we.used_correctly && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 uppercase">
                                  Correct
                                </span>
                              )}
                              {we.score !== undefined && we.score !== null && (
                                <span className="text-xs font-black text-slate-600 dark:text-slate-300 ml-1">
                                  {we.score}/10
                                </span>
                              )}
                            </div>
                          </div>
                          <p className="text-xs text-slate-600 dark:text-slate-400">
                            {we.feedback}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Polished Improved Version */}
                  {evaluation.improved_version && (
                    <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40 space-y-1.5">
                      <div className="text-xs font-bold uppercase tracking-wider text-indigo-900 dark:text-indigo-300 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        Polished Native-Speaker Alternative
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 text-sm italic">
                        "{evaluation.improved_version}"
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEvaluation(null)
                        setResponse('')
                      }}
                    >
                      Retry This Scenario
                    </Button>

                    <div className="flex items-center gap-3">
                      <Button
                        variant="secondary"
                        onClick={() => navigate('/daily')}
                      >
                        Return to Daily Plan
                      </Button>
                      <Button
                        variant="primary"
                        onClick={checkEligibilityAndStart}
                        className="bg-purple-600 hover:bg-purple-700 text-white font-bold gap-2"
                      >
                        <span>Next Scenario</span>
                        <ArrowRight className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
export default MultiWordPracticePage
