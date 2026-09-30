import { Link } from 'react-router-dom'
import { NavItemConfig } from './navConfig'

interface NavItemProps {
  item: NavItemConfig
  isActive: boolean
  onClick?: () => void
  className?: string
}

export function NavItem({ item, isActive, onClick, className = '' }: NavItemProps) {
  const Icon = item.icon

  return (
    <Link
      to={item.path}
      onClick={onClick}
      aria-current={isActive ? 'page' : undefined}
      className={`group flex items-center justify-between px-3 py-2 rounded-md text-sm font-medium transition-colors focus:outline-hidden focus-visible:ring-2 focus-visible:ring-blue-500 ${
        isActive
          ? 'bg-blue-50 text-blue-700 font-semibold border-r-2 border-blue-600'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
      } ${className}`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <Icon
          className={`w-4 h-4 shrink-0 transition-colors ${
            isActive ? 'text-blue-600' : 'text-gray-400 group-hover:text-gray-600'
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
}
