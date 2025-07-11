import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Search, User, LogOut } from 'lucide-react'

interface HeaderProps {
  user?: any
  onSignOut?: () => void
}

export const Header: React.FC<HeaderProps> = ({ user: propUser, onSignOut }) => {
  const location = useLocation()
  const [user, setUser] = useState<any>(null)

  // Mock authentication - simulates a logged in admin user
  useEffect(() => {
    // Use prop user if provided, otherwise use mock user
    if (propUser) {
      setUser(propUser)
    } else {
      // Mock user for demonstration
      setUser({
        id: 'mock-admin-user',
        email: 'admin@bylawdb.com',
        role: 'admin'
      })
    }
  }, [propUser])

  const handleSignOut = async () => {
    try {
      if (onSignOut) {
        onSignOut()
      } else {
        // Mock sign out - just clear the user
        setUser(null)
        console.log('User signed out')
      }
    } catch (error) {
      console.error('Sign out error:', error)
    }
  }

  const handleSignIn = async () => {
    try {
      // Mock sign in - set a mock user
      setUser({
        id: 'mock-admin-user',
        email: 'admin@bylawdb.com',
        role: 'admin'
      })
      console.log('User signed in')
    } catch (error) {
      console.error('Sign in error:', error)
    }
  }

  const isActive = (path: string) => location.pathname === path

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and Navigation */}
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Search className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">Bylaw DB</span>
            </Link>

            <nav className="hidden md:flex items-center space-x-6">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/') 
                    ? 'text-primary-600 bg-primary-50' 
                    : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                }`}
              >
                Search Bylaws
              </Link>
              
              <Link
                to="/compliance"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive('/compliance') 
                    ? 'text-primary-600 bg-primary-50' 
                    : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                }`}
              >
                Compliance Checker
              </Link>
              
              {user && (
                <Link
                  to="/admin"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive('/admin') 
                      ? 'text-primary-600 bg-primary-50' 
                      : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                  }`}
                >
                  Admin Dashboard
                </Link>
              )}
            </nav>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                  <span className="hidden sm:block text-sm font-medium text-gray-700">
                    {user.email}
                  </span>
                </div>
                <button
                  onClick={handleSignOut}
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:block">Sign Out</span>
                </button>
              </div>
            ) : (
              <button
                onClick={handleSignIn}
                className="flex items-center space-x-1 px-4 py-2 rounded-md text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 transition-colors"
              >
                <User className="w-4 h-4" />
                <span>Admin Login</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}