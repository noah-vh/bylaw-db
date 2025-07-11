import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  },
})

// Helper function to handle API errors
export const handleApiError = (error: any) => {
  console.error('API Error:', error)
  
  if (error.code === 'PGRST301') {
    throw new Error('No data found')
  }
  
  if (error.code === 'PGRST116') {
    throw new Error('Invalid query parameters')
  }
  
  if (error.message) {
    throw new Error(error.message)
  }
  
  throw new Error('An unexpected error occurred')
}