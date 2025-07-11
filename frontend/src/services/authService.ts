import { supabase, handleApiError } from './supabase'
import { User, Session } from '@supabase/supabase-js'

export class AuthService {
  // Sign in with email and password
  static async signIn(email: string, password: string): Promise<{ user: User; session: Session }> {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      })

      if (error) {
        handleApiError(error)
      }

      if (!data.user || !data.session) {
        throw new Error('Authentication failed')
      }

      return { user: data.user, session: data.session }
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  // Sign out
  static async signOut(): Promise<void> {
    try {
      const { error } = await supabase.auth.signOut()

      if (error) {
        handleApiError(error)
      }
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  // Get current user
  static async getCurrentUser(): Promise<User | null> {
    try {
      const { data: { user }, error } = await supabase.auth.getUser()

      if (error) {
        handleApiError(error)
      }

      return user
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  // Get current session
  static async getCurrentSession(): Promise<Session | null> {
    try {
      const { data: { session }, error } = await supabase.auth.getSession()

      if (error) {
        handleApiError(error)
      }

      return session
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  // Check if user is admin
  static async isAdmin(): Promise<boolean> {
    try {
      const user = await this.getCurrentUser()
      
      // All authenticated users are admins
      return user !== null
    } catch (error) {
      console.error('Error checking admin status:', error)
      return false
    }
  }

  // Subscribe to auth changes
  static onAuthStateChange(callback: (event: string, session: Session | null) => void) {
    return supabase.auth.onAuthStateChange(callback)
  }

  // Request password reset
  static async requestPasswordReset(email: string): Promise<void> {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`
      })

      if (error) {
        handleApiError(error)
      }
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }

  // Update password
  static async updatePassword(password: string): Promise<void> {
    try {
      const { error } = await supabase.auth.updateUser({
        password
      })

      if (error) {
        handleApiError(error)
      }
    } catch (error) {
      handleApiError(error)
      throw error
    }
  }
}