import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { VocabularyPage } from '@/pages/VocabularyPage'
import { LearnPage } from '@/pages/LearnPage'
import { PracticePage } from '@/pages/PracticePage'
import { ReviewsPage } from '@/pages/ReviewsPage'
import { ConversationsPage } from '@/pages/ConversationsPage'
import { PersonalizationPage } from '@/pages/PersonalizationPage'
import { KnowledgePage } from '@/pages/KnowledgePage'
import { DashboardPage } from '@/pages/DashboardPage'
import { AchievementsPage } from '@/pages/AchievementsPage'
import { DailyPlanPage } from '@/pages/DailyPlanPage'
import { MultiWordPracticePage } from '@/pages/MultiWordPracticePage'
import { ExportPage } from '@/pages/ExportPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { Button } from '@/components/ui/Button'
import { BookOpen, Home, LayoutDashboard, LogOut, Library, Brain, MessageSquare, Sparkles, Compass, Trophy, Calendar, Layers, Download } from 'lucide-react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function Navigation() {
  const { isAuthenticated, logout, user } = useAuthStore()

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link to="/" className="flex items-center gap-2 font-bold text-xl text-blue-600">
              <BookOpen className="h-6 w-6" />
              KirubAI
            </Link>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                to="/"
                className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
              >
                <Home className="h-4 w-4 mr-1" />
                Home
              </Link>
              {isAuthenticated && (
                <>
                  <Link
                    to="/daily"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-blue-700 font-bold border-b-2 border-blue-600"
                  >
                    <Calendar className="h-4 w-4 mr-1 text-blue-600" />
                    Daily Plan
                  </Link>
                  <Link
                    to="/practice/multi-word"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-purple-700 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Layers className="h-4 w-4 mr-1 text-purple-600" />
                    Use My Vocab
                  </Link>
                  <Link
                    to="/vocabulary"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Library className="h-4 w-4 mr-1" />
                    Vocabulary
                  </Link>
                  <Link
                    to="/reviews"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Brain className="h-4 w-4 mr-1 text-purple-600" />
                    Reviews
                  </Link>
                  <Link
                    to="/conversations"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <MessageSquare className="h-4 w-4 mr-1 text-indigo-600" />
                    Conversations
                  </Link>
                  <Link
                    to="/personalization"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Sparkles className="h-4 w-4 mr-1 text-amber-500" />
                    Personalized Plan
                  </Link>
                  <Link
                    to="/knowledge"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Compass className="h-4 w-4 mr-1 text-teal-600" />
                    Knowledge Base
                  </Link>
                  <Link
                    to="/dashboard"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <LayoutDashboard className="h-4 w-4 mr-1" />
                    Dashboard
                  </Link>
                  <Link
                    to="/achievements"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Trophy className="h-4 w-4 mr-1 text-amber-500" />
                    Achievements
                  </Link>
                  <Link
                    to="/export"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 border-b-2 border-transparent hover:border-gray-300"
                  >
                    <Download className="h-4 w-4 mr-1 text-blue-600" />
                    Export
                  </Link>
                </>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700 hidden sm:inline">
                  {user?.full_name}
                </span>
                <Button variant="ghost" size="sm" onClick={logout} className="flex items-center gap-1">
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Login
                  </Button>
                </Link>
                <Link to="/register">
                  <Button size="sm">Sign up</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navigation />
      <main className="flex-1">{children}</main>
    </div>
  )
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/daily"
              element={
                <ProtectedRoute>
                  <DailyPlanPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/practice/multi-word"
              element={
                <ProtectedRoute>
                  <MultiWordPracticePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vocabulary"
              element={
                <ProtectedRoute>
                  <VocabularyPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/vocabulary/:id/learn"
              element={
                <ProtectedRoute>
                  <LearnPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/practice/:id"
              element={
                <ProtectedRoute>
                  <PracticePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/practice"
              element={
                <ProtectedRoute>
                  <VocabularyPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reviews"
              element={
                <ProtectedRoute>
                  <ReviewsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/conversations"
              element={
                <ProtectedRoute>
                  <ConversationsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/conversations/:id"
              element={
                <ProtectedRoute>
                  <ConversationsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/personalization"
              element={
                <ProtectedRoute>
                  <PersonalizationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/knowledge"
              element={
                <ProtectedRoute>
                  <KnowledgePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/achievements"
              element={
                <ProtectedRoute>
                  <AchievementsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/export"
              element={
                <ProtectedRoute>
                  <ExportPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
