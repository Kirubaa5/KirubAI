import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Search,
  BookOpen,
  CheckCircle2,
  XCircle,
  Lightbulb,
  ShieldCheck,
  FileText,
  HelpCircle,
  Sparkles,
  ChevronRight,
  X,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorState } from '@/components/common/ErrorState'
import { EmptyState } from '@/components/common/EmptyState'
import { knowledgeApi } from '@/api/knowledge'
import {
  KnowledgeExplanationResponse,
  KnowledgeDocument,
  KnowledgeCategory,
} from '@/types'

const SUGGESTED_QUERIES = [
  "Why is 'discuss about' incorrect?",
  "Why do we say 'look forward to meeting'?",
  "What is the difference between 'make' and 'do'?",
  "When should I use 'since' vs 'for'?",
  "How do I choose between 'affect' and 'effect'?",
  "When do I use 'fewer' instead of 'less'?",
]

const CATEGORY_TABS: { label: string; value: KnowledgeCategory }[] = [
  { label: 'All Topics', value: 'all' },
  { label: 'Grammar Rules', value: 'grammar' },
  { label: 'Common Mistakes', value: 'common_mistakes' },
  { label: 'Collocations', value: 'collocations' },
  { label: 'Learning Tips', value: 'learning_tips' },
]

export function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<KnowledgeCategory>('all')
  const [explanationResult, setExplanationResult] = useState<KnowledgeExplanationResponse | null>(null)
  const [activeDocument, setActiveDocument] = useState<KnowledgeDocument | null>(null)
  const [queryError, setQueryError] = useState<string | null>(null)

  // 1. Fetch Knowledge Documents for Browser
  const {
    data: documentsData,
    isLoading: isLoadingDocs,
    error: docsError,
    refetch: refetchDocs,
  } = useQuery({
    queryKey: ['knowledge-documents', selectedCategory],
    queryFn: () =>
      knowledgeApi.getDocuments({
        category: selectedCategory === 'all' ? undefined : selectedCategory,
      }),
  })

  // 2. Query Mutation
  const queryMutation = useMutation({
    mutationFn: (text: string) =>
      knowledgeApi.queryKnowledge({
        query: text,
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        top_k: 3,
      }),
    onSuccess: (data) => {
      setExplanationResult(data)
      setQueryError(null)
    },
    onError: (err: any) => {
      setQueryError(
        err?.response?.data?.detail || 'Failed to query the knowledge base. Please try again.'
      )
    },
  })

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!searchQuery.trim()) {
      setQueryError('Please enter a question or phrase to search.')
      return
    }
    setQueryError(null)
    queryMutation.mutate(searchQuery.trim())
  }

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion)
    setQueryError(null)
    queryMutation.mutate(suggestion)
  }

  const documents = documentsData?.items || []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 rounded-2xl p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 text-xs font-semibold backdrop-blur-sm border border-white/20">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
              <span>Grounded RAG Knowledge Engine</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Grammar & Usage Knowledge Base
            </h1>
            <p className="text-slate-300 text-sm sm:text-base max-w-2xl">
              Instant, verified English grammar rules, common mistake explanations, collocations,
              and cognitive learning strategies backed by curated linguistic knowledge.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20 flex items-center gap-4 min-w-[220px]">
            <div className="h-12 w-12 rounded-lg bg-indigo-500/30 flex items-center justify-center border border-white/20">
              <BookOpen className="h-6 w-6 text-indigo-300" />
            </div>
            <div>
              <p className="text-xs text-slate-300 uppercase font-bold tracking-wider">Curated Guides</p>
              <p className="text-xl font-bold">{documentsData?.total || 10} Articles</p>
              <p className="text-xs text-emerald-300">Verified & Grounded</p>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 1: Interactive Query & Search Box */}
      <Card className="border-indigo-100 shadow-sm">
        <CardContent className="p-6 space-y-4">
          <form onSubmit={handleSearchSubmit} className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask any grammar question, phrase dilemma, or collocation rule..."
                  className="pl-10 h-12 text-sm bg-white"
                />
              </div>
              <Button
                type="submit"
                disabled={queryMutation.isPending || !searchQuery.trim()}
                className="h-12 px-6 flex items-center gap-2"
              >
                {queryMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" /> Searching...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" /> Ask RAG Engine
                  </>
                )}
              </Button>
            </div>

            {queryError && (
              <p className="text-xs text-rose-600 font-medium">{queryError}</p>
            )}
          </form>

          {/* Quick Suggestion Chips */}
          <div className="space-y-1.5">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <HelpCircle className="h-3.5 w-3.5 text-indigo-500" />
              Common Questions:
            </p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUERIES.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs px-3 py-1.5 rounded-full bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 font-medium transition border border-slate-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SECTION 2: Grounded RAG Explanation Result */}
      {explanationResult && (
        <Card className="border-indigo-200 bg-gradient-to-b from-white to-slate-50/50 shadow-md animate-in fade-in duration-300">
          <CardHeader className="pb-4 border-b border-gray-100">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 bg-indigo-100 text-indigo-800 rounded-full">
                  Rule: {explanationResult.rule_applied}
                </span>
                <span className="text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-semibold flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3" /> Grounded ({Math.round(explanationResult.groundedness_confidence * 100)}%)
                </span>
              </div>
              <span className="text-xs text-gray-500 italic">
                Query: "{explanationResult.query}"
              </span>
            </div>
            <CardTitle className="text-lg font-bold text-gray-900 mt-3 leading-snug">
              {explanationResult.summary}
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-6 pt-6">
            {/* Detailed Explanation */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Detailed Analysis
              </h4>
              <p className="text-sm text-gray-800 leading-relaxed bg-white p-4 rounded-xl border border-gray-100">
                {explanationResult.detailed_explanation}
              </p>
            </div>

            {/* Side-by-side Correct vs Incorrect */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Correct Usage */}
              <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-4 space-y-2">
                <h5 className="text-xs font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Correct Usage & Examples
                </h5>
                <ul className="space-y-2 text-xs text-emerald-950">
                  {explanationResult.correct_usage.map((ex, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{ex}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Incorrect Usage */}
              <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-4 space-y-2">
                <h5 className="text-xs font-bold text-rose-900 uppercase tracking-wider flex items-center gap-1.5">
                  <XCircle className="h-4 w-4 text-rose-600" />
                  Common Mistakes to Avoid
                </h5>
                <ul className="space-y-2 text-xs text-rose-950">
                  {explanationResult.incorrect_usage.map((err, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-rose-500 font-bold">•</span>
                      <span>{err}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Learning Memory Tip */}
            {explanationResult.learning_tip && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                <div className="p-2 bg-amber-100 rounded-lg text-amber-800 shrink-0">
                  <Lightbulb className="h-5 w-5" />
                </div>
                <div>
                  <h5 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                    Memory Hook / Learning Tip
                  </h5>
                  <p className="text-sm font-medium text-amber-900 mt-0.5">
                    {explanationResult.learning_tip}
                  </p>
                </div>
              </div>
            )}

            {/* Traceable Knowledge Sources */}
            {explanationResult.sources.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-gray-100">
                <h5 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-indigo-600" />
                  Verified Sources Used by RAG Engine:
                </h5>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {explanationResult.sources.map((src) => (
                    <div
                      key={src.id}
                      className="bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 transition text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-indigo-700">{src.id}</span>
                        <span className="text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded font-medium">
                          {Math.round(src.relevance_score * 100)}% match
                        </span>
                      </div>
                      <p className="font-semibold text-gray-900 truncate">{src.title}</p>
                      <p className="text-gray-500 text-[11px] line-clamp-2">{src.summary}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* SECTION 3: Knowledge Base Catalog & Browser */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-indigo-600" />
              Browse Knowledge Guides
            </h2>
            <p className="text-sm text-gray-500">
              Curated articles covering grammar rules, collocations, common pitfalls, and study techniques
            </p>
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap gap-1 bg-gray-100 p-1 rounded-lg">
            {CATEGORY_TABS.map((tab) => {
              const isSelected = selectedCategory === tab.value
              return (
                <button
                  key={tab.value}
                  onClick={() => setSelectedCategory(tab.value)}
                  className={`text-xs px-3 py-1.5 rounded-md font-medium transition ${
                    isSelected
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        {isLoadingDocs ? (
          <div className="py-12 flex justify-center">
            <LoadingSpinner size="md" className="text-indigo-600" />
          </div>
        ) : docsError ? (
          <ErrorState
            title="Failed to Load Knowledge Guides"
            message="Could not retrieve the knowledge base articles. Please try again."
            onRetry={() => refetchDocs()}
          />
        ) : documents.length === 0 ? (
          <EmptyState
            title="No Guides in this Category"
            message="No articles matched the selected filter."
            action={
              <Button onClick={() => setSelectedCategory('all')} size="sm">
                View All Guides
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <Card
                key={doc.id}
                className="hover:shadow-md transition border-gray-200 cursor-pointer flex flex-col justify-between"
                onClick={() => setActiveDocument(doc)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                      {doc.category.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gray-400 font-mono">{doc.id}</span>
                  </div>
                  <CardTitle className="text-base font-bold text-gray-900 mt-2 line-clamp-2">
                    {doc.title}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 flex-1 flex flex-col justify-between">
                  <p className="text-xs text-gray-600 line-clamp-3 leading-relaxed">
                    {doc.summary}
                  </p>
                  <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-xs text-indigo-600 font-medium">
                    <span>{doc.rules.length} core rules</span>
                    <span className="flex items-center gap-0.5 hover:underline">
                      Read Guide <ChevronRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Full Document Detail Modal */}
      {activeDocument && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-200 p-6 sm:p-8 space-y-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800">
                    {activeDocument.category.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">{activeDocument.id}</span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mt-2">
                  {activeDocument.title}
                </h3>
              </div>
              <button
                onClick={() => setActiveDocument(null)}
                className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-sm text-gray-800">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Summary
                </h4>
                <p className="leading-relaxed">{activeDocument.summary}</p>
              </div>

              {activeDocument.rules.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                    Core Rules
                  </h4>
                  <ul className="space-y-1.5 list-disc pl-5 text-xs text-gray-900">
                    {activeDocument.rules.map((rule, i) => (
                      <li key={i}>{rule}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-2">
                <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Full Guide & Content
                </h4>
                <div className="whitespace-pre-line text-xs text-gray-700 bg-white p-4 rounded-xl border border-gray-100 leading-relaxed">
                  {activeDocument.content}
                </div>
              </div>

              {/* Examples & Common Mistakes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {activeDocument.correct_examples.length > 0 && (
                  <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-3.5 space-y-1.5">
                    <h5 className="text-xs font-bold text-emerald-900 uppercase">Correct Examples</h5>
                    <ul className="space-y-1 text-xs text-emerald-950">
                      {activeDocument.correct_examples.map((ex, i) => (
                        <li key={i}>• {ex}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {activeDocument.common_mistakes.length > 0 && (
                  <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-3.5 space-y-1.5">
                    <h5 className="text-xs font-bold text-rose-900 uppercase">Common Mistakes</h5>
                    <ul className="space-y-1 text-xs text-rose-950">
                      {activeDocument.common_mistakes.map((m, i) => (
                        <li key={i}>• {m}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <p className="text-[11px] text-gray-400 italic">
                Source: {activeDocument.source}
              </p>
            </div>

            <div className="pt-4 border-t border-gray-100 flex justify-end">
              <Button onClick={() => setActiveDocument(null)} variant="outline">
                Close Guide
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KnowledgePage
