import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Sparkles,
  Target,
  BookOpen,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Flame,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { personalizationApi } from '@/api/personalization'
import {
  PersonalizedRecommendation,
  WordSummaryItem,
  PersonalizedScenario,
} from '@/types'

const DOMAIN_OPTIONS = [
  'Workplace & Business',
  'Technology & Software',
  'Travel & Exploration',
  'Daily Life & Casual',
  'Job Interviews',
  'Academic & Discussions',
]

export function PersonalizationPage() {
  const navigate = useNavigate()

  // Scenario Generator State
  const [selectedWord, setSelectedWord] = useState('')
  const [selectedDomain, setSelectedDomain] = useState(DOMAIN_OPTIONS[0])
  const [weakNote, setWeakNote] = useState('')
  const [generatedScenario, setGeneratedScenario] = useState<PersonalizedScenario | null>(null)
  const [scenarioError, setScenarioError] = useState<string | null>(null)

  // 1. Fetch Profile
  const {
    data: profile,
    isLoading: isLoadingProfile,
    error: profileError,
    refetch: refetchProfile,
  } = useQuery({
    queryKey: ['personalization-profile'],
    queryFn: () => personalizationApi.getProfile(),
  })

  // 2. Fetch Recommendations
  const {
    data: recommendationsData,
    isLoading: isLoadingRecommendations,
    error: recsError,
    refetch: refetchRecs,
  } = useQuery({
    queryKey: ['personalization-recommendations'],
    queryFn: () => personalizationApi.getRecommendations(5),
  })

  // 3. Scenario Generation Mutation
  const scenarioMutation = useMutation({
    mutationFn: (data: { word: string; domain: string; weak_area_context?: string }) =>
      personalizationApi.generateScenario(data),
    onSuccess: (data) => {
      setGeneratedScenario(data)
      setScenarioError(null)
    },
    onError: (err: any) => {
      setScenarioError(
        err?.response?.data?.detail || 'Failed to generate personalized scenario. Please try again.'
      )
    },
  })

  const handleGenerateScenario = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedWord.trim()) {
      setScenarioError('Please enter a target word to generate a personalized scenario.')
      return
    }
    setScenarioError(null)
    scenarioMutation.mutate({
      word: selectedWord.trim(),
      domain: selectedDomain,
      weak_area_context: weakNote.trim() || undefined,
    })
  }

  const handleActionClick = (rec: PersonalizedRecommendation) => {
    switch (rec.activity_type) {
      case 'review':
        navigate('/reviews')
        break
      case 'practice':
        if (rec.vocabulary_id) {
          navigate(`/practice/${rec.vocabulary_id}`)
        } else {
          setSelectedWord(rec.word)
          const elem = document.getElementById('scenario-generator')
          if (elem) elem.scrollIntoView({ behavior: 'smooth' })
        }
        break
      case 'conversation':
        navigate('/conversations')
        break
      case 'learn':
        if (rec.vocabulary_id) {
          navigate(`/vocabulary/${rec.vocabulary_id}/learn`)
        } else {
          navigate('/vocabulary')
        }
        break
      default:
        navigate('/vocabulary')
    }
  }

  const isLoading = isLoadingProfile || isLoadingRecommendations
  const hasError = profileError || recsError

  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <LoadingSpinner size="lg" className="text-blue-600" />
        <p className="text-sm font-medium text-gray-500">
          Analyzing your learning patterns & building recommendations...
        </p>
      </div>
    )
  }

  if (hasError || !profile) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <ErrorState
          title="Could Not Load Personalized Plan"
          message="There was a problem retrieving your personalized learning profile. Please try again."
          onRetry={() => {
            refetchProfile()
            refetchRecs()
          }}
        />
      </div>
    )
  }

  const recommendations = recommendationsData?.recommendations || []
  const hasVocabulary = profile.total_vocabulary > 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 rounded-2xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-xs font-semibold backdrop-blur-sm border border-white/20">
              <Sparkles className="h-3.5 w-3.5 text-yellow-300" />
              <span>Adaptive Learning Engine</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Personalized Learning Plan
            </h1>
            <p className="text-blue-100 text-sm sm:text-base max-w-2xl">
              Targeted practice, weak-area reinforcement, and AI scenario generation tailored to your
              current vocabulary mastery.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20 flex items-center gap-4 min-w-[240px]">
            <div className="h-12 w-12 rounded-lg bg-blue-500/30 flex items-center justify-center border border-white/20">
              <Target className="h-6 w-6 text-yellow-300" />
            </div>
            <div>
              <p className="text-xs text-blue-200 uppercase font-bold tracking-wider">Learner Level</p>
              <p className="text-xl font-bold">
                CEFR {profile.adaptive_cefr_level}
              </p>
              <p className="text-xs text-blue-200">
                Difficulty: {profile.adaptive_difficulty_score}/10.0
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Focus Area Alert Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="p-2 bg-amber-100 rounded-lg text-amber-700 mt-0.5">
            <Flame className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-900 uppercase tracking-wide">
              Today's Recommended Focus
            </h3>
            <p className="text-sm font-medium text-amber-800 mt-0.5">
              {profile.recommended_focus}
            </p>
          </div>
        </div>
        <Button
          size="sm"
          onClick={() => navigate('/adaptive')}
          className="bg-amber-600 hover:bg-amber-700 text-white shrink-0 self-start sm:self-center flex items-center gap-1.5 font-semibold"
        >
          <Sparkles className="h-4 w-4" />
          <span>View Adaptive Plan</span>
        </Button>
      </div>

      {/* SECTION 1: Prioritized Recommendations */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Target className="h-5 w-5 text-blue-600" />
              Recommended Next Steps
            </h2>
            <p className="text-sm text-gray-500">
              Prioritized actions based on spaced repetition, weak areas, and mastery progression
            </p>
          </div>
        </div>

        {recommendations.length === 0 ? (
          <Card>
            <CardContent className="py-8">
              <EmptyState
                title="No Pending Recommendations"
                message="You're all caught up! Add more vocabulary words to unlock customized practice and reviews."
                action={
                  <Button onClick={() => navigate('/vocabulary')} size="sm">
                    Add Words
                  </Button>
                }
              />
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {recommendations.map((rec, index) => {
              const isHigh = rec.priority === 'high'
              const isReview = rec.activity_type === 'review'
              const isPractice = rec.activity_type === 'practice'
              const isConvo = rec.activity_type === 'conversation'

              return (
                <Card
                  key={`${rec.word}-${index}`}
                  className="flex flex-col justify-between hover:shadow-md transition border-gray-200"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`text-xs font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                          isReview
                            ? 'bg-purple-100 text-purple-800'
                            : isPractice
                            ? 'bg-blue-100 text-blue-800'
                            : isConvo
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {rec.activity_type}
                      </span>
                      {isHigh && (
                        <span className="text-xs font-semibold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200 flex items-center gap-1">
                          <AlertTriangle className="h-3 w-3" /> High Priority
                        </span>
                      )}
                    </div>
                    <CardTitle className="text-xl font-bold text-gray-900 mt-2">
                      {rec.word}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 flex-1 flex flex-col justify-between">
                    <p className="text-xs text-gray-600 leading-relaxed">
                      {rec.reason}
                    </p>
                    <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-500">
                        Target: {rec.cefr_level} ({rec.recommended_difficulty}/10)
                      </span>
                      <Button
                        size="sm"
                        variant={isHigh ? 'primary' : 'outline'}
                        onClick={() => handleActionClick(rec)}
                        className="flex items-center gap-1 text-xs"
                      >
                        {isReview && 'Start Review'}
                        {isPractice && 'Practice'}
                        {isConvo && 'Start Chat'}
                        {rec.activity_type === 'learn' && 'Learn Word'}
                        <ArrowRight className="h-3.5 w-3.5 ml-0.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: Two Column (Weak Words vs Learning Analytics) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Weak Words & Focus Areas */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-rose-500" />
                Weak Words & Focus Areas
              </CardTitle>
              <span className="text-xs font-semibold px-2.5 py-1 bg-rose-50 text-rose-700 rounded-full border border-rose-200">
                {profile.weak_words.length} items
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Words with struggling status, recall failures, or low retention scores
            </p>
          </CardHeader>
          <CardContent className="flex-1">
            {profile.weak_words.length === 0 ? (
              <div className="py-8 text-center text-gray-500 space-y-2">
                <CheckCircle2 className="h-10 w-10 text-emerald-500 mx-auto" />
                <p className="font-semibold text-gray-800">No Weak Vocabulary Detected</p>
                <p className="text-xs text-gray-500 max-w-xs mx-auto">
                  You have high retention across your learned words. Keep practicing to maintain memory!
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {profile.weak_words.map((item: WordSummaryItem) => (
                  <div
                    key={item.id}
                    className="py-3 flex items-center justify-between gap-3 hover:bg-gray-50 px-2 rounded-lg transition"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-900">{item.word}</span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-medium ${
                            item.status === 'struggling'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {item.status}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Mastery: {Math.round(item.mastery_score * 100)}% • Failures: {item.failed_recall_count} • Practices: {item.practice_count}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs"
                        onClick={() => {
                          setSelectedWord(item.word)
                          const elem = document.getElementById('scenario-generator')
                          if (elem) elem.scrollIntoView({ behavior: 'smooth' })
                        }}
                      >
                        Customize Scenario
                      </Button>
                      <Button
                        size="sm"
                        className="text-xs"
                        onClick={() => navigate(`/practice/${item.id}`)}
                      >
                        Practice
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Column: Learning Pattern Analytics */}
        <Card className="flex flex-col">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-indigo-600" />
              Learning Pattern Analytics
            </CardTitle>
            <p className="text-xs text-gray-500 mt-1">
              Deterministic mastery breakdown and recall consistency metrics
            </p>
          </CardHeader>
          <CardContent className="space-y-6 flex-1">
            {/* Stats Row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center">
                <p className="text-xs text-gray-500">Avg Mastery</p>
                <p className="text-lg font-bold text-blue-600">
                  {Math.round(profile.average_mastery * 100)}%
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center">
                <p className="text-xs text-gray-500">Practice Rate</p>
                <p className="text-lg font-bold text-emerald-600">
                  {Math.round(profile.practice_success_rate * 100)}%
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center">
                <p className="text-xs text-gray-500">Recall Accuracy</p>
                <p className="text-lg font-bold text-purple-600">
                  {Math.round(profile.recall_accuracy_rate * 100)}%
                </p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center">
                <p className="text-xs text-gray-500">Conversations</p>
                <p className="text-lg font-bold text-indigo-600">
                  {profile.total_conversations_completed}
                </p>
              </div>
            </div>

            {/* Mastery Distribution */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Vocabulary State Distribution ({profile.total_vocabulary} words)
                </span>
              </div>
              <div className="space-y-2">
                {[
                  { label: 'Mastered', count: profile.mastery_distribution.mastered, color: 'bg-emerald-500' },
                  { label: 'Reinforced', count: profile.mastery_distribution.reinforced, color: 'bg-blue-500' },
                  { label: 'Recalled', count: profile.mastery_distribution.recalled, color: 'bg-indigo-400' },
                  { label: 'Practiced', count: profile.mastery_distribution.practiced, color: 'bg-cyan-500' },
                  { label: 'Learned', count: profile.mastery_distribution.learned, color: 'bg-amber-400' },
                  { label: 'Struggling', count: profile.mastery_distribution.struggling, color: 'bg-rose-500' },
                  { label: 'New', count: profile.mastery_distribution.new, color: 'bg-gray-300' },
                ].map((item) => {
                  const pct = hasVocabulary
                    ? Math.round((item.count / profile.total_vocabulary) * 100)
                    : 0
                  return (
                    <div key={item.label} className="text-xs space-y-1">
                      <div className="flex justify-between text-gray-600 font-medium">
                        <span>{item.label}</span>
                        <span>{item.count} ({pct}%)</span>
                      </div>
                      <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${item.color} rounded-full transition-all duration-500`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SECTION 3: AI Personalized Scenario Generator */}
      <Card id="scenario-generator" className="border-blue-200 bg-gradient-to-b from-white to-blue-50/30">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            AI Personalized Scenario Generator
          </CardTitle>
          <p className="text-xs text-gray-500 mt-1">
            Generate custom real-life communication scenarios adapted to your chosen domain, target word, and proficiency level.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleGenerateScenario} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                  Target Word <span className="text-rose-500">*</span>
                </label>
                <Input
                  placeholder="e.g., negotiate, hesitate, resilient..."
                  value={selectedWord}
                  onChange={(e) => setSelectedWord(e.target.value)}
                  className="bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                  Context / Domain
                </label>
                <select
                  className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                >
                  {DOMAIN_OPTIONS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase mb-1">
                Specific Learning Focus / Weakness Note (Optional)
              </label>
              <Input
                placeholder="e.g., Struggles with polite disagreement in meetings, or travel questions..."
                value={weakNote}
                onChange={(e) => setWeakNote(e.target.value)}
                className="bg-white"
              />
            </div>

            {scenarioError && (
              <p className="text-xs text-rose-600 font-medium">{scenarioError}</p>
            )}

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={scenarioMutation.isPending || !selectedWord.trim()}
                className="flex items-center gap-2"
              >
                {scenarioMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" /> Generating Scenario...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" /> Generate Personalized Scenario
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Generated Scenario Result Card */}
          {generatedScenario && (
            <div className="bg-white border border-blue-200 rounded-xl p-6 shadow-sm space-y-4 animate-in fade-in duration-300">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 bg-blue-100 text-blue-800 rounded-full">
                  {generatedScenario.domain} • CEFR {generatedScenario.cefr_level}
                </span>
                <span className="text-xs text-gray-500 font-medium">
                  Difficulty: {generatedScenario.difficulty_score}/10
                </span>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-bold text-gray-700 uppercase">Situation</h4>
                <p className="text-sm text-gray-900 bg-gray-50 p-4 rounded-lg border border-gray-100 leading-relaxed">
                  {generatedScenario.situation}
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-bold text-gray-700 uppercase">Your Task</h4>
                <p className="text-sm text-indigo-950 font-medium bg-indigo-50/70 p-4 rounded-lg border border-indigo-100">
                  {generatedScenario.prompt}
                </p>
              </div>

              {generatedScenario.context_hint && (
                <p className="text-xs text-gray-500 italic">
                  💡 Hint: {generatedScenario.context_hint}
                </p>
              )}

              <div className="pt-3 border-t border-gray-100 flex justify-end">
                {generatedScenario.vocabulary_id ? (
                  <Button
                    onClick={() => navigate(`/practice/${generatedScenario.vocabulary_id}`)}
                    className="flex items-center gap-2"
                  >
                    Practice This Word Now <ArrowRight className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    onClick={() => navigate('/vocabulary')}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    Add Word to Vocabulary <BookOpen className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default PersonalizationPage
