import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vocabularyApi } from '@/api/vocabulary'
import { VocabularyStatus } from '@/types'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Sparkles,
  Layers,
  MessageSquare,
  TrendingUp,
  Award,
} from 'lucide-react'

const cefrColors: Record<string, { bg: string; text: string }> = {
  A1: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', text: 'text-emerald-700' },
  A2: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', text: 'text-emerald-700' },
  B1: { bg: 'bg-blue-50 text-blue-700 border-blue-200', text: 'text-blue-700' },
  B2: { bg: 'bg-indigo-50 text-indigo-700 border-indigo-200', text: 'text-indigo-700' },
  C1: { bg: 'bg-purple-50 text-purple-700 border-purple-200', text: 'text-purple-700' },
  C2: { bg: 'bg-rose-50 text-rose-700 border-rose-200', text: 'text-rose-700' },
}

const statusColors: Record<VocabularyStatus, { bg: string; text: string; label: string }> = {
  new: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'New' },
  learned: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Learned' },
  practiced: { bg: 'bg-indigo-100', text: 'text-indigo-700', label: 'Practiced' },
  recalled: { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Recalled' },
  reinforced: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Reinforced' },
  mastered: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Mastered' },
  struggling: { bg: 'bg-red-100', text: 'text-red-700', label: 'Struggling' },
}

