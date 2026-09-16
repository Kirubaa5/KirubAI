import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Trophy,
  Award,
  Flame,
  Target,
  Brain,
  MessageSquare,
  BookOpen,
  Bookmark,
  Library,
  Zap,
  Sparkles,
  Repeat,
  MessageCircle,
  Mic,
  Star,
  Crown,
  Lock,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Milestone,
  Calendar,
} from 'lucide-react'

import { gamificationApi } from '@/api/gamification'
import { Achievement } from '@/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'

type FilterCategory = 'all' | 'vocabulary' | 'practice' | 'reviews' | 'conversations' | 'streaks'

const ICON_MAP: Record<string, React.ElementType> = {
  BookOpen,
  Bookmark,
  Library,
  Target,
  Zap,
  Award,
  Brain,
  Sparkles,
  Repeat,
  MessageSquare,
  MessageCircle,
  Mic,
  Trophy,
  Star,
  Flame,
  Crown,
}

const CATEGORY_LABELS: Record<FilterCategory, string> = {
  all: 'All',
  vocabulary: 'Vocabulary',
  practice: 'Practice',
  reviews: 'Reviews',
  conversations: 'Conversations',
  streaks: 'Streaks & Mastery',
}

export function AchievementsPage() {
  const [selectedCategory, setSelectedCategory] = useState<FilterCategory>('all')
  const [showRoadmap, setShowRoadmap] = useState(false)

  // 1. Fetch Overview
  const {
    data: overview,
    isLoading: isLoadingOverview,
    error: overviewError,
    refetch: refetchOverview,
  } = useQuery({
    queryKey: ['gamification-overview'],
    queryFn: () => gamificationApi.getOverview(),
  })

  // 2. Fetch Achievements
  const {
    data: achievementsData,
    isLoading: isLoadingAchievements,
    error: achievementsError,
    refetch: refetchAchievements,
  } = useQuery({
    queryKey: ['gamification-achievements'],
    queryFn: () => gamificationApi.getAchievements(),
  })

  // 3. Fetch Level Roadmap
  const {
    data: levelsData,
    refetch: refetchLevels,
  } = useQuery({
    queryKey: ['gamification-levels'],
    queryFn: () => gamificationApi.getLevels(),
  })

  const isLoading = isLoadingOverview || isLoadingAchievements
  const hasError = overviewError || achievementsError

  const handleRefresh = () => {
    refetchOverview()
    refetchAchievements()
    refetchLevels()
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 flex flex-col items-center justify-center gap-3">
        <LoadingSpinner size="lg" className="text-blue-600" />
        <p className="text-sm text-gray-500 font-medium">Loading achievements & level progression...</p>
      </div>
    )
  }

  if (hasError || !overview || !achievementsData) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <ErrorState
          title="Could not load achievements"
          message="An error occurred while fetching your gamification details."
          onRetry={handleRefresh}
        />
      </div>
    )
  }

  const allAchievements = achievementsData.items || []

  // Filter achievements
  const filteredAchievements = allAchievements.filter((a) => {
    if (selectedCategory === 'all') return true
    return a.category.toLowerCase() === selectedCategory.toLowerCase()
  })

  const categoryCounts = (cat: FilterCategory) => {
    if (cat === 'all') return allAchievements.length
    return allAchievements.filter((a) => a.category.toLowerCase() === cat.toLowerCase()).length
  }

  const categoryUnlockedCounts = (cat: FilterCategory) => {
    if (cat === 'all') return allAchievements.filter((a) => a.is_unlocked).length
    return allAchievements.filter((a) => a.category.toLowerCase() === cat.toLowerCase() && a.is_unlocked).length
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Trophy className="h-7 w-7 text-amber-500" />
            Gamification & Achievements
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Track your XP, level progression, learning streaks, and unlock milestones.
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={handleRefresh}
          className="flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Level & XP Hero Card */}
      <Card className="border-blue-100 bg-white shadow-sm overflow-hidden">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            {/* Left: Level Info */}
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-2xl bg-blue-600 text-white flex flex-col items-center justify-center shadow-md font-bold shrink-0">
                <span className="text-xs uppercase tracking-wider text-blue-200">LVL</span>
                <span className="text-2xl leading-none">{overview.level}</span>
              </div>
              <div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  Level {overview.level}
                </span>
                <h2 className="text-xl font-bold text-gray-900 mt-0.5">{overview.level_title}</h2>
                <p className="text-xs text-gray-500 mt-0.5">
                  Total XP Earned:{' '}
                  <span className="font-semibold text-gray-700">{overview.total_xp} XP</span>
                </p>
              </div>
            </div>

            {/* Middle: Level Progress */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-medium text-gray-600">
                <span>
                  Level Progress:{' '}
                  <span className="text-blue-600 font-semibold">
                    {overview.xp_within_level} / 100 XP
                  </span>
                </span>
                <span>{overview.level_progress_percentage}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${overview.level_progress_percentage}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 text-right">
                {overview.next_level_xp - overview.total_xp} XP needed for Level{' '}
                {overview.level + 1}
              </p>
            </div>

            {/* Right: Streaks & Daily Goal */}
            <div className="flex flex-wrap sm:flex-nowrap items-center justify-start lg:justify-end gap-3 pt-2 lg:pt-0 border-t lg:border-t-0 border-gray-100">
              {/* Streak Badge */}
              <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
                <Flame className="h-5 w-5 text-amber-500 shrink-0" />
                <div>
                  <div className="text-xs text-amber-800 font-medium">Daily Streak</div>
                  <div className="text-sm font-bold text-amber-900">
                    {overview.current_streak} days{' '}
                    <span className="text-xs font-normal text-amber-700">
                      (Best: {overview.longest_streak})
                    </span>
                  </div>
                </div>
              </div>

              {/* Daily Goal Badge */}
              <div
                className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
                  overview.is_daily_goal_completed
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                    : 'bg-gray-50 border-gray-200 text-gray-900'
                }`}
              >
                <CheckCircle2
                  className={`h-5 w-5 shrink-0 ${
                    overview.is_daily_goal_completed ? 'text-emerald-600' : 'text-gray-400'
                  }`}
                />
                <div>
                  <div className="text-xs font-medium text-gray-600">Daily Goal</div>
                  <div className="text-sm font-bold">
                    {overview.daily_goal_progress} / {overview.daily_goal}{' '}
                    {overview.is_daily_goal_completed && (
                      <span className="text-xs text-emerald-700 font-semibold">Done!</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Level Roadmap Section (Collapsible) */}
      <Card className="border-gray-200 shadow-sm">
        <CardHeader
          className="py-4 px-6 cursor-pointer select-none flex flex-row items-center justify-between hover:bg-gray-50 transition-colors"
          onClick={() => setShowRoadmap(!showRoadmap)}
        >
          <div className="flex items-center gap-2">
            <Milestone className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-base font-semibold text-gray-900">
              Level Roadmap & Milestones
            </CardTitle>
          </div>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
            {showRoadmap ? (
              <ChevronUp className="h-5 w-5 text-gray-500" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-500" />
            )}
          </Button>
        </CardHeader>
        {showRoadmap && (
          <CardContent className="px-6 pb-6 pt-2 border-t border-gray-100">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3 mt-4">
              {(levelsData?.levels || []).map((lvl) => (
                <div
                  key={lvl.level}
                  className={`p-3 rounded-xl border text-sm transition-all ${
                    lvl.is_current
                      ? 'border-blue-500 bg-blue-50/70 shadow-sm ring-1 ring-blue-400'
                      : lvl.is_unlocked
                      ? 'border-emerald-200 bg-emerald-50/40 text-gray-800'
                      : 'border-gray-200 bg-gray-50/60 text-gray-400 opacity-75'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        lvl.is_current
                          ? 'bg-blue-600 text-white'
                          : lvl.is_unlocked
                          ? 'bg-emerald-600 text-white'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      Level {lvl.level}
                    </span>
                    <span className="text-xs font-medium text-gray-500">
                      {lvl.xp_required} XP
                    </span>
                  </div>
                  <div className="font-semibold text-gray-900 truncate">{lvl.title}</div>
                  <div className="text-xs mt-1">
                    {lvl.is_current ? (
                      <span className="text-blue-700 font-semibold">Current Level</span>
                    ) : lvl.is_unlocked ? (
                      <span className="text-emerald-700 font-medium">Unlocked</span>
                    ) : (
                      <span className="text-gray-400">Locked</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Achievements Header & Progress Summary */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Curated Achievements</h2>
            <p className="text-xs text-gray-500">
              Complete learning activities, practice scenarios, and active recall reviews to unlock badges.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs font-medium text-gray-500">Total Unlocked</div>
              <div className="text-sm font-bold text-gray-900">
                {overview.unlocked_achievements_count} of {overview.total_achievements_count} ({overview.achievement_completion_percentage}%)
              </div>
            </div>
            <div className="w-28 bg-gray-200 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-amber-500 h-2.5 rounded-full"
                style={{ width: `${overview.achievement_completion_percentage}%` }}
              />
            </div>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-gray-200">
          {(Object.keys(CATEGORY_LABELS) as FilterCategory[]).map((cat) => {
            const isSelected = selectedCategory === cat
            const count = categoryCounts(cat)
            const unlocked = categoryUnlockedCounts(cat)
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3.5 py-1.5 rounded-lg text-xs sm:text-sm font-medium whitespace-nowrap transition-colors flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <span>{CATEGORY_LABELS[cat]}</span>
                <span
                  className={`text-xs px-1.5 py-0.2 rounded-full ${
                    isSelected
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {unlocked}/{count}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Achievement Cards Grid */}
      {filteredAchievements.length === 0 ? (
        <EmptyState
          title="No achievements in this category"
          message="Try selecting a different filter category above."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAchievements.map((achievement: Achievement) => {
            const IconComponent = ICON_MAP[achievement.icon] || Award
            const isUnlocked = achievement.is_unlocked

            return (
              <Card
                key={achievement.key}
                className={`transition-all overflow-hidden border ${
                  isUnlocked
                    ? 'border-emerald-200 bg-white shadow-sm ring-1 ring-emerald-100'
                    : 'border-gray-200 bg-gray-50/50'
                }`}
              >
                <CardContent className="p-5 flex flex-col justify-between h-full">
                  <div>
                    {/* Card Top Row: Icon + Status Pill */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div
                        className={`h-11 w-11 rounded-xl flex items-center justify-center shrink-0 ${
                          isUnlocked
                            ? 'bg-amber-100 text-amber-700 shadow-xs'
                            : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                        <IconComponent className="h-6 w-6" />
                      </div>

                      {isUnlocked ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Unlocked
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-600">
                          <Lock className="h-3.5 w-3.5" />
                          Locked
                        </span>
                      )}
                    </div>

                    {/* Title & Description */}
                    <h3 className="font-bold text-gray-900 text-base">{achievement.title}</h3>
                    <p className="text-xs text-gray-600 mt-1 leading-relaxed">
                      {achievement.description}
                    </p>
                  </div>

                  {/* Card Bottom Row: Progress or Unlock Date */}
                  <div className="mt-4 pt-3 border-t border-gray-100">
                    {isUnlocked ? (
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span className="flex items-center gap-1 text-emerald-700 font-medium">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Completed
                        </span>
                        {achievement.achieved_at && (
                          <span className="flex items-center gap-1 text-gray-400">
                            <Calendar className="h-3 w-3" />
                            {formatDate(achievement.achieved_at)}
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="space-y-1.5">
                        <div className="flex justify-between text-xs text-gray-600">
                          <span>
                            Progress:{' '}
                            <span className="font-semibold text-gray-900">
                              {achievement.current_progress} / {achievement.target_threshold}
                            </span>
                          </span>
                          <span className="font-medium text-gray-500">
                            {achievement.progress_percentage}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${achievement.progress_percentage}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default AchievementsPage
