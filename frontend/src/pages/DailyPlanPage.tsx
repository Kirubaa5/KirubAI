import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Calendar,
  Flame,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  BookOpen,
  Brain,
  Target,
  Layers,
  Lock,
  RefreshCw,
} from 'lucide-react'
import { dailyApi } from '@/api/daily'
import { DailyPlanResponse, DailyTaskItem } from '@/types'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'

const TASK_ICONS: Record<string, React.ReactNode> = {
  reviews_due: <Brain className="w-5 h-5 text-indigo-600" />,
  struggling_practice: <Target className="w-5 h-5 text-amber-600" />,
  learn_new: <BookOpen className="w-5 h-5 text-emerald-600" />,
  use_my_vocabulary: <Layers className="w-5 h-5 text-purple-600" />,
}

export const DailyPlanPage: React.FC = () => {
  const navigate = useNavigate()
  const [plan, setPlan] = useState<DailyPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPlan = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await dailyApi.getDailyPlan()
      setPlan(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load daily learning plan')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPlan()
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !plan) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ErrorState
          title="Could not load Daily Plan"
          message={error || 'An error occurred'}
          onRetry={fetchPlan}
        />
      </div>
    )
  }

  // Find the first actionable pending task for the quick start button
  const nextPendingTask = plan.tasks.find(
    (t) => t.status === 'pending' || t.status === 'ready'
  )

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 translate-x-12 -translate-y-8 opacity-10 pointer-events-none">
          <Calendar className="w-80 h-80 text-white" />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-200 text-xs font-semibold uppercase tracking-wider">
              <Calendar className="w-3.5 h-3.5" />
              Daily Learning Routine • {plan.date}
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Today's Learning Plan
            </h1>
            <p className="text-blue-200 max-w-xl text-sm sm:text-base">
              Follow your prioritized sequence to lock in vocabulary retention and build active conversational fluency.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="bg-white/10 backdrop-blur-md px-4 py-3 rounded-xl border border-white/10 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
                <Flame className="w-6 h-6" />
              </div>
              <div>
                <div className="text-xs text-blue-200 uppercase font-bold tracking-wider">Streak</div>
                <div className="text-xl font-black text-white">{plan.current_streak} {plan.current_streak === 1 ? 'Day' : 'Days'}</div>
              </div>
            </div>

            {nextPendingTask && (
              <Button
                variant="primary"
                size="lg"
                onClick={() => navigate(nextPendingTask.action_url)}
                className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold shadow-lg shadow-emerald-900/30 gap-2"
              >
                <span>Start Next: {nextPendingTask.title}</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Daily Goal Progress Bar */}
        <div className="mt-8 pt-6 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-4 items-center">
          <div className="sm:col-span-2 space-y-2">
            <div className="flex justify-between text-xs font-semibold text-blue-200">
              <span>Daily Goal Progress</span>
              <span>
                {plan.daily_goal_progress} / {plan.daily_goal_target} Activities
                {plan.is_goal_completed && ' • Completed (+25 XP awarded!)'}
              </span>
            </div>
            <div className="w-full bg-white/15 h-3 rounded-full overflow-hidden p-0.5">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  plan.is_goal_completed
                    ? 'bg-gradient-to-r from-emerald-400 to-teal-300 shadow-sm shadow-emerald-400/50'
                    : 'bg-gradient-to-r from-blue-400 to-indigo-300'
                }`}
                style={{
                  width: `${Math.min(
                    100,
                    Math.round((plan.daily_goal_progress / Math.max(1, plan.daily_goal_target)) * 100)
                  )}%`,
                }}
              />
            </div>
          </div>

          <div className="flex sm:justify-end items-center gap-2">
            <div className="text-xs text-blue-200">Task Completion:</div>
            <div className="text-sm font-bold text-white bg-white/10 px-2.5 py-1 rounded-md border border-white/10">
              {plan.completed_tasks_count} / {plan.total_tasks_count} Tasks ({plan.completion_percentage}%)
            </div>
          </div>
        </div>
      </div>

      {/* Word of the Day Banner */}
      {plan.word_of_the_day && (
        <Card className="border-indigo-100 dark:border-indigo-900/40 bg-gradient-to-br from-indigo-50/50 via-white to-blue-50/30 dark:from-slate-900 dark:via-slate-900 dark:to-indigo-950/20 shadow-sm">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider">
                  <Sparkles className="w-3.5 h-3.5" />
                  Word of the Day
                </div>
                <div className="flex items-baseline gap-3">
                  <span className="text-2xl font-black text-slate-900 dark:text-white capitalize">
                    {plan.word_of_the_day.word}
                  </span>
                  {plan.word_of_the_day.cefr_level && (
                    <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300">
                      {plan.word_of_the_day.cefr_level}
                    </span>
                  )}
                  {plan.word_of_the_day.part_of_speech && (
                    <span className="text-xs text-slate-500 italic">
                      {plan.word_of_the_day.part_of_speech}
                    </span>
                  )}
                </div>
                <p className="text-slate-700 dark:text-slate-300 text-sm">
                  {plan.word_of_the_day.meaning}
                </p>
                {plan.word_of_the_day.example_sentence && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic border-l-2 border-indigo-400 pl-2 mt-1">
                    "{plan.word_of_the_day.example_sentence}"
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/learn?word=${plan.word_of_the_day?.word}`)}
                >
                  View Details
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => navigate(`/practice?word=${plan.word_of_the_day?.word}`)}
                >
                  Practice Word
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Prioritized Daily Routine Tasks */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              Prioritized Task Routine
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Structured in cognitive order: Retention (Reviews) → Improvement (Struggling) → Growth (New) → Synthesis (Multi-Word).
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchPlan} className="gap-1.5 text-slate-500">
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {plan.tasks.map((task: DailyTaskItem) => {
            const isCompleted = task.status === 'completed'
            const isLocked = task.status === 'locked'

            return (
              <Card
                key={task.id}
                className={`transition-all duration-200 border ${
                  isCompleted
                    ? 'border-emerald-200 dark:border-emerald-900/30 bg-emerald-50/20 dark:bg-emerald-950/10'
                    : isLocked
                    ? 'border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 opacity-80'
                    : 'border-blue-200 dark:border-blue-900/50 bg-white dark:bg-slate-900 shadow-md ring-1 ring-blue-500/10'
                }`}
              >
                <CardContent className="p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      {/* Priority Tag & Icon */}
                      <div className="flex flex-col items-center justify-center shrink-0">
                        <div
                          className={`w-12 h-12 rounded-xl flex items-center justify-center border shadow-sm ${
                            isCompleted
                              ? 'bg-emerald-100 border-emerald-300 dark:bg-emerald-900/30 dark:border-emerald-700'
                              : isLocked
                              ? 'bg-slate-100 border-slate-300 dark:bg-slate-800 dark:border-slate-700 text-slate-400'
                              : 'bg-blue-50 border-blue-200 dark:bg-blue-950/50 dark:border-blue-800'
                          }`}
                        >
                          {isCompleted ? (
                            <CheckCircle2 className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                          ) : isLocked ? (
                            <Lock className="w-5 h-5 text-slate-400" />
                          ) : (
                            TASK_ICONS[task.task_type] || <Clock className="w-5 h-5 text-blue-600" />
                          )}
                        </div>
                        <span className="text-[10px] font-black uppercase tracking-wider text-slate-400 dark:text-slate-500 mt-1">
                          P{task.priority}
                        </span>
                      </div>

                      {/* Task Info */}
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-bold text-base text-slate-900 dark:text-white">
                            {task.title}
                          </h3>
                          <span
                            className={`text-[11px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                              isCompleted
                                ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
                                : isLocked
                                ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                                : 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300'
                            }`}
                          >
                            {task.status}
                          </span>
                        </div>

                        <p className="text-sm text-slate-600 dark:text-slate-300">
                          {task.description}
                        </p>

                        {/* Associated Word Chips if any */}
                        {task.items && task.items.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 pt-1">
                            {task.items.map((item) => (
                              <span
                                key={item.id}
                                className="inline-flex items-center text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium"
                              >
                                {item.word}
                                {item.status && (
                                  <span className="ml-1 text-[10px] text-slate-400">
                                    ({item.status})
                                  </span>
                                )}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Action Button */}
                    <div className="sm:self-center shrink-0">
                      <Button
                        variant={isCompleted ? 'outline' : isLocked ? 'secondary' : 'primary'}
                        size="md"
                        onClick={() => navigate(task.action_url)}
                        disabled={isLocked && task.item_count === 0}
                        className="w-full sm:w-auto"
                      >
                        {task.action_label}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
export default DailyPlanPage
