import { Link, useLocation } from 'react-router-dom'
import { BookOpen, LogOut, Flame, Sparkles } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/Button'
import { NAV_SECTIONS, NavItemConfig } from './navConfig'
import { NavItem } from './NavItem'

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
    <aside
      className={`flex flex-col h-full bg-white border-r border-gray-200 select-none w-[260px] ${className}`}
      aria-label="Application Sidebar"
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-gray-100 shrink-0">
        <Link
          to="/"
          onClick={onNavigate}
          className="flex items-center gap-2.5 group focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500 rounded-md p-1 -ml-1"
        >
          <div className="w-8 h-8 rounded-md bg-blue-600 flex items-center justify-center text-white shrink-0">
            <BookOpen className="w-4 h-4" />
          </div>
          <div className="flex flex-col min-w-0">
            <span className="font-bold text-base text-gray-900 tracking-tight leading-tight">
              KirubAI
            </span>
            <span className="text-[11px] text-gray-500 font-medium leading-none mt-0.5 truncate">
              Vocabulary Mastery
            </span>
          </div>
        </Link>
      </div>

      {/* Navigation Sections */}
      <nav
        className="flex-1 overflow-y-auto px-3 py-4 space-y-5"
        aria-label="Main Navigation"
      >
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-3 text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-1">
              {section.title}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavItem
                  key={item.path}
                  item={item}
                  isActive={isRouteActive(item)}
                  onClick={onNavigate}
                />
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* User Footer / Auth Area */}
      <div className="p-3 border-t border-gray-200 bg-gray-50/70 shrink-0">
        {isAuthenticated && user ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 rounded-md bg-white border border-gray-200">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-semibold text-xs flex items-center justify-center shrink-0">
                  {getInitials(user.full_name, user.email)}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-gray-900 truncate leading-tight">
                    {displayName}
                  </p>
                  {user.email && (
                    <p className="text-[11px] text-gray-500 truncate leading-tight">
                      {user.email}
                    </p>
                  )}
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

            {/* User metrics pill */}
            <div className="flex items-center justify-between px-2 py-0.5 text-[11px] font-medium text-gray-500">
              <span className="capitalize flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-500" />
                {user.english_level || 'Intermediate'}
              </span>
              {typeof user.current_streak === 'number' && user.current_streak > 0 && (
                <span className="flex items-center gap-1 text-amber-600 font-semibold">
                  <Flame className="w-3 h-3 text-amber-500 fill-amber-500" />
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
