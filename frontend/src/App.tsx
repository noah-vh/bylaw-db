import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Import original components
import { Header } from './components/common/Header'
import { ResourcePortal } from './pages/ResourcePortal'
import { AdminDashboard } from './pages/AdminDashboard'
import { BylawHistory } from './pages/BylawHistory'
import { SourceViewer } from './pages/SourceViewer'
import { ComplianceChecker } from './pages/ComplianceChecker'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

// Mock auth context
interface User {
  id: string
  email: string
  role: string
}

// Mock Authentication Service
const MockAuthService = {
  signIn: async (email: string, password: string): Promise<User> => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // Simple mock validation
    if (email === 'admin@example.com' && password === 'admin123') {
      return {
        id: 'mock-admin-id',
        email: 'admin@example.com',
        role: 'admin'
      }
    }
    
    throw new Error('Invalid credentials')
  },
  
  signOut: async (): Promise<void> => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 300))
  },
  
  getCurrentUser: (): User | null => {
    // Check if user is stored in localStorage for persistence
    const stored = localStorage.getItem('mock-user')
    return stored ? JSON.parse(stored) : null
  },
  
  setUser: (user: User | null) => {
    if (user) {
      localStorage.setItem('mock-user', JSON.stringify(user))
    } else {
      localStorage.removeItem('mock-user')
    }
  }
}

// Login Component
const LoginForm: React.FC<{ onLogin: (user: User) => void }> = ({ onLogin }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const user = await MockAuthService.signIn(email, password)
      MockAuthService.setUser(user)
      onLogin(user)
    } catch (error: any) {
      setError(error.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-primary-600 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Admin Login</h2>
          <p className="text-gray-600 mt-2">Access the Bylaw Database Admin Dashboard</p>
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              placeholder="admin@example.com"
              required
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
              placeholder="Enter your password"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-2">Demo Credentials:</p>
          <div className="text-xs text-gray-500">
            <p>Email: admin@example.com</p>
            <p>Password: admin123</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const existingUser = MockAuthService.getCurrentUser()
    if (existingUser) {
      setUser(existingUser)
    }
    setLoading(false)
  }, [])

  const handleLogin = (user: User) => {
    setUser(user)
  }

  const handleSignOut = async () => {
    try {
      await MockAuthService.signOut()
      MockAuthService.setUser(null)
      setUser(null)
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Bylaw Database...</p>
        </div>
      </div>
    )
  }

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header user={user} onSignOut={handleSignOut} />
          
          <main>
            <Routes>
              <Route path="/" element={<ResourcePortal />} />
              <Route path="/compliance" element={<ComplianceChecker />} />
              <Route 
                path="/admin" 
                element={
                  user ? (
                    <AdminDashboard user={user} />
                  ) : (
                    <LoginForm onLogin={handleLogin} />
                  )
                } 
              />
              <Route path="/bylaw/:id/history" element={<BylawHistory />} />
              <Route path="/bylaw/:id/source" element={<SourceViewer />} />
            </Routes>
          </main>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App