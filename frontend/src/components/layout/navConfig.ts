import {
  Home,
  Calendar,
  Layers,
  Library,
  Brain,
  MessageSquare,
  LayoutDashboard,
  Sparkles,
  Target,
  Trophy,
  Compass,
  Download,
  LucideIcon,
} from 'lucide-react'

export interface NavItemConfig {
  title: string
  path: string
  icon: LucideIcon
  badge?: string
  exact?: boolean
  description?: string
}

export interface NavSectionConfig {
  title: string
  items: NavItemConfig[]
}

export const NAV_SECTIONS: NavSectionConfig[] = [
  {
    title: 'Primary',
    items: [
      {
        title: 'Home',
        path: '/',
        icon: Home,
        exact: true,
        description: 'Overview & quick start',
      },
      {
        title: 'Daily Plan',
        path: '/daily',
        icon: Calendar,
        description: 'Today’s structured routine',
      },
      {
        title: 'Use My Vocab',
        path: '/practice/multi-word',
        icon: Layers,
        description: 'Multi-word scenario practice',
      },
    ],
  },
  {
    title: 'Learn & Practice',
    items: [
      {
        title: 'Vocabulary',
        path: '/vocabulary',
        icon: Library,
        description: 'Word collection & learning',
      },
      {
        title: 'Reviews',
        path: '/reviews',
        icon: Brain,
        description: 'Spaced repetition recall',
      },
      {
        title: 'Conversations',
        path: '/conversations',
        icon: MessageSquare,
        description: 'AI scenario dialogues',
      },
    ],
  },
  {
    title: 'Insights',
    items: [
      {
        title: 'Dashboard',
        path: '/dashboard',
        icon: LayoutDashboard,
        description: 'Progress & learning analytics',
      },
      {
        title: 'Adaptive Plan',
        path: '/adaptive',
        icon: Sparkles,
        description: 'Dynamic recommendations',
      },
      {
        title: 'Personalization',
        path: '/personalization',
        icon: Target,
        description: 'Custom learning goals',
      },
      {
        title: 'Achievements',
        path: '/achievements',
        icon: Trophy,
        description: 'Badges, streaks & milestones',
      },
    ],
  },
  {
    title: 'Tools',
    items: [
      {
        title: 'Knowledge Base',
        path: '/knowledge',
        icon: Compass,
        description: 'Grammar & collocation rules',
      },
      {
        title: 'Export Decks',
        path: '/export',
        icon: Download,
        description: 'Anki, CSV, PDF & JSON exports',
      },
    ],
  },
]

export const ROUTE_TITLE_MAP: Record<string, { title: string; category?: string }> = {
  '/': { title: 'Home' },
  '/daily': { title: 'Daily Learning Plan', category: 'Primary' },
  '/practice/multi-word': { title: 'Use My Vocabulary', category: 'Primary' },
  '/vocabulary': { title: 'Vocabulary List', category: 'Learn & Practice' },
  '/reviews': { title: 'Spaced Reviews', category: 'Learn & Practice' },
  '/conversations': { title: 'Conversations', category: 'Learn & Practice' },
  '/dashboard': { title: 'Dashboard', category: 'Insights' },
  '/adaptive': { title: 'Adaptive Learning Plan', category: 'Insights' },
  '/personalization': { title: 'Personalization', category: 'Insights' },
  '/achievements': { title: 'Achievements & Milestones', category: 'Insights' },
  '/knowledge': { title: 'Knowledge Base', category: 'Tools' },
  '/export': { title: 'Export Study Decks', category: 'Tools' },
  '/login': { title: 'Login' },
  '/register': { title: 'Sign Up' },
}
