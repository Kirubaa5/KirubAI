import { Link, useLocation } from 'react-router-dom'
import { Menu, Flame, Sparkles, BookOpen } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { ROUTE_TITLE_MAP } from './navConfig'

interface HeaderProps {
  onOpenMobileMenu: () => void
}

export function Header({ onOpenMobileMenu }: HeaderProps) {
  const location = useLocation()
  const { isAuthenticated, user } = useAuthStore()

  // Resolve current route title and section category
  const currentRouteMeta = ROUTE_TITLE_MAP[location.pathname] || {
    title: location.pathname.startsWith('/vocabulary/')
      ? 'Word Details'
      : location.pathname.startsWith('/practice/')
      ? 'Practice Session'
      : location.pathname.startsWith('/conversations/')
      ? 'AI Conversation'
      : 'KirubAI',
  }

  const getInitials = (name?: string, email?: string): string => {
    const target = name?.trim() || email?.split('@')[0] || 'U'
    const parts = target.split(' ').filter(Boolean)
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
    }
    return target.substring(0, 2).toUpperCase()
  }

  const displayName = user?.full_name || (user?.email ? user.email.split('@')[0] : 'Learner')

  return (
    <header className="sticky top-0 z-20 h-16 bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 flex items-center justify-between transition-colors">
      {/* Left: Mobile Menu Trigger & Page Title */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        <button
          type="button"
          onClick={onOpenMobileMenu}
          className="lg:hidden p-2 -ml-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Mobile brand (shown only on <1024px screens) */}
        <Link
          to="/"
          className="flex lg:hidden items-center gap-2 font-bold text-gray-900 shrink-0"
        >
          <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center text-white">
            <BookOpen className="w-4 h-4" />
          </div>
          <span className="text-base tracking-tight font-bold">KirubAI</span>
        </Link>

        {/* Breadcrumb / Title for desktop */}
        <div className="hidden lg:flex items-center gap-2 min-w-0">
          {currentRouteMeta.category && (
            <>
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                {currentRouteMeta.category}
              </span>
              <span className="text-gray-300">/</span>
            </>
          )}
          <h1 className="text-base sm:text-lg font-bold text-gray-900 truncate tracking-tight">
            {currentRouteMeta.title}
          </h1>
        </div>
      </div>

      {/* Right: Contextual Status & Actions */}
      <div className="flex items-center gap-2 sm:gap-3">
        {isAuthenticated && user ? (
          <>
            {/* Streak Indicator */}
            {typeof user.current_streak === 'number' && user.current_streak > 0 && (
              <div
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold"
                title={`${user.current_streak} day active streak`}
              >
                <Flame className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                <span>{user.current_streak}d Streak</span>
              </div>
            )}

            {/* Level Pill */}
            {user.english_level && (
              <div className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-medium capitalize">
                <Sparkles className="w-3 h-3 text-blue-600" />
                <span>{user.english_level}</span>
              </div>
            )}

            {/* User Profile Avatar */}
            <div className="flex items-center gap-2 pl-1 sm:pl-2 border-l border-gray-200">
              <div
                className="w-8 h-8 rounded-full bg-blue-600 text-white font-semibold text-xs flex items-center justify-center shrink-0"
                title={user.email || displayName}
              >
                {getInitials(user.full_name, user.email)}
              </div>
              <span className="hidden md:inline-block text-xs font-semibold text-gray-800 max-w-[120px] truncate">
                {displayName}
              </span>
            </div>
          </>
        ) : (
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="text-xs font-semibold text-gray-700 hover:text-gray-900 px-2.5 py-1.5 rounded-md hover:bg-gray-100"
            >
              Login
            </Link>
            <Link
              to="/register"
              className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md transition-colors"
            >
              Sign Up
            </Link>
          </div>
        )}
      </div>
    </header>
  )
}
