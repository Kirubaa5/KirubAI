import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reviewsApi } from '@/api/reviews'
import { DueReviewItem, ReviewSubmitResponse } from '@/types'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import {
  Brain,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ArrowRight,
  Sparkles,
  Send,
  BookOpen,
  Calendar,
  Award,
  TrendingUp,
} from 'lucide-react'

export function ReviewsPage() {
  const queryClient = useQueryClient()

  // Review Queue state
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userResponse, setUserResponse] = useState('')
  const [showHint, setShowHint] = useState(false)
  const [lastSubmission, setLastSubmission] = useState<ReviewSubmitResponse | null>(null)
  const [inputError, setInputError] = useState<string | null>(null)
  const [completedReviewsCount, setCompletedReviewsCount] = useState(0)
  const [successfulRecallsCount, setSuccessfulRecallsCount] = useState(0)
  const [totalXpEarned, setTotalXpEarned] = useState(0)
  const [isQueueFinished, setIsQueueFinished] = useState(false)

  // Fetch Due Reviews
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['reviews-due'],
    queryFn: () => reviewsApi.getDue(50),
  })

  const dueItems: DueReviewItem[] = data?.items || []
  const currentItem = dueItems[currentIndex]

  // Review Submission Mutation
  const submitMutation = useMutation({
    mutationFn: ({ vocabId, responseText }: { vocabId: string; responseText: string }) =>
      reviewsApi.submit(vocabId, responseText, 'recall'),
    onSuccess: (result) => {
      setLastSubmission(result)
      setCompletedReviewsCount((prev) => prev + 1)
      if (result.recall_successful) {
        setSuccessfulRecallsCount((prev) => prev + 1)
      }
      setTotalXpEarned((prev) => prev + result.xp_earned)

      queryClient.invalidateQueries({ queryKey: ['vocabulary'] })
      queryClient.invalidateQueries({ queryKey: ['reviews-due'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!currentItem) return

    const trimmed = userResponse.trim()
    if (!trimmed) {
      setInputError('Please enter your recalled word before submitting.')
      return
    }

    setInputError(null)
    submitMutation.mutate({
      vocabId: currentItem.vocabulary_id,
      responseText: trimmed,
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSubmit(e)
    }
  }

  const handleNextWord = () => {
    if (currentIndex + 1 < dueItems.length) {
      setCurrentIndex((prev) => prev + 1)
      setUserResponse('')
      setShowHint(false)
      setLastSubmission(null)
      setInputError(null)
    } else {
      setIsQueueFinished(true)
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <LoadingSpinner size="lg" className="text-purple-600 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-1">Loading Review Queue</h2>
        <p className="text-sm text-gray-500">Checking your spaced repetition schedule...</p>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto">
          <ErrorState
            title="Failed to load review queue"
            message="We could not fetch your scheduled reviews. Please try again."
            onRetry={() => refetch()}
          />
        </div>
      </div>
    )
  }

  // Empty Queue / All Caught Up State
  if (dueItems.length === 0 && !isQueueFinished) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <EmptyState
            icon={<Brain className="h-14 w-14 text-purple-600" />}
            title="You're All Caught Up!"
            message="No vocabulary words are due for spaced repetition review right now. Words will appear here automatically when they are ready for retention review."
            action={
              <div className="flex flex-col sm:flex-row gap-3 mt-6">
                <Link to="/vocabulary">
                  <Button variant="outline" className="w-full sm:w-auto flex items-center gap-2">
                    <BookOpen className="h-4 w-4" />
                    Browse Vocabulary
                  </Button>
                </Link>
                <Link to="/vocabulary">
                  <Button className="w-full sm:w-auto flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Practice New Words
                  </Button>
                </Link>
              </div>
            }
          />
        </div>
      </div>
    )
  }

  // Completed Session State
  if (isQueueFinished) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <Card className="border-purple-200 bg-gradient-to-b from-purple-50/60 via-white to-white shadow-md text-center p-8">
            <div className="inline-flex p-4 bg-purple-100 text-purple-700 rounded-full mb-4">
              <Award className="h-10 w-10" />
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 mb-2">
              Review Session Complete!
            </h1>
            <p className="text-sm text-gray-600 max-w-md mx-auto mb-6">
              You’ve strengthened your memory pathways and solidified active recall.
            </p>

            <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto mb-8">
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
                <span className="text-[11px] font-bold text-gray-500 uppercase block">Reviewed</span>
                <span className="text-2xl font-black text-gray-900">{completedReviewsCount}</span>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
                <span className="text-[11px] font-bold text-gray-500 uppercase block">Recalled</span>
                <span className="text-2xl font-black text-emerald-600">
                  {successfulRecallsCount}
                </span>
              </div>
              <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-xs">
                <span className="text-[11px] font-bold text-gray-500 uppercase block">XP Earned</span>
                <span className="text-2xl font-black text-purple-600">+{totalXpEarned}</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link to="/vocabulary">
                <Button className="w-full sm:w-auto flex items-center gap-2">
                  <BookOpen className="h-4 w-4" />
                  Back to Vocabulary
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    )
  }

  const prompt = currentItem.prompt
  const progressPercent = Math.round(((currentIndex + 1) / dueItems.length) * 100)

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header & Progress */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-purple-100 text-purple-700 rounded-lg">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Spaced Repetition Review</h1>
                <p className="text-xs text-gray-500">Active recall memory training</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-purple-100 text-purple-800">
                Word {currentIndex + 1} of {dueItems.length}
              </span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-purple-600 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Active Recall Challenge Card */}
        <Card className="mb-6 border-purple-100 shadow-sm bg-white overflow-hidden">
          <CardHeader className="bg-purple-50/50 border-b border-purple-100/60 py-3.5 px-6">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs sm:text-sm font-bold text-purple-950 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-600" />
                Active Recall Challenge
              </CardTitle>
              <div className="flex items-center gap-2">
                {prompt.part_of_speech && (
                  <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-white text-purple-700 border border-purple-200">
                    {prompt.part_of_speech}
                  </span>
                )}
                {prompt.context_label && (
                  <span className="text-[11px] font-medium text-gray-600 bg-white px-2 py-0.5 rounded border border-gray-200">
                    {prompt.context_label}
                  </span>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="p-6 space-y-5">
            {/* Definition */}
            {prompt.definition && (
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400 block mb-1">
                  Meaning / Definition
                </span>
                <p className="text-lg sm:text-xl font-semibold text-gray-900 leading-snug">
                  "{prompt.definition}"
                </p>
              </div>
            )}

            {/* Cloze Sentence */}
            {prompt.cloze_sentence && (
              <div className="bg-gray-50 border border-gray-200/80 rounded-xl p-4">
                <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 block mb-1.5">
                  Contextual Fill-in-the-Blank
                </span>
                <p className="text-base text-gray-800 font-medium leading-relaxed">
                  "{prompt.cloze_sentence}"
                </p>
              </div>
            )}

            {/* Hint Box (Collapsible) */}
            <div>
              {!showHint ? (
                <button
                  type="button"
                  onClick={() => setShowHint(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-600 hover:text-purple-800 transition-colors"
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                  Need a hint? (Show clue)
                </button>
              ) : (
                <div className="bg-amber-50/80 border border-amber-200 rounded-lg p-3 text-xs text-amber-900 space-y-1 animate-fadeIn">
                  <div className="font-semibold flex items-center gap-1">
                    <HelpCircle className="h-3.5 w-3.5 text-amber-600" />
                    Memory Clue:
                  </div>
                  <p>{prompt.hint || 'Think about the meaning and context above.'}</p>
                  {prompt.synonyms_hint && prompt.synonyms_hint.length > 0 && (
                    <p className="text-amber-800">
                      <span className="font-medium">Related words: </span>
                      {prompt.synonyms_hint.join(', ')}
                    </p>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Submitting Loading State */}
        {submitMutation.isPending && (
          <Card className="mb-6 border-purple-200 bg-white shadow-sm p-6 text-center animate-pulse">
            <LoadingSpinner size="md" className="mx-auto mb-2 text-purple-600" />
            <p className="text-sm font-semibold text-gray-800">Evaluating your recall...</p>
          </Card>
        )}

        {/* Answer Input Form (Shown before submission) */}
        {!lastSubmission && !submitMutation.isPending && (
          <Card className="mb-6 border-gray-200 shadow-sm bg-white">
            <CardContent className="p-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label
                    htmlFor="recall-input"
                    className="text-sm font-bold text-gray-900 block mb-1.5"
                  >
                    What is the English word?
                  </label>
                  <div className="relative">
                    <input
                      id="recall-input"
                      type="text"
                      value={userResponse}
                      onChange={(e) => {
                        setUserResponse(e.target.value)
                        if (inputError) setInputError(null)
                      }}
                      onKeyDown={handleKeyDown}
                      placeholder="Type the target word here..."
                      className="w-full rounded-lg border border-gray-300 p-3.5 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent transition-all shadow-inner"
                      autoFocus
                      autoComplete="off"
                      spellCheck="false"
                    />
                  </div>
                  {inputError && (
                    <p className="text-xs text-red-600 mt-1.5 flex items-center gap-1">
                      <AlertCircle className="h-3.5 w-3.5" />
                      {inputError}
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-[11px] text-gray-400">
                    Press <kbd className="px-1.5 py-0.5 bg-gray-100 rounded border">Enter</kbd> to
                    submit
                  </span>
                  <Button
                    type="submit"
                    disabled={!userResponse.trim()}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700"
                  >
                    <Send className="h-4 w-4" />
                    Submit Answer
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Result & Evaluation View (Shown after submission) */}
        {lastSubmission && !submitMutation.isPending && (
          <div className="space-y-6 animate-fadeIn">
            {/* Success/Failure Banner Card */}
            <Card
              className={`border shadow-sm overflow-hidden ${
                lastSubmission.recall_successful
                  ? 'border-emerald-200 bg-gradient-to-br from-emerald-50/80 via-white to-white'
                  : 'border-amber-200 bg-gradient-to-br from-amber-50/80 via-white to-white'
              }`}
            >
              <CardContent className="p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                  <div className="flex items-start gap-3">
                    {lastSubmission.recall_successful ? (
                      <div className="p-2 bg-emerald-100 text-emerald-700 rounded-full shrink-0">
                        <CheckCircle2 className="h-6 w-6" />
                      </div>
                    ) : (
                      <div className="p-2 bg-amber-100 text-amber-700 rounded-full shrink-0">
                        <AlertCircle className="h-6 w-6" />
                      </div>
                    )}
                    <div>
                      <h2 className="text-lg sm:text-xl font-bold text-gray-900">
                        {lastSubmission.recall_successful
                          ? 'Recalled Successfully!'
                          : 'Needs Review'}
                      </h2>
                      <p className="text-xs sm:text-sm text-gray-600 mt-0.5">
                        {lastSubmission.feedback}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center">
                    <span className="text-xs font-bold px-3 py-1 bg-white rounded-lg border border-gray-200 shadow-xs text-purple-700">
                      +{lastSubmission.xp_earned} XP
                    </span>
                    <span
                      className={`text-lg font-black px-3 py-1 rounded-lg ${
                        lastSubmission.recall_successful
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {lastSubmission.score.toFixed(1)}/10
                    </span>
                  </div>
                </div>

                {/* Target Word Revelation Card */}
                <div className="bg-white rounded-xl p-4 border border-gray-200 shadow-xs mb-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 block">
                        Target Word
                      </span>
                      <h3 className="text-2xl font-black text-gray-900 capitalize">
                        {lastSubmission.target_word}
                      </h3>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 block">
                        New Status
                      </span>
                      <span className="inline-block px-2.5 py-0.5 text-xs font-bold rounded-full bg-purple-100 text-purple-800 capitalize">
                        {lastSubmission.new_status}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Spaced Repetition Schedule Info */}
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100 text-xs">
                  <div className="flex items-center gap-2 text-gray-600">
                    <Calendar className="h-4 w-4 text-purple-600 shrink-0" />
                    <span>
                      Interval:{' '}
                      <strong className="text-gray-900">
                        {lastSubmission.new_interval_days} day
                        {lastSubmission.new_interval_days > 1 ? 's' : ''}
                      </strong>
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-600 justify-end">
                    <TrendingUp className="h-4 w-4 text-emerald-600 shrink-0" />
                    <span>
                      Mastery:{' '}
                      <strong className="text-gray-900">
                        {Math.round(lastSubmission.mastery_score * 100)}%
                      </strong>
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Bar */}
            <div className="flex justify-end">
              <Button
                onClick={handleNextWord}
                className="w-full sm:w-auto flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700"
              >
                <span>
                  {currentIndex + 1 < dueItems.length ? 'Next Word in Queue' : 'Finish Session'}
                </span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ReviewsPage
