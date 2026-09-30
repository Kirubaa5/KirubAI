import { Link, useLocation } from 'react-router-dom'
import { BookOpen, LogOut, Flame, Sparkles } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { NAV_SECTIONS, NavItemConfig } from './navConfig'

interface SidebarProps {
  onNavigate?: () => void
  className?: string
}

export function Sidebar({ onNavigate, className = '' }: SidebarProps) {
  const location = useLocation()
  const { isAuthenticated, user, logout } = useAuthStore()

  const isRouteActive = (item: NavItemConfig): boolean => {
    if (item.exact || item.path === '/') {
      return location.pathname === item.path
    }
    return location.pathname === item.path || location.pathname.startsWith(`${item.path}/`)
  }

  const getInitials = (name?: string): string => {
    if (!name) return 'U'
    const parts = name.trim().split(' ')
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
    }
    return name.substring(0, 2).toUpperCase()
  }

  return (
    <aside
      className={`flex flex-col h-full bg-white border-r border-gray-200 select-none ${className}`}
      aria-label="Application Sidebar"
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-5 border-b border-gray-100 shrink-0">
        <Link
          to="/"
          onClick={onNavigate}
          className="flex items-center gap-2.5 group focus:outline-hidden focus:ring-2 focus:ring-blue-500 rounded-lg p-1 -ml-1 transition-colors"
        >
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-xs group-hover:shadow-md transition-shadow">
            <BookOpen className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg text-gray-900 tracking-tight leading-tight">
                KirubAI
              </span>
              <span className="inline-flex items-center px-1.5 py-0.2 text-[10px] font-semibold bg-blue-50 text-blue-700 rounded-md border border-blue-200">
                PRO
              </span>
            </div>
            <span className="text-[11px] text-gray-500 font-medium leading-none mt-0.5">
              Vocabulary Mastery
            </span>
          </div>
        </Link>
      </div>

      {/* Navigation Sections */}
      <nav
        className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-200"
        aria-label="Main Navigation"
      >
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const active = isRouteActive(item)
                const Icon = item.icon
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={onNavigate}
                    aria-current={active ? 'page' : undefined}
                    className={`group flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 focus:outline-hidden focus:ring-2 focus:ring-blue-500 ${
                      active
                        ? 'bg-blue-50/90 text-blue-700 font-semibold shadow-xs'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/70'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          active
                            ? 'text-blue-600'
                            : 'text-gray-400 group-hover:text-gray-600'
                        }`}
                        aria-hidden="true"
                      />
                      <span className="truncate">{item.title}</span>
                    </div>

                    {item.badge && (
                      <span className="ml-2 inline-flex items-center px-1.5 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User Footer / Auth Area */}
      <div className="p-3 border-t border-gray-100 bg-gray-50/50 shrink-0">
        {isAuthenticated && user ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 rounded-lg bg-white border border-gray-200/80 shadow-xs">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-xs">
                  {getInitials(user.full_name || user.email)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-gray-900 truncate leading-tight">
                    {user.full_name || 'Learner'}
                  </p>
                  <p className="text-[11px] text-gray-500 truncate leading-tight">
                    {user.email}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  logout()
                  if (onNavigate) onNavigate()
                }}
                className="p-1.5 h-8 w-8 text-gray-400 hover:text-red-600 hover:bg-red-50 shrink-0"
                aria-label="Log out of account"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>

            {/* Quick user metrics pill */}
            <div className="flex items-center justify-between px-2 py-1 text-[11px] font-medium text-gray-500">
              <span className="capitalize flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-500" />
                {user.english_level || 'Intermediate'}
              </span>
              {typeof user.current_streak === 'number' && user.current_streak > 0 && (
                <span className="flex items-center gap-1 text-amber-600 font-semibold">
                  <Flame className="w-3 h-3 text-amber-500" />
                  {user.current_streak}d streak
                </span>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <Link to="/login" onClick={onNavigate} className="w-full">
              <Button variant="outline" size="sm" className="w-full justify-center text-xs font-semibold">
                Login
              </Button>
            </Link>
            <Link to="/register" onClick={onNavigate} className="w-full">
              <Button size="sm" className="w-full justify-center text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white">
                Sign Up
              </Button>
            </Link>
          </div>
        )}
      </div>
    </aside>
  )
}
