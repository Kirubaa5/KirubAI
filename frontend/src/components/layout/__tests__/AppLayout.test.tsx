import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AppLayout } from '../AppLayout'
import { useAuthStore } from '@/stores/authStore'

describe('AppLayout & Navigation Redesign', () => {
  beforeEach(() => {
    // Reset auth store before each test
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  })

  it('renders KirubAI branding and navigation sections on desktop', () => {
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

    // Check navigation section categories
    expect(screen.getByText('Primary')).toBeInTheDocument()
    expect(screen.getByText('Learn & Practice')).toBeInTheDocument()
    expect(screen.getByText('Insights')).toBeInTheDocument()
    expect(screen.getByText('Tools')).toBeInTheDocument()

    // Check critical navigation links
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

    // Check main page content
    expect(screen.getByText('Page Content')).toBeInTheDocument()
  })

  it('highlights the active route based on current path', () => {
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

  it('displays user profile and logout button when authenticated', () => {
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

    const logoutBtn = screen.getByRole('button', { name: /log out/i })
    expect(logoutBtn).toBeInTheDocument()

    fireEvent.click(logoutBtn)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('opens and closes the mobile navigation drawer via hamburger button and close button', () => {
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

    // Drawer should now be visible
    const drawer = screen.getByRole('dialog', { name: /navigation menu/i })
    expect(drawer).toBeInTheDocument()

    // Close drawer via close button
    const closeButton = screen.getByRole('button', { name: /close navigation menu/i })
    fireEvent.click(closeButton)

    expect(screen.queryByRole('dialog', { name: /navigation menu/i })).not.toBeInTheDocument()
  })

  it('closes the mobile navigation drawer when Escape key is pressed', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppLayout>
          <div>Test Content</div>
        </AppLayout>
      </MemoryRouter>
    )

    // Open mobile menu
    const menuButton = screen.getByRole('button', { name: /open navigation menu/i })
    fireEvent.click(menuButton)
    expect(screen.getByRole('dialog', { name: /navigation menu/i })).toBeInTheDocument()

    // Press Escape
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByRole('dialog', { name: /navigation menu/i })).not.toBeInTheDocument()
  })
})
