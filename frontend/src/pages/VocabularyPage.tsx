import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vocabularyApi } from '@/api/vocabulary'
import { Vocabulary, VocabularyStatus } from '@/types'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent } from '@/components/ui/Card'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { ErrorState } from '@/components/common/ErrorState'
import { Plus, Search, Trash2, BookOpen } from 'lucide-react'

const statusColors: Record<VocabularyStatus, { bg: string; text: string; label: string }> = {
  new: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'New' },
  learned: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Learned' },
  practiced: { bg: 'bg-indigo-100', text: 'text-indigo-700', label: 'Practiced' },
  recalled: { bg: 'bg-purple-100', text: 'text-purple-700', label: 'Recalled' },
  reinforced: { bg: 'bg-amber-100', text: 'text-amber-700', label: 'Reinforced' },
  mastered: { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Mastered' },
  struggling: { bg: 'bg-red-100', text: 'text-red-700', label: 'Struggling' },
}

export function VocabularyPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [newWord, setNewWord] = useState('')
  const [isAdding, setIsAdding] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['vocabulary', { search: searchTerm, status: selectedStatus }],
    queryFn: () =>
      vocabularyApi.list({
        search: searchTerm || undefined,
        status: selectedStatus || undefined,
        per_page: 50,
      }),
  })

  const addMutation = useMutation({
    mutationFn: (word: string) => vocabularyApi.add(word),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] })
      setNewWord('')
      setIsAdding(false)
      setFormError(null)
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || 'Failed to add word')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => vocabularyApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vocabulary'] })
    },
  })

  const handleAddWord = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newWord.trim()) return
    addMutation.mutate(newWord.trim())
  }

  const items = data?.items || []

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">My Vocabulary</h1>
            <p className="mt-1 text-sm text-gray-500">
              Track, practice, and master your English vocabulary
            </p>
          </div>
          <Button onClick={() => setIsAdding(!isAdding)} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add New Word
          </Button>
        </div>

        {/* Add Word Modal/Inline form */}
        {isAdding && (
          <Card className="mb-8 border-blue-200 bg-blue-50/50">
            <CardContent className="pt-6">
              <form onSubmit={handleAddWord} className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1">
                  <Input
                    placeholder="Enter an English word (e.g., hesitate, resilient)..."
                    value={newWord}
                    onChange={(e) => {
                      setNewWord(e.target.value)
                      setFormError(null)
                    }}
                    error={formError || undefined}
                    autoFocus
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" disabled={addMutation.isPending || !newWord.trim()}>
                    {addMutation.isPending ? 'Adding...' : 'Add Word'}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setIsAdding(false)
                      setFormError(null)
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Filters and Search */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search words..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {['', 'new', 'learned', 'practiced', 'recalled', 'reinforced', 'mastered', 'struggling'].map(
              (status) => (
                <button
                  key={status}
                  onClick={() => setSelectedStatus(status)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${
                    selectedStatus === status
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {status === '' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              )
            )}
          </div>
        </div>

        {/* Main Content Area */}
        {isLoading ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <ErrorState
            title="Failed to load vocabulary"
            message="There was an error loading your vocabulary list. Please try again."
            onRetry={() => refetch()}
          />
        ) : items.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="h-12 w-12" />}
            title={searchTerm || selectedStatus ? 'No words match your filter' : 'No words added yet'}
            message={
              searchTerm || selectedStatus
                ? 'Try changing your search term or status filter.'
                : 'Start turning passive words into active vocabulary by adding your first word!'
            }
            action={
              !searchTerm && !selectedStatus ? (
                <Button onClick={() => setIsAdding(true)} className="mt-4">
                  Add Your First Word
                </Button>
              ) : null
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((vocab: Vocabulary) => {
              const statusCfg = statusColors[vocab.status] || statusColors.new
              const masteryPercent = Math.round(vocab.mastery_score * 100)

              return (
                <Card key={vocab.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 capitalize">{vocab.word}</h3>
                        <span
                          className={`inline-block px-2 py-0.5 mt-1 text-xs font-semibold rounded-full ${statusCfg.bg} ${statusCfg.text}`}
                        >
                          {statusCfg.label}
                        </span>
                      </div>
                      <button
                        onClick={() => deleteMutation.mutate(vocab.id)}
                        className="text-gray-400 hover:text-red-600 transition-colors p-1"
                        title="Delete word"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    {/* Mastery progress */}
                    <div className="mt-4">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>Mastery</span>
                        <span className="font-medium text-gray-700">{masteryPercent}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            masteryPercent >= 80
                              ? 'bg-emerald-500'
                              : masteryPercent >= 50
                              ? 'bg-blue-500'
                              : 'bg-indigo-400'
                          }`}
                          style={{ width: `${Math.max(masteryPercent, 5)}%` }}
                        />
                      </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-gray-100 text-xs text-gray-500">
                      <div>
                        Practice Attempts:{' '}
                        <span className="font-semibold text-gray-700">{vocab.practice_count}</span>
                      </div>
                      <div>
                        Successful Uses:{' '}
                        <span className="font-semibold text-gray-700">
                          {vocab.successful_usage_count}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-end">
                      <Link
                        to={`/vocabulary/${vocab.id}/learn`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
                      >
                        <BookOpen className="h-3.5 w-3.5" />
                        {vocab.status === 'new' ? 'Learn Word' : 'Review Explanation'}
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