export function LearnPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const {
    data: vocab,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['vocabulary-learn', id],
    queryFn: () => vocabularyApi.getLearningContent(id!),
    enabled: !!id,
  })

  const markLearnedMutation = useMutation({
    mutationFn: (vocabId: string) => vocabularyApi.markLearned(vocabId),
    onSuccess: (updatedVocab) => {
      queryClient.setQueryData(['vocabulary-learn', id], updatedVocab)
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] })
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="text-center max-w-md">
          <LoadingSpinner size="lg" className="mx-auto mb-4 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Generating AI Learning Content
          </h2>
          <p className="text-sm text-gray-600">
            Analyzing word nuance, formulating natural contextual explanations, and crafting 10
            conversational examples...
          </p>
        </div>
      </div>
    )
  }

  if (error || !vocab) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Link
            to="/vocabulary"
            className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Vocabulary
          </Link>
          <ErrorState
            title="Failed to load learning content"
            message="Could not load or generate the AI learning material for this word. Please check your connection and try again."
            onRetry={() => refetch()}
          />
        </div>
      </div>
    )
  }

  const details = vocab.details
  const examples = vocab.examples || []
  const cefrStyle = details?.cefr_level ? cefrColors[details.cefr_level] : null
  const statusCfg = statusColors[vocab.status] || statusColors.new
  const isLearnedOrBeyond = vocab.status !== 'new'

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Navigation & Status Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <Link
            to="/vocabulary"
            className="inline-flex items-center text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-1.5" />
            Back to Vocabulary
          </Link>

          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-full ${statusCfg.bg} ${statusCfg.text}`}
            >
              Status: {statusCfg.label}
            </span>
            {isLearnedOrBeyond && (
              <span className="inline-flex items-center text-xs font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                Learned
              </span>
            )}
          </div>
        </div>

        {/* Word Hero Card */}
        <Card className="mb-8 border-gray-200 shadow-sm bg-white overflow-hidden">
          <div className="p-6 sm:p-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gray-100 pb-6 mb-6">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight capitalize">
                    {vocab.word}
                  </h1>
                  {details?.pronunciation_text && (
                    <span className="text-base text-gray-500 font-mono bg-gray-100 px-2.5 py-1 rounded-md">
                      /{details.pronunciation_text}/
                    </span>
                  )}
                </div>
                {details?.part_of_speech && (
                  <p className="text-sm font-medium text-blue-600 mt-1.5 italic">
                    {details.part_of_speech}
                  </p>
                )}
              </div>

              {/* Metadata Badges */}
              <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                {details?.cefr_level && (
                  <div
                    className={`inline-flex flex-col px-3 py-1.5 rounded-lg border text-xs font-semibold ${
                      cefrStyle?.bg || 'bg-gray-100 text-gray-700 border-gray-200'
                    }`}
                  >
                    <span className="text-[10px] uppercase tracking-wider text-gray-500 font-normal">
                      CEFR Level
                    </span>
                    <span>{details.cefr_level}</span>
                  </div>
                )}
                {details?.difficulty_score !== undefined && details.difficulty_score !== null && (
                  <div className="inline-flex flex-col px-3 py-1.5 rounded-lg border border-gray-200 bg-gray-50 text-xs font-semibold text-gray-800">
                    <span className="text-[10px] uppercase tracking-wider text-gray-500 font-normal">
                      Difficulty
                    </span>
                    <span>{details.difficulty_score.toFixed(1)} / 10</span>
                  </div>
                )}
              </div>
            </div>

            {/* Definitions & Context */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-blue-50/60 rounded-xl p-5 border border-blue-100">
                <div className="flex items-center gap-2 text-blue-800 font-semibold text-sm mb-2">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                  Simple Definition
                </div>
                <p className="text-gray-800 text-base leading-relaxed">
                  {details?.simple_meaning || 'No definition available.'}
                </p>
              </div>

              {details?.contextual_meaning && (
                <div className="bg-amber-50/60 rounded-xl p-5 border border-amber-100">
                  <div className="flex items-center gap-2 text-amber-900 font-semibold text-sm mb-2">
                    <Sparkles className="h-4 w-4 text-amber-600" />
                    How & When to Use It
                  </div>
                  <p className="text-gray-800 text-sm leading-relaxed">
                    {details.contextual_meaning}
                  </p>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Linguistic Exploration Grid */}
        {details && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Word Forms */}
            <Card className="border-gray-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <Layers className="h-4 w-4 text-indigo-600" />
                  Word Forms
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {Object.entries(details.word_forms || {}).length > 0 ? (
                  Object.entries(details.word_forms).map(([formType, formWord]) => (
                    <div
                      key={formType}
                      className="flex justify-between items-center py-1 border-b border-gray-100 last:border-0"
                    >
                      <span className="text-gray-500 capitalize text-xs">{formType}</span>
                      <span className="font-medium text-gray-900 font-mono text-xs">
                        {formWord}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-400">No additional forms listed.</p>
                )}
              </CardContent>
            </Card>

            {/* Synonyms & Antonyms */}
            <Card className="border-gray-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-600" />
                  Synonyms & Antonyms
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 block mb-1.5">
                    Synonyms
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(details.synonyms || []).length > 0 ? (
                      details.synonyms.map((syn) => (
                        <span
                          key={syn}
                          className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs rounded-full font-medium"
                        >
                          {syn}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400">None</span>
                    )}
                  </div>
                </div>

                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 block mb-1.5">
                    Antonyms
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {(details.antonyms || []).length > 0 ? (
                      details.antonyms.map((ant) => (
                        <span
                          key={ant}
                          className="px-2.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 text-xs rounded-full font-medium"
                        >
                          {ant}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-gray-400">None</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Common Collocations */}
            <Card className="border-gray-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-blue-600" />
                  Common Collocations
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <ul className="space-y-2">
                  {(details.collocations || []).length > 0 ? (
                    details.collocations.map((col, idx) => (
                      <li key={idx} className="flex items-start text-xs text-gray-700">
                        <span className="text-blue-500 mr-2 font-bold">•</span>
                        <span className="font-medium">{col}</span>
                      </li>
                    ))
                  ) : (
                    <li className="text-xs text-gray-400">No collocations listed.</li>
                  )}
                </ul>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 10 Conversational Examples Section */}
        <div className="mb-10">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-blue-600" />
                10 Real-Life Conversational Examples
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                See how native speakers use <span className="font-semibold">{vocab.word}</span> across
                varied everyday situations.
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full border border-blue-200">
              {examples.length} Examples
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {examples.map((ex, index) => (
              <Card
                key={ex.id || index}
                className="border-gray-200 hover:border-blue-200 hover:shadow-sm transition-all bg-white"
              >
                <CardContent className="p-4 sm:p-5 flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="inline-flex items-center px-2 py-0.5 text-[11px] font-semibold rounded-md bg-gray-100 text-gray-700 border border-gray-200">
                        {ex.context_label}
                      </span>
                      <span className="text-[11px] font-mono text-gray-400">#{index + 1}</span>
                    </div>
                    <p className="text-sm text-gray-800 leading-relaxed italic">
                      "{ex.example_text}"
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Action Bottom Bar */}
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-sm">
          <CardContent className="p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <Award className="h-5 w-5 text-blue-600" />
                {vocab.status === 'new'
                  ? 'Ready to move this word into your active vocabulary?'
                  : 'Great job reviewing this word!'}
              </h3>
              <p className="text-xs text-gray-600 mt-1">
                {vocab.status === 'new'
                  ? 'Marking this word as learned records your progress and awards 10 XP.'
                  : 'You have already completed the explanation step for this word.'}
              </p>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              {vocab.status === 'new' ? (
                <Button
                  onClick={() => markLearnedMutation.mutate(vocab.id)}
                  disabled={markLearnedMutation.isPending}
                  className="w-full sm:w-auto flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {markLearnedMutation.isPending ? 'Saving...' : 'Mark as Understood (+10 XP)'}
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => navigate('/vocabulary')}
                  className="w-full sm:w-auto"
                >
                  Return to Vocabulary List
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
export default LearnPage
