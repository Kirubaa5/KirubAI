import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from '../AppLayout'
import { useAuthStore } from '@/stores/authStore'

describe('AppLayout & Responsive Navigation Shell', () => {
  beforeEach(() => {
    // Reset auth store before each test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  it('renders KirubAI branding, navigation sections, and all 12 destinations on desktop', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Page Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    // Check branding
    expect(screen.getAllByText('KirubAI').length).toBeGreaterThan(0)
    expect(screen.getByText('Vocabulary Mastery')).toBeInTheDocument()

    // Check 4 navigation section titles
    expect(screen.getByText('Primary')).toBeInTheDocument()
    expect(screen.getByText('Learn & Practice')).toBeInTheDocument()
    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.getByText('Tools')).toBeInTheDocument()

    // Check all 12 navigation destinations
    expect(screen.getAllByText('Home').length).toBeGreaterThan(0)
    expect(screen.getByText('Daily Plan')).toBeInTheDocument()
    expect(screen.getByText('Use My Vocab')).toBeInTheDocument()
    expect(screen.getByText('Vocabulary')).toBeInTheDocument()
    expect(screen.getByText('Reviews')).toBeInTheDocument()
    expect(screen.getByText('Conversations')).toBeInTheDocument()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Adaptive Plan')).toBeInTheDocument()
    expect(screen.getByText('Personalization')).toBeInTheDocument()
    expect(screen.getByText('Achievements')).toBeInTheDocument()
    expect(screen.getByText('Knowledge Base')).toBeInTheDocument()
    expect(screen.getByText('Export Decks')).toBeInTheDocument()

    // Check children content
    expect(screen.getByText('Page Content')).toBeInTheDocument()
  })

  it('highlights the active route based on the current path', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AppLayout>
          <div>Dashboard Page Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    expect(dashboardLink).toHaveAttribute('aria-current', 'page')
    expect(dashboardLink.className).toContain('bg-blue-50')
  })

  it('renders unauthenticated state with Login and Sign Up buttons', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Public Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    expect(screen.getAllByRole('link', { name: /login/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('link', { name: /sign up/i }).length).toBeGreaterThan(0)
  })

  it('displays user profile, metrics, and triggers logout when authenticated', () => {
    useAuthStore.setState({
      user: {
        id: '123',
        email: 'learner@example.com',
        full_name: 'Kiruba Dev',
        english_level: 'advanced',
        current_streak: 5,
        xp: 120,
      },
      token: 'jwt-token-123',
      isAuthenticated: true,
    })

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AppLayout>
          <div>Protected Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    expect(screen.getAllByText('Kiruba Dev').length).toBeGreaterThan(0)
    expect(screen.getByText('learner@example.com')).toBeInTheDocument()
    expect(screen.getAllByText(/5d streak/i).length).toBeGreaterThan(0)

    const logoutBtn = screen.getByRole('button', { name: /log out of account/i })
    expect(logoutBtn).toBeInTheDocument()

    fireEvent.click(logoutBtn)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('opens and closes mobile drawer via hamburger and close button', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Responsive Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    // Mobile menu starts closed
    expect(screen.queryByRole('dialog', { name: /navigation menu/i })).not.toBeInTheDocument()

    // Open mobile menu
    const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
    fireEvent.click(menuButton)

    // Drawer is now open
    const drawer = screen.getByRole('dialog', { name: /navigation menu/i })
    expect(drawer).toBeInTheDocument()

    // Close drawer via close button
    const closeButton = screen.getByRole('button', { name: /close navigation menu/i })
    fireEvent.click(closeButton)

    expect(screen.queryByRole('dialog', { name: /navigation menu/i })).not.toBeInTheDocument()
  })

  it('closes mobile drawer when Escape key is pressed', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Escape Test Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
    fireEvent.click(menuButton)
    expect(screen.getByRole('dialog', { name: /navigation menu/i })).toBeInTheDocument()

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('dialog', { name: /navigation menu/i })).not.toBeInTheDocument()
  })

  it('closes mobile drawer when clicking a navigation link inside the drawer', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Link Click Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
    fireEvent.click(menuButton)
    expect(screen.getByRole('dialog', { name: /navigation menu/i })).toBeInTheDocument()

    // Click link inside drawer
    const drawerLinks = screen.getAllByRole('link', { name: /vocabulary/i })
    fireEvent.click(drawerLinks[drawerLinks.length - 1])

    expect(screen.queryByRole('dialog', { name: /navigation menu/i })).not.toBeInTheDocument()
  })
})
