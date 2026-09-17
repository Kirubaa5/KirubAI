import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Download,
  FileSpreadsheet,
  FileCode,
  Layers,
  CheckCircle2,
  AlertCircle,
  Brain,
  Filter,
  ArrowLeft,
  Sparkles,
  BookOpen,
  RefreshCw,
} from 'lucide-react'

import { exportApi } from '@/api/export'
import { ExportFormat, ExportFilterParams } from '@/types'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'

const FORMAT_CONFIG: Record<
  ExportFormat,
  {
    title: string
    extension: string
    badge: string
    description: string
    icon: React.ElementType
    features: string[]
  }
> = {
  anki: {
    title: 'Anki Flashcard Deck',
    extension: '.txt / .tsv',
    badge: 'Spaced Repetition',
    description: 'Formatted import-ready study cards with styling, meanings, collocations, examples, and tags.',
    icon: Layers,
    features: ['Front/back styled cards', 'CEFR & status tags', 'Import into Anki Desktop & Mobile'],
  },
  csv: {
    title: 'CSV Spreadsheet',
    extension: '.csv',
    badge: 'Spreadsheets & Tables',
    description: 'Standard UTF-8 comma-separated spreadsheet with full vocabulary details and learning metrics.',
    icon: FileSpreadsheet,
    features: ['Excel & Google Sheets compatible', 'Full word details & forms', 'Learning history & metrics'],
  },
  json: {
    title: 'JSON Data Archive',
    extension: '.json',
    badge: 'Complete Backup',
    description: 'Structured JSON archive of all word definitions, example sentences, practice metrics, and review queues.',
    icon: FileCode,
    features: ['Complete raw data fidelity', 'Developers & integrations', 'Easy database portability'],
  },
}

const STATUS_FILTERS = [
  { value: 'all', label: 'All Words' },
  { value: 'active', label: 'Active Learning' },
  { value: 'mastered', label: 'Mastered' },
  { value: 'struggling', label: 'Struggling' },
  { value: 'due', label: 'Due for Review' },
  { value: 'new', label: 'New' },
  { value: 'learned', label: 'Learned' },
  { value: 'practiced', label: 'Practiced' },
  { value: 'recalled', label: 'Recalled' },
  { value: 'reinforced', label: 'Reinforced' },
]

const CEFR_FILTERS = [
  { value: 'all', label: 'All CEFR Levels' },
  { value: 'A1', label: 'A1 - Beginner' },
  { value: 'A2', label: 'A2 - Elementary' },
  { value: 'B1', label: 'B1 - Intermediate' },
  { value: 'B2', label: 'B2 - Upper Intermediate' },
  { value: 'C1', label: 'C1 - Advanced' },
  { value: 'C2', label: 'C2 - Mastery' },
]

const MASTERY_FILTERS = [
  { value: 'all', label: 'All Mastery Levels' },
  { value: 'low', label: 'Beginner (<30%)', min: 0.0, max: 0.3 },
  { value: 'medium', label: 'Developing (30% - 70%)', min: 0.3, max: 0.7 },
  { value: 'high', label: 'High Mastery (>70%)', min: 0.7, max: 1.0 },
]

