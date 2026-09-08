import { LoadingSpinner } from '@/components/common/LoadingSpinner'

export function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
        <p className="text-center text-gray-600">Dashboard coming in Phase 9</p>
      </div>
    </div>
  )
}
