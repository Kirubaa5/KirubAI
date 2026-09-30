import React, { useState } from 'react'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { MobileDrawer } from './MobileDrawer'

interface AppLayoutProps {
  children: React.ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col text-gray-900 antialiased">
      {/* 1. Desktop Fixed Sidebar */}
      <div className="hidden lg:flex lg:w-[260px] lg:flex-col lg:fixed lg:inset-y-0 z-30">
        <Sidebar />
      </div>

      {/* 2. Mobile Slide-over Drawer */}
      <MobileDrawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />

      {/* 3. Main Content Wrapper */}
      <div className="lg:pl-[260px] flex flex-col flex-1 min-w-0">
        <Header onOpenMobileMenu={() => setIsMobileMenuOpen(true)} />

        <main className="flex-1 w-full max-w-full overflow-x-hidden focus:outline-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