export function ExportPage() {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('anki')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedCefr, setSelectedCefr] = useState<string>('all')
  const [selectedMasteryBracket, setSelectedMasteryBracket] = useState<string>('all')
  const [includeExamples, setIncludeExamples] = useState<boolean>(true)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  // Construct active filter params
  const activeMastery = MASTERY_FILTERS.find((m) => m.value === selectedMasteryBracket)
  const filterParams: ExportFilterParams = {
    status: selectedStatus === 'all' ? undefined : selectedStatus,
    cefr_level: selectedCefr === 'all' ? undefined : selectedCefr,
    min_mastery: activeMastery?.min,
    max_mastery: activeMastery?.max,
    include_examples: includeExamples,
  }

  // 1. Fetch live preview counts and distributions
  const {
    data: preview,
    isLoading: isLoadingPreview,
    error: previewError,
    refetch: refetchPreview,
  } = useQuery({
    queryKey: ['export-preview', selectedStatus, selectedCefr, selectedMasteryBracket, includeExamples],
    queryFn: () => exportApi.getPreview(filterParams),
  })

  // 2. Export download mutation
  const downloadMutation = useMutation({
    mutationFn: async () => {
      setSuccessMessage(null)
      setExportError(null)
      return exportApi.download(selectedFormat, filterParams)
    },
    onSuccess: (result) => {
      const wordCount = preview?.matching_words_count ?? 0
      setSuccessMessage(`Export complete! Downloaded ${wordCount} words to ${result.filename}.`)
      setTimeout(() => setSuccessMessage(null), 8000)
    },
    onError: (err: any) => {
      setExportError(err?.response?.data?.detail || err?.message || 'Failed to generate export file.')
    },
  })

  const matchingCount = preview?.matching_words_count ?? 0
  const isGenerating = downloadMutation.isPending

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
              <Link to="/vocabulary" className="hover:text-blue-600 flex items-center gap-1 transition-colors">
                <ArrowLeft className="h-4 w-4" />
                Vocabulary
              </Link>
              <span>/</span>
              <span className="text-gray-900 font-medium">Export & Study Decks</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl flex items-center gap-2">
              <Download className="h-7 w-7 text-blue-600" />
              Export & Study Deck Generator
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Export your English vocabulary, example sentences, and spaced repetition data for Anki or spreadsheets.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link to="/vocabulary">
              <Button variant="outline" size="sm" className="flex items-center gap-1.5">
                <BookOpen className="h-4 w-4 text-gray-600" />
                Manage Words
              </Button>
            </Link>
            <Link to="/reviews">
              <Button variant="outline" size="sm" className="flex items-center gap-1.5 border-purple-300 text-purple-700 bg-purple-50 hover:bg-purple-100">
                <Brain className="h-4 w-4 text-purple-600" />
                Study Reviews
              </Button>
            </Link>
          </div>
        </div>

        {/* Feedback alerts */}
        {successMessage && (
          <div className="mb-6 p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold">Download Successful</p>
              <p className="text-xs text-emerald-700 mt-0.5">{successMessage}</p>
            </div>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-xs font-semibold text-emerald-700 hover:text-emerald-900"
            >
              Dismiss
            </button>
          </div>
        )}

        {exportError && (
          <div className="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-800 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-semibold">Export Failed</p>
              <p className="text-xs text-red-700 mt-0.5">{exportError}</p>
            </div>
            <button
              onClick={() => setExportError(null)}
              className="text-xs font-semibold text-red-700 hover:text-red-900"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Format Selection Grid */}
        <div className="mb-8">
          <h2 className="text-base font-semibold text-gray-900 mb-3">1. Select Export Format</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {(Object.keys(FORMAT_CONFIG) as ExportFormat[]).map((format) => {
              const cfg = FORMAT_CONFIG[format]
              const Icon = cfg.icon
              const isSelected = selectedFormat === format

              return (
                <div
                  key={format}
                  onClick={() => setSelectedFormat(format)}
                  className={`cursor-pointer rounded-xl border p-5 transition-all bg-white flex flex-col justify-between ${
                    isSelected
                      ? 'border-blue-600 ring-2 ring-blue-600/20 shadow-sm'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <div
                        className={`p-2.5 rounded-lg ${
                          isSelected ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 border border-gray-200">
                        {cfg.extension}
                      </span>
                    </div>
                    <h3 className="font-semibold text-gray-900 text-base">{cfg.title}</h3>
                    <p className="text-xs text-gray-500 mt-1">{cfg.description}</p>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <ul className="space-y-1 text-xs text-gray-600">
                      {cfg.features.map((feat, idx) => (
                        <li key={idx} className="flex items-center gap-1.5">
                          <CheckCircle2 className="h-3.5 w-3.5 text-blue-600 shrink-0" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Filter Configuration & Preview Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-8">
          {/* Left Column: Filter Controls (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <Card>
              <CardHeader className="pb-3 border-b border-gray-100">
                <CardTitle className="text-base flex items-center gap-2 text-gray-900">
                  <Filter className="h-4 w-4 text-blue-600" />
                  2. Choose Vocabulary Filters
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-5">
                {/* Status Filter */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">
                    Learning Status
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {STATUS_FILTERS.map((s) => (
                      <button
                        key={s.value}
                        type="button"
                        onClick={() => setSelectedStatus(s.value)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          selectedStatus === s.value
                            ? 'bg-blue-600 text-white shadow-xs'
                            : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100'
                        }`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* CEFR Filter */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">
                    CEFR Proficiency Level
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {CEFR_FILTERS.map((c) => (
                      <button
                        key={c.value}
                        type="button"
                        onClick={() => setSelectedCefr(c.value)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          selectedCefr === c.value
                            ? 'bg-indigo-600 text-white shadow-xs'
                            : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-100'
                        }`}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Mastery Filter */}
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">
                    Mastery Score Range
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {MASTERY_FILTERS.map((m) => (
                      <button
                        key={m.value}
                        type="button"
                        onClick={() => setSelectedMasteryBracket(m.value)}
                        className={`px-3 py-2 text-xs font-medium rounded-lg text-left transition-colors border ${
                          selectedMasteryBracket === m.value
                            ? 'bg-blue-50 border-blue-600 text-blue-900 font-semibold'
                            : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {m.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Options toggle */}
                <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-medium text-gray-900">Include Example Sentences</p>
                    <p className="text-xs text-gray-500">Include real-world conversational examples with cards</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={includeExamples}
                    onChange={(e) => setIncludeExamples(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Real-time Deck Preview & Download Button (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <Card className="border-gray-200 bg-white shadow-xs">
              <CardHeader className="pb-3 border-b border-gray-100">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base text-gray-900 flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-amber-500" />
                    Deck Summary
                  </CardTitle>
                  <button
                    onClick={() => refetchPreview()}
                    title="Refresh summary"
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                {isLoadingPreview ? (
                  <div className="flex justify-center py-8">
                    <LoadingSpinner size="md" />
                  </div>
                ) : previewError ? (
                  <ErrorState
                    title="Could not load preview"
                    message="Failed to calculate export preview metrics."
                    onRetry={() => refetchPreview()}
                  />
                ) : (
                  <>
                    {/* Metric pill */}
                    <div className="p-4 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-between">
                      <div>
                        <span className="text-xs font-medium text-blue-800">Words Selected</span>
                        <div className="text-2xl font-extrabold text-blue-900 mt-0.5">
                          {matchingCount}
                          <span className="text-xs font-normal text-blue-600 ml-1.5">
                            of {preview?.total_vocabulary_count ?? 0} total
                          </span>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-medium text-blue-800">Export Format</span>
                        <div className="text-sm font-bold text-blue-900 uppercase">
                          {selectedFormat}
                        </div>
                      </div>
                    </div>

                    {/* Status & CEFR breakdowns */}
                    {matchingCount > 0 ? (
                      <div className="space-y-3">
                        {/* CEFR Level distribution */}
                        {preview?.cefr_distribution && Object.keys(preview.cefr_distribution).length > 0 && (
                          <div>
                            <span className="text-xs font-medium text-gray-500 block mb-1.5">
                              CEFR Breakdown:
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {Object.entries(preview.cefr_distribution).map(([level, count]) => (
                                <span
                                  key={level}
                                  className="text-xs px-2 py-0.5 rounded-md bg-gray-100 text-gray-700 font-medium"
                                >
                                  <span className="font-semibold text-gray-900">{level}:</span> {count}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Status distribution */}
                        {preview?.status_distribution && Object.keys(preview.status_distribution).length > 0 && (
                          <div>
                            <span className="text-xs font-medium text-gray-500 block mb-1.5">
                              Status Distribution:
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {Object.entries(preview.status_distribution).map(([status, count]) => (
                                <span
                                  key={status}
                                  className="text-xs px-2 py-0.5 rounded-md bg-gray-100 text-gray-700 capitalize"
                                >
                                  {status}: <strong className="text-gray-900">{count}</strong>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Sample words preview */}
                        {preview?.sample_words && preview.sample_words.length > 0 && (
                          <div>
                            <span className="text-xs font-medium text-gray-500 block mb-1.5">
                              Sample Words in Export:
                            </span>
                            <div className="flex flex-wrap gap-1">
                              {preview.sample_words.map((word) => (
                                <span
                                  key={word}
                                  className="text-xs px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-100 font-medium"
                                >
                                  {word}
                                </span>
                              ))}
                              {matchingCount > preview.sample_words.length && (
                                <span className="text-xs px-2 py-0.5 text-gray-500 italic">
                                  +{matchingCount - preview.sample_words.length} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <EmptyState
                        icon={<BookOpen className="h-8 w-8 text-gray-400" />}
                        title="No matching words"
                        message="No vocabulary words match the selected filters. Broaden your criteria to generate an export."
                      />
                    )}

                    {/* Download Action Button */}
                    <div className="pt-2">
                      <Button
                        className="w-full py-3 flex items-center justify-center gap-2 text-sm font-semibold"
                        disabled={matchingCount === 0 || isGenerating}
                        onClick={() => downloadMutation.mutate()}
                      >
                        {isGenerating ? (
                          <>
                            <LoadingSpinner size="sm" />
                            <span>Generating {FORMAT_CONFIG[selectedFormat].title}...</span>
                          </>
                        ) : (
                          <>
                            <Download className="h-4 w-4" />
                            <span>
                              Download {FORMAT_CONFIG[selectedFormat].title} ({matchingCount} words)
                            </span>
                          </>
                        )}
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExportPage
