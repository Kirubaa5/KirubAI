import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { useAuthStore } from '@/stores/authStore'

export function HomePage() {
  const { isAuthenticated } = useAuthStore()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Turn the words you know into words you use
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          KirubAI is an AI-powered English vocabulary learning platform that transforms passive
          vocabulary into active, usable language skills.
        </p>
        <div className="flex gap-4 justify-center">
          {isAuthenticated ? (
            <Link to="/dashboard">
              <Button size="lg">Go to Dashboard</Button>
            </Link>
          ) : (
            <>
              <Link to="/register">
                <Button size="lg">Get Started</Button>
              </Link>
              <Link to="/login">
                <Button size="lg" variant="outline">
                  Login
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
