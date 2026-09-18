import { useQuery } from '@tanstack/react-query'
import { useNavigate, Link } from 'react-router-dom'
import {
  Sparkles,
  Target,
  Brain,
  Layers,
  MessageSquare,
  BookOpen,
  Compass,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Flame,
  CheckCircle2,
  RefreshCw,
  Award,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { adaptiveApi } from '@/api/adaptive'
import { AdaptiveRecommendationItem } from '@/types'

export function AdaptiveLearningPage() {
  const navigate = useNavigate()

  const {
    data: plan,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['adaptive-plan'],
    queryFn: () => adaptiveApi.getPlan(),
  })

  if (isLoading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center gap-3">
        <LoadingSpinner size="lg" className="text-blue-600" />
        <p className="text-sm font-medium text-gray-500">
          Analyzing performance metrics & calibrating adaptive recommendations...
        </p>
      </div>
    )
  }

  if (error || !plan) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <ErrorState
          title="Could Not Load Adaptive Plan"
          message="There was an issue generating your adaptive learning recommendations. Please try again."
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  const { learner_profile, primary_recommendation, recommendations, diagnostic_focus, daily_plan_sync } = plan
  const isEmptyUser = learner_profile.total_vocabulary === 0

  const getActivityIcon = (activityType: string) => {
    switch (activityType) {
      case 'review':
        return <Brain className="h-5 w-5 text-purple-600" />
      case 'practice':
        return <Target className="h-5 w-5 text-blue-600" />
      case 'multi_word':
        return <Layers className="h-5 w-5 text-indigo-600" />
      case 'conversation':
        return <MessageSquare className="h-5 w-5 text-emerald-600" />
      case 'learn':
        return <BookOpen className="h-5 w-5 text-amber-600" />
      case 'error_remediation':
        return <Compass className="h-5 w-5 text-rose-600" />
      default:
        return <Sparkles className="h-5 w-5 text-blue-600" />
    }
  }

  const getPriorityBadgeClass = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'high':
        return 'bg-amber-100 text-amber-800 border-amber-200'
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 rounded-2xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-xs font-semibold backdrop-blur-sm border border-white/20">
              <Sparkles className="h-3.5 w-3.5 text-yellow-300" />
              <span>Personalized Recommendation Engine</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Adaptive Learning Plan
            </h1>
            <p className="text-blue-100 text-sm sm:text-base max-w-2xl">
              Real-time recommendations calibrated to your CEFR level, memory retention curve,
              and recent diagnostic error analysis.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* CEFR Level Box */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20 min-w-[140px]">
              <p className="text-xs text-blue-200 uppercase font-bold tracking-wider">Level</p>
              <p className="text-xl font-bold">CEFR {learner_profile.cefr_level}</p>
              <p className="text-xs text-blue-200">
                Diff: {learner_profile.difficulty_score} / 10.0
              </p>
            </div>

            {/* Mastery Box */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20 min-w-[140px]">
              <p className="text-xs text-blue-200 uppercase font-bold tracking-wider">Avg Mastery</p>
              <p className="text-xl font-bold">
                {Math.round(learner_profile.average_mastery * 100)}%
              </p>
              <p className="text-xs text-blue-200">
                {learner_profile.active_vocabulary} Active Words
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isRefetching}
              className="bg-white/10 hover:bg-white/20 text-white border-white/30 h-10 px-3"
            >
              <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </div>

      {/* Daily Plan Sync & Streak Alert Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Daily Goal</p>
            <p className="text-lg font-bold text-gray-900">
              {daily_plan_sync.daily_goal_progress} / {daily_plan_sync.daily_goal_target} Activities
            </p>
          </div>
          {daily_plan_sync.is_goal_completed ? (
            <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center text-green-600">
              <CheckCircle2 className="h-5 w-5" />
            </div>
          ) : (
            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
              <Award className="h-5 w-5" />
            </div>
          )}
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Current Streak</p>
            <p className="text-lg font-bold text-gray-900">
              {daily_plan_sync.current_streak} Day{daily_plan_sync.current_streak === 1 ? '' : 's'}
            </p>
          </div>
          <div className="h-10 w-10 rounded-full bg-amber-100 flex items-center justify-center text-amber-600">
            <Flame className="h-5 w-5" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase">Recent Accuracy</p>
            <p className="text-lg font-bold text-gray-900">
              {Math.round(learner_profile.recent_accuracy_rate * 100)}%
            </p>
          </div>
          <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>
      </div>

      {isEmptyUser ? (
        <Card className="border-dashed border-2 border-gray-300">
          <CardContent className="py-12">
            <EmptyState
              title="Welcome to Adaptive Learning"
              message="Your vocabulary bank is currently empty. Add your first target words to activate personalized scenario practice, spaced repetition schedules, and diagnostic feedback."
              action={
                <Button onClick={() => navigate('/vocabulary')} size="md">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Add First Words
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {/* SECTION 1: PRIMARY NEXT ACTIVITY HERO CARD */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-600" />
                Recommended Next Activity
              </h2>
              <span className="text-xs font-semibold uppercase tracking-wider text-blue-700 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                Top Priority
              </span>
            </div>

            <Card className="border-2 border-blue-200 bg-gradient-to-br from-blue-50/40 via-white to-indigo-50/30 shadow-md">
              <CardContent className="p-6 sm:p-8 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="p-2 rounded-lg bg-white border border-gray-200 shadow-xs">
                        {getActivityIcon(primary_recommendation.activity_type)}
                      </span>
                      <span
                        className={`text-xs font-bold uppercase px-2.5 py-1 rounded-full border ${getPriorityBadgeClass(
                          primary_recommendation.priority
                        )}`}
                      >
                        {primary_recommendation.priority} Priority
                      </span>
                      <span className="text-xs font-semibold text-gray-600 bg-white px-2.5 py-1 rounded-full border border-gray-200">
                        CEFR {primary_recommendation.cefr_level} • Difficulty{' '}
                        {primary_recommendation.difficulty}
                      </span>
                    </div>

                    <h3 className="text-xl sm:text-2xl font-bold text-gray-900">
                      {primary_recommendation.title}
                    </h3>
                  </div>

                  <Button
                    size="lg"
                    onClick={() => navigate(primary_recommendation.action_url)}
                    className="sm:self-center shadow-md bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2 font-bold px-6 shrink-0"
                  >
                    <span>{primary_recommendation.action_label}</span>
                    <ArrowRight className="h-5 w-5" />
                  </Button>
                </div>

                {/* Target Words Chips */}
                {primary_recommendation.target_words.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-500">
                      Target Vocabulary
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {primary_recommendation.target_words.map((word, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-3 py-1 rounded-md text-sm font-semibold bg-white border border-blue-200 text-blue-900 shadow-xs"
                        >
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reason & Learning Objective Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-100">
                  <div className="bg-white p-4 rounded-lg border border-gray-200/80">
                    <p className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-1 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                      Why This Activity?
                    </p>
                    <p className="text-sm text-gray-700 font-medium">
                      {primary_recommendation.reason}
                    </p>
                  </div>

                  <div className="bg-white p-4 rounded-lg border border-gray-200/80">
                    <p className="text-xs font-bold uppercase text-gray-500 tracking-wider mb-1 flex items-center gap-1.5">
                      <Target className="h-3.5 w-3.5 text-blue-500" />
                      Learning Objective
                    </p>
                    <p className="text-sm text-gray-700 font-medium">
                      {primary_recommendation.learning_objective}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* SECTION 2: DIAGNOSTIC ERRORS & LINGUISTIC FOCUS */}
          <div className="space-y-3">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Compass className="h-5 w-5 text-teal-600" />
              Diagnostic Focus & Linguistic Analysis
            </h2>

            <Card className="border border-gray-200">
              <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Left: Weakness & Strategy */}
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-bold uppercase text-gray-500 tracking-wider">
                        Primary Focus Area
                      </p>
                      <p className="text-base font-bold text-gray-900 mt-1 flex items-center gap-2">
                        {diagnostic_focus.primary_weakness ? (
                          <>
                            <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                            <span>{diagnostic_focus.primary_weakness}</span>
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                            <span className="text-green-800 font-semibold">
                              Balanced Proficiency — No Critical Weakness
                            </span>
                          </>
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs font-bold uppercase text-gray-500 tracking-wider">
                        Pedagogical Strategy
                      </p>
                      <p className="text-sm text-gray-700 mt-1 bg-gray-50 p-3 rounded-lg border border-gray-200 font-medium">
                        {diagnostic_focus.recommended_strategy}
                      </p>
                    </div>
                  </div>

                  {/* Right: Error Breakdown */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-bold uppercase text-gray-500 tracking-wider">
                        Recent Error Patterns ({diagnostic_focus.recent_error_count} detected)
                      </p>
                      <Link
                        to="/knowledge"
                        className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline"
                      >
                        Study Rules
                      </Link>
                    </div>

                    {diagnostic_focus.top_error_types.length === 0 ? (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-sm text-green-800 flex items-center gap-2 font-medium">
                        <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                        <span>No recent linguistic errors recorded. High grammatical and contextual precision!</span>
                      </div>
                    ) : (
                      <div className="space-y-2.5">
                        {diagnostic_focus.top_error_types.map((err, idx) => (
                          <div
                            key={idx}
                            className="bg-gray-50 rounded-lg p-3 border border-gray-200 space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold uppercase px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
                                {err.error_type}
                              </span>
                              <span className="text-xs font-semibold text-gray-600">
                                {err.count} occurrence{err.count > 1 ? 's' : ''}
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 font-medium">
                              {err.description}
                            </p>
                            {err.sample_phrases.length > 0 && (
                              <div className="text-xs text-gray-500 font-mono bg-white px-2 py-1 rounded border border-gray-200 truncate">
                                "{err.sample_phrases[0]}"
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* SECTION 3: PRIORITIZED ADAPTIVE QUEUE */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <Layers className="h-5 w-5 text-indigo-600" />
              Prioritized Adaptive Queue
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {recommendations.map((rec: AdaptiveRecommendationItem, idx: number) => {
                const isPrimary = rec.id === primary_recommendation.id
                return (
                  <Card
                    key={rec.id || idx}
                    className={`flex flex-col justify-between transition-all hover:shadow-md ${
                      isPrimary ? 'border-blue-300 ring-1 ring-blue-300' : 'border-gray-200'
                    }`}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="p-1.5 rounded-md bg-gray-50 border border-gray-200">
                          {getActivityIcon(rec.activity_type)}
                        </span>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`text-[11px] font-bold uppercase px-2 py-0.5 rounded-full border ${getPriorityBadgeClass(
                              rec.priority
                            )}`}
                          >
                            {rec.priority}
                          </span>
                          <span className="text-[11px] font-semibold text-gray-600 bg-gray-50 px-2 py-0.5 rounded-full border border-gray-200">
                            CEFR {rec.cefr_level}
                          </span>
                        </div>
                      </div>
                      <CardTitle className="text-base font-bold text-gray-900 line-clamp-2">
                        {rec.title}
                      </CardTitle>
                    </CardHeader>

                    <CardContent className="space-y-4 flex-1 flex flex-col justify-between">
                      <div className="space-y-3">
                        {rec.target_words.length > 0 && (
                          <div className="flex flex-wrap gap-1.5">
                            {rec.target_words.map((w, wIdx) => (
                              <span
                                key={wIdx}
                                className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-800 font-semibold border border-blue-100"
                              >
                                {w}
                              </span>
                            ))}
                          </div>
                        )}

                        <div className="space-y-1.5">
                          <p className="text-xs text-gray-600 font-medium">
                            <span className="font-bold text-gray-700">Reason: </span>
                            {rec.reason}
                          </p>
                          <p className="text-xs text-gray-600 font-medium">
                            <span className="font-bold text-gray-700">Objective: </span>
                            {rec.learning_objective}
                          </p>
                        </div>
                      </div>

                      <Button
                        variant={isPrimary ? 'primary' : 'outline'}
                        size="sm"
                        onClick={() => navigate(rec.action_url)}
                        className="w-full mt-2 font-semibold flex items-center justify-center gap-1.5"
                      >
                        <span>{rec.action_label}</span>
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
