import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Brain,
  Sparkles,
  MessageSquare,
  Flame,
  Award,
  BookOpen,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
  BarChart3,
  Calendar,
  Layers,
  ChevronRight,
  RefreshCw,
  Compass,
  Download,
} from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area,
  CartesianGrid,
} from 'recharts'

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import { dashboardApi } from '@/api/dashboard'
import { progressApi } from '@/api/progress'
import { VocabularyStatus } from '@/types'

const STATUS_COLORS: Record<VocabularyStatus, { bg: string; text: string; bar: string; label: string }> = {
  new: { bg: 'bg-gray-100', text: 'text-gray-700', bar: 'bg-gray-400', label: 'New' },
  learned: { bg: 'bg-sky-100', text: 'text-sky-800', bar: 'bg-sky-500', label: 'Learned' },
  practiced: { bg: 'bg-blue-100', text: 'text-blue-800', bar: 'bg-blue-500', label: 'Practiced' },
  recalled: { bg: 'bg-purple-100', text: 'text-purple-800', bar: 'bg-purple-500', label: 'Recalled' },
  reinforced: { bg: 'bg-indigo-100', text: 'text-indigo-800', bar: 'bg-indigo-500', label: 'Reinforced' },
  mastered: { bg: 'bg-emerald-100', text: 'text-emerald-800', bar: 'bg-emerald-500', label: 'Mastered' },
  struggling: { bg: 'bg-amber-100', text: 'text-amber-800', bar: 'bg-amber-500', label: 'Struggling' },
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [activeTrendTab, setActiveTrendTab] = useState<'weekly' | 'monthly'>('weekly')

  // 1. Fetch Dashboard Summary
  const {
    data: dashboard,
    isLoading: isLoadingDashboard,
    error: dashboardError,
    refetch: refetchDashboard,
  } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardApi.getSummary(),
  })

  // 2. Fetch Progress Overview
  const {
    data: overview,
    isLoading: isLoadingOverview,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ['progress-overview'],
    queryFn: () => progressApi.getOverview(),
  })

  // 3. Fetch Weekly Progress
  const {
    data: weeklyProgress,
    isLoading: isLoadingWeekly,
    refetch: refetchWeekly,
  } = useQuery({
    queryKey: ['progress-weekly'],
    queryFn: () => progressApi.getWeekly(),
  })

  // 4. Fetch Monthly Progress
  const {
    data: monthlyProgress,
    isLoading: isLoadingMonthly,
    refetch: refetchMonthly,
  } = useQuery({
    queryKey: ['progress-monthly'],
    queryFn: () => progressApi.getMonthly(),
  })

  // 5. Fetch Vocabulary Breakdown
  const {
    data: breakdown,
    isLoading: isLoadingBreakdown,
    refetch: refetchBreakdown,
  } = useQuery({
    queryKey: ['progress-vocabulary-breakdown'],
    queryFn: () => progressApi.getVocabularyBreakdown(),
  })

  const isLoading =
    isLoadingDashboard ||
    isLoadingOverview ||
    isLoadingWeekly ||
    isLoadingMonthly ||
    isLoadingBreakdown

  const hasError = dashboardError || overviewError

  const handleRefetchAll = () => {
    refetchDashboard()
    refetchOverview()
    refetchWeekly()
    refetchMonthly()
    refetchBreakdown()
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center py-24">
        <div className="text-center space-y-4">
          <LoadingSpinner size="lg" />
          <p className="text-sm text-gray-500 font-medium">Loading your learning analytics...</p>
        </div>
      </div>
    )
  }

  if (hasError || !dashboard || !overview) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-4xl mx-auto py-12">
          <ErrorState
            title="Failed to load dashboard"
            message="Could not retrieve your learning progress data. Please check your connection and try again."
            onRetry={handleRefetchAll}
          />
        </div>
      </div>
    )
  }

  const { today, stats, recent_activity } = dashboard
  const isBrandNewUser = stats.total_words === 0 && recent_activity.length === 0

  const dailyGoalPercent = Math.min(
    100,
    Math.round((today.daily_goal_progress / Math.max(1, today.daily_goal_target)) * 100)
  )

  const overallAccuracyDisplay = Math.round(
    ((overview.practice_accuracy + overview.recall_accuracy_rate) /
      (overview.total_practice_attempts > 0 && overview.total_reviews_completed > 0
        ? 2
        : overview.total_practice_attempts > 0
        ? 1
        : overview.total_reviews_completed > 0
        ? 1
        : 1)) *
      100
  )

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
              Learning Dashboard
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Your central hub for active recall, vocabulary mastery, and conversation practice.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/adaptive')}
              className="flex items-center gap-1.5 border-amber-300 text-amber-800 bg-amber-50 hover:bg-amber-100"
            >
              <Sparkles className="h-4 w-4 text-amber-600" />
              <span>Adaptive Plan</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/export')}
              className="flex items-center gap-1.5 border-gray-300 text-gray-700 hover:bg-gray-100"
            >
              <Download className="h-4 w-4 text-blue-600" />
              <span>Export Decks</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefetchAll}
              className="flex items-center gap-1.5"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </Button>
            <Button
              size="sm"
              onClick={() => navigate('/vocabulary')}
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white"
            >
              <BookOpen className="h-4 w-4" />
              <span>Add Word</span>
            </Button>
          </div>
        </div>

        {/* Empty state prompt for brand new accounts */}
        {isBrandNewUser && (
          <Card className="border-dashed border-2 border-blue-200 bg-blue-50/50">
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 rounded-xl text-blue-600">
                    <Sparkles className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">Welcome to KirubAI!</h3>
                    <p className="text-sm text-gray-600">
                      Add words you encounter to start scenario practice and build active recall.
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => navigate('/vocabulary')}
                  className="whitespace-nowrap bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Start Adding Words
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Section 1: "What should I do today?" */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              What should I do today?
            </h2>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/practice/multi-word')}
                className="gap-1.5 text-purple-700 border-purple-200 hover:bg-purple-50"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Use My Vocabulary</span>
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => navigate('/daily')}
                className="gap-1.5"
              >
                <span>Full Daily Routine</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Task 1: Spaced Repetition Reviews */}
            <Card
              className={`transition-all hover:border-purple-300 ${
                today.reviews_due > 0 ? 'bg-purple-50/40 border-purple-200' : 'bg-white'
              }`}
            >
              <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
                <div className="flex items-start justify-between">
                  <div className="p-2.5 bg-purple-100 rounded-lg text-purple-700">
                    <Brain className="h-5 w-5" />
                  </div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      today.reviews_due > 0
                        ? 'bg-purple-100 text-purple-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {today.reviews_due} Due
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Spaced Repetition</h3>
                  <p className="text-xs text-gray-600 mt-1">
                    {today.reviews_due > 0
                      ? `${today.reviews_due} word${today.reviews_due > 1 ? 's' : ''} scheduled for active recall review today.`
                      : 'All reviews are completed. Great work staying on schedule!'}
                  </p>
                </div>
                <Button
                  variant={today.reviews_due > 0 ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => navigate('/reviews')}
                  className={`w-full justify-between ${
                    today.reviews_due > 0
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : ''
                  }`}
                >
                  <span>{today.reviews_due > 0 ? 'Start Reviews' : 'View Review Queue'}</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            {/* Task 2: Scenario Practice */}
            <Card
              className={`transition-all hover:border-blue-300 ${
                today.words_to_practice > 0 ? 'bg-blue-50/40 border-blue-200' : 'bg-white'
              }`}
            >
              <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
                <div className="flex items-start justify-between">
                  <div className="p-2.5 bg-blue-100 rounded-lg text-blue-700">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      today.words_to_practice > 0
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {today.words_to_practice} Ready
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Scenario Practice</h3>
                  <p className="text-xs text-gray-600 mt-1">
                    {today.words_to_practice > 0
                      ? `${today.words_to_practice} word${today.words_to_practice > 1 ? 's' : ''} ready for interactive contextual scenario practice.`
                      : 'Add new vocabulary words to unlock realistic AI practice scenarios.'}
                  </p>
                </div>
                <Button
                  variant={today.words_to_practice > 0 ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => navigate('/vocabulary')}
                  className={`w-full justify-between ${
                    today.words_to_practice > 0
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : ''
                  }`}
                >
                  <span>Practice Words</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            {/* Task 3: AI Text Conversation */}
            <Card className="transition-all hover:border-indigo-300 bg-white">
              <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
                <div className="flex items-start justify-between">
                  <div className="p-2.5 bg-indigo-100 rounded-lg text-indigo-700">
                    <MessageSquare className="h-5 w-5" />
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700">
                    AI Coach
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Conversation Practice</h3>
                  <p className="text-xs text-gray-600 mt-1">
                    Chat with AI to naturally apply learned vocabulary with real-time feedback.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate('/conversations')}
                  className="w-full justify-between border-indigo-200 text-indigo-700 hover:bg-indigo-50"
                >
                  <span>Start AI Chat</span>
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Daily Goal & Word of the Day Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Daily Goal Card */}
            <Card className="lg:col-span-1">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <span>Daily Goal</span>
                  <span className="text-xs font-normal text-gray-500">
                    {today.daily_goal_progress} / {today.daily_goal_target} completed
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex justify-between text-xs font-medium text-gray-600 mb-1.5">
                    <span>Progress</span>
                    <span>{dailyGoalPercent}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                      style={{ width: `${dailyGoalPercent}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-center text-xs">
                  <div className="p-2.5 bg-gray-50 rounded-lg">
                    <p className="text-gray-500">Current Streak</p>
                    <p className="font-bold text-gray-900 text-sm mt-0.5 flex items-center justify-center gap-1">
                      <Flame className="h-4 w-4 text-orange-500" />
                      {stats.current_streak} {stats.current_streak === 1 ? 'day' : 'days'}
                    </p>
                  </div>
                  <div className="p-2.5 bg-gray-50 rounded-lg">
                    <p className="text-gray-500">Level & XP</p>
                    <p className="font-bold text-gray-900 text-sm mt-0.5 flex items-center justify-center gap-1">
                      <Award className="h-4 w-4 text-amber-500" />
                      Lvl {stats.level} ({stats.total_xp} XP)
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Word of the Day Card */}
            {today.word_of_the_day && (
              <Card className="lg:col-span-2 bg-gradient-to-br from-white to-blue-50/30 border-blue-100">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                        Word of the Day
                      </span>
                      {today.word_of_the_day.cefr_level && (
                        <span className="text-xs font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-800">
                          {today.word_of_the_day.cefr_level}
                        </span>
                      )}
                      {today.word_of_the_day.part_of_speech && (
                        <span className="text-xs text-gray-500 italic">
                          ({today.word_of_the_day.part_of_speech})
                        </span>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/vocabulary`)}
                      className="text-xs text-blue-600 hover:text-blue-700 p-0 h-auto"
                    >
                      Explore in Vocabulary <ChevronRight className="h-3 w-3 ml-0.5 inline" />
                    </Button>
                  </div>
                  <CardTitle className="text-xl font-bold text-gray-900 mt-2">
                    {today.word_of_the_day.word}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {today.word_of_the_day.meaning}
                  </p>
                  {today.word_of_the_day.example_sentence && (
                    <div className="p-3 bg-white/80 rounded-lg border border-blue-100/60 text-xs text-gray-600 italic">
                      "{today.word_of_the_day.example_sentence}"
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* Section 2: High-Level KPI Summary */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Total Words</p>
                <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
                  <BookOpen className="h-4 w-4" />
                </div>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-2">{stats.total_words}</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.active_words} active in learning loop
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Mastered</p>
                <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
                  <CheckCircle2 className="h-4 w-4" />
                </div>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-2">{stats.mastered_words}</p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.total_words > 0
                  ? `${Math.round((stats.mastered_words / stats.total_words) * 100)}% of vocabulary`
                  : '0% of vocabulary'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Accuracy Rate</p>
                <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
                  <TrendingUp className="h-4 w-4" />
                </div>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {overallAccuracyDisplay}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {overview.total_practice_attempts + overview.total_reviews_completed} total attempts
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500">Current Streak</p>
                <div className="p-2 bg-orange-50 rounded-lg text-orange-600">
                  <Flame className="h-4 w-4" />
                </div>
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-2">{stats.current_streak}</p>
              <p className="text-xs text-gray-500 mt-1">
                Longest: {overview.longest_streak} {overview.longest_streak === 1 ? 'day' : 'days'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Section 3: Vocabulary Mastery Breakdown & Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Vocabulary Distribution Card */}
          <Card className="lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-blue-600" />
                  Vocabulary Breakdown
                </span>
                <span className="text-xs text-gray-500 font-normal">
                  {breakdown?.total_words || 0} words
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {breakdown && breakdown.total_words > 0 ? (
                <div className="space-y-3">
                  {breakdown.by_status.map((item) => {
                    const statusKey = item.status as VocabularyStatus
                    const config = STATUS_COLORS[statusKey] || STATUS_COLORS.new
                    return (
                      <div key={item.status} className="space-y-1">
                        <div className="flex justify-between text-xs font-medium">
                          <span className="flex items-center gap-1.5">
                            <span className={`w-2 h-2 rounded-full ${config.bar}`} />
                            <span className="text-gray-700 capitalize">{config.label}</span>
                          </span>
                          <span className="text-gray-500">
                            {item.count} ({item.percentage}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-1.5 rounded-full ${config.bar}`}
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-gray-500">
                  No vocabulary words added yet.
                </div>
              )}

              {/* CEFR Level distribution summary */}
              {breakdown && breakdown.total_words > 0 && (
                <div className="pt-3 border-t border-gray-100">
                  <p className="text-xs font-medium text-gray-500 mb-2">CEFR Level Distribution</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(breakdown.by_cefr_level).map(([lvl, count]) => {
                      if (count === 0 && lvl === 'Unassigned') return null
                      return (
                        <span
                          key={lvl}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
                        >
                          {lvl}: <strong className="ml-1 text-gray-900">{count}</strong>
                        </span>
                      )
                    })}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Progress Trends Chart Card */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-600" />
                  Learning Activity Trends
                </CardTitle>
                <div className="flex items-center bg-gray-100 p-0.5 rounded-lg text-xs font-medium">
                  <button
                    type="button"
                    onClick={() => setActiveTrendTab('weekly')}
                    className={`px-3 py-1 rounded-md transition-colors ${
                      activeTrendTab === 'weekly'
                        ? 'bg-white text-gray-900 shadow-xs'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    7 Days
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTrendTab('monthly')}
                    className={`px-3 py-1 rounded-md transition-colors ${
                      activeTrendTab === 'monthly'
                        ? 'bg-white text-gray-900 shadow-xs'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    30 Days
                  </button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {activeTrendTab === 'weekly' ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">Practices</p>
                      <p className="font-bold text-gray-900 mt-0.5">
                        {weeklyProgress?.total_practices || 0}
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">Reviews</p>
                      <p className="font-bold text-gray-900 mt-0.5">
                        {weeklyProgress?.total_reviews || 0}
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">Active Days</p>
                      <p className="font-bold text-gray-900 mt-0.5">
                        {weeklyProgress?.active_days || 0} / 7
                      </p>
                    </div>
                  </div>

                  <div className="h-56 w-full pt-2">
                    {weeklyProgress && weeklyProgress.daily_progress.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart
                          data={weeklyProgress.daily_progress}
                          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                          <XAxis dataKey="day_name" stroke="#888888" fontSize={11} tickLine={false} />
                          <YAxis stroke="#888888" fontSize={11} tickLine={false} allowDecimals={false} />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const d = payload[0].payload
                                return (
                                  <div className="bg-gray-900 text-white p-2.5 rounded-lg shadow-lg text-xs space-y-1">
                                    <p className="font-semibold">{d.day_name} ({d.date})</p>
                                    <p className="text-blue-300">Practices: {d.practices_count}</p>
                                    <p className="text-purple-300">Reviews: {d.reviews_count}</p>
                                    <p className="text-emerald-300">XP: +{d.xp_earned}</p>
                                  </div>
                                )
                              }
                              return null
                            }}
                          />
                          <Bar dataKey="practices_count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Practices" />
                          <Bar dataKey="reviews_count" fill="#a855f7" radius={[4, 4, 0, 0]} name="Reviews" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-full text-xs text-gray-400">
                        No activity recorded this week.
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">30-Day Activities</p>
                      <p className="font-bold text-gray-900 mt-0.5">
                        {monthlyProgress?.total_activities || 0}
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">Retention Rate</p>
                      <p className="font-bold text-gray-900 mt-0.5">
                        {Math.round((monthlyProgress?.retention_rate || 0) * 100)}%
                      </p>
                    </div>
                    <div className="p-2 bg-gray-50 rounded-lg">
                      <p className="text-gray-500">Active Days</p>
                      <p className="font-bold text-gray-900 mt-0.5">
                        {monthlyProgress?.active_days || 0} / 30
                      </p>
                    </div>
                  </div>

                  <div className="h-56 w-full pt-2">
                    {monthlyProgress && monthlyProgress.trends.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                          data={monthlyProgress.trends}
                          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                        >
                          <defs>
                            <linearGradient id="activityGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                          <XAxis
                            dataKey="day_or_week"
                            stroke="#888888"
                            fontSize={10}
                            tickLine={false}
                            interval={4}
                          />
                          <YAxis stroke="#888888" fontSize={11} tickLine={false} allowDecimals={false} />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const d = payload[0].payload
                                return (
                                  <div className="bg-gray-900 text-white p-2.5 rounded-lg shadow-lg text-xs space-y-1">
                                    <p className="font-semibold">{d.day_or_week} ({d.date})</p>
                                    <p className="text-blue-300">Activities: {d.activities_count}</p>
                                    <p className="text-emerald-300">XP: +{d.xp_earned}</p>
                                  </div>
                                )
                              }
                              return null
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="activities_count"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#activityGrad)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex items-center justify-center h-full text-xs text-gray-400">
                        No monthly activity data available.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Section 4: Recent Activity & Quick Navigation */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity Timeline */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center justify-between">
                <span>Recent Learning Activity</span>
                <span className="text-xs font-normal text-gray-500">Latest 10 actions</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recent_activity.length > 0 ? (
                <div className="divide-y divide-gray-100">
                  {recent_activity.map((act, index) => {
                    return (
                      <div
                        key={`${act.type}-${act.at}-${index}`}
                        className="py-3 flex items-start justify-between gap-3 text-xs"
                      >
                        <div className="flex items-start gap-3">
                          <div
                            className={`p-2 rounded-lg mt-0.5 ${
                              act.type === 'practice'
                                ? 'bg-blue-50 text-blue-600'
                                : act.type === 'review'
                                ? 'bg-purple-50 text-purple-600'
                                : act.type === 'conversation'
                                ? 'bg-indigo-50 text-indigo-600'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {act.type === 'practice' && <Sparkles className="h-3.5 w-3.5" />}
                            {act.type === 'review' && <CheckCircle2 className="h-3.5 w-3.5" />}
                            {act.type === 'conversation' && <MessageSquare className="h-3.5 w-3.5" />}
                            {act.type === 'vocabulary' && <BookOpen className="h-3.5 w-3.5" />}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-gray-900 text-sm">
                                {act.word || 'Learning Session'}
                              </span>
                              {act.score !== null && act.score !== undefined && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700">
                                  Score: {act.score}
                                </span>
                              )}
                            </div>
                            <p className="text-gray-600 mt-0.5">{act.detail}</p>
                          </div>
                        </div>
                        <span className="text-gray-400 whitespace-nowrap text-[11px]">
                          {new Date(act.at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-gray-500">
                  No learning activity recorded yet. Start practicing to see your history!
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Hub Navigation Card */}
          <Card className="lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Explore Learning Hub</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2.5">
              <button
                type="button"
                onClick={() => navigate('/personalization')}
                className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-amber-300 hover:bg-amber-50/30 transition-all text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-amber-100 rounded-md text-amber-700">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-900 group-hover:text-amber-900">
                      Personalized Plan
                    </p>
                    <p className="text-[11px] text-gray-500">Weak words & custom scenarios</p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-amber-600 transition-colors" />
              </button>

              <button
                type="button"
                onClick={() => navigate('/knowledge')}
                className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-teal-300 hover:bg-teal-50/30 transition-all text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-teal-100 rounded-md text-teal-700">
                    <Compass className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-900 group-hover:text-teal-900">
                      Grammar & Knowledge
                    </p>
                    <p className="text-[11px] text-gray-500">Instant explanations & rules</p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-teal-600 transition-colors" />
              </button>

              <button
                type="button"
                onClick={() => navigate('/conversations')}
                className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/30 transition-all text-left group"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-indigo-100 rounded-md text-indigo-700">
                    <MessageSquare className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-900 group-hover:text-indigo-900">
                      AI Conversations
                    </p>
                    <p className="text-[11px] text-gray-500">Text conversation coaching</p>
                  </div>
                </div>
                <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-indigo-600 transition-colors" />
              </button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
