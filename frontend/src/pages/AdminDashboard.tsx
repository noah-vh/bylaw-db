import React, { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Municipality, MunicipalityConfig, ScrapingJob, DataCorrection, BylawType, ScheduleConfig } from '../types/municipality.types'
import { MunicipalityService } from '../services/municipalityService'
import { ScrapingService } from '../services/scrapingService'
import { 
  Users, 
  Building, 
  FileText, 
  Settings, 
  Play, 
  AlertCircle, 
  Clock,
  Database,
  Edit,
  Save,
  X,
  Plus,
  RefreshCw,
  Calendar,
  Eye,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader,
  Activity,
  BarChart3
} from 'lucide-react'

interface AdminDashboardProps {
  user: any
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ user }) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [isAdmin, setIsAdmin] = useState(false)

  // Check admin status - simplified
  useEffect(() => {
    // For now, all authenticated users are admins
    setIsAdmin(!!user)
  }, [user])

  // Fetch dashboard data
  const { data: municipalities = [] } = useQuery({
    queryKey: ['municipalities'],
    queryFn: () => MunicipalityService.getMunicipalities(),
    enabled: isAdmin
  })

  const { data: bylawStats } = useQuery({
    queryKey: ['bylaws', 'stats'],
    queryFn: async () => {
      // Mock stats for now
      return {
        total: 0,
        active: 0,
        categories: []
      }
    },
    enabled: isAdmin
  })

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h2>
          <p className="text-gray-600">Please log in to access the admin dashboard.</p>
        </div>
      </div>
    )
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">You don't have permission to access the admin dashboard.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
          <p className="text-lg text-gray-600">
            Manage municipalities, configure scraping, and monitor system status
          </p>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { key: 'overview', label: 'Overview', icon: Database },
                { key: 'municipalities', label: 'Municipalities', icon: Building },
                { key: 'scraping', label: 'Scraping Jobs', icon: Settings },
                { key: 'users', label: 'Users', icon: Users }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === key
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <OverviewTab municipalities={municipalities} bylawStats={bylawStats} />
          )}
          
          {activeTab === 'municipalities' && (
            <MunicipalitiesTab municipalities={municipalities} />
          )}
          
          {activeTab === 'scraping' && (
            <ScrapingTab municipalities={municipalities} />
          )}
          
          {activeTab === 'users' && (
            <UsersTab />
          )}
        </div>
      </div>
    </div>
  )
}

// LoginForm moved to App.tsx

const OverviewTab: React.FC<{ municipalities: Municipality[], bylawStats: any }> = ({ 
  municipalities, 
  bylawStats 
}) => {
  const stats = [
    {
      name: 'Total Municipalities',
      value: municipalities.length,
      icon: Building,
      color: 'bg-blue-500'
    },
    {
      name: 'Total Bylaws',
      value: bylawStats?.total || 0,
      icon: FileText,
      color: 'bg-green-500'
    },
    {
      name: 'Categories',
      value: bylawStats?.categories?.length || 0,
      icon: Database,
      color: 'bg-purple-500'
    },
    {
      name: 'Active Scraping Jobs',
      value: 0, // Would need separate query
      icon: Settings,
      color: 'bg-orange-500'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          <div className="text-center text-gray-500">
            <Clock className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No recent activity to display</p>
          </div>
        </div>
      </div>
    </div>
  )
}

const MunicipalitiesTab: React.FC<{ municipalities: Municipality[] }> = ({ municipalities }) => {
  const [showAddModal, setShowAddModal] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    province: '',
    website_url: ''
  })
  const [loading, setLoading] = useState(false)
  const queryClient = useQueryClient()

  const handleAdd = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/municipalities', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })
      
      if (!response.ok) {
        throw new Error('Failed to create municipality')
      }
      setShowAddModal(false)
      setFormData({ name: '', province: '', website_url: '' })
      // Refresh the municipalities list
      queryClient.invalidateQueries({ queryKey: ['municipalities'] })
      alert('Municipality added successfully!')
    } catch (error) {
      console.error('Error adding municipality:', error)
      alert('Failed to add municipality')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="px-6 py-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Municipalities</h3>
          <button 
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Add Municipality
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Province
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {municipalities.map((municipality) => (
              <tr key={municipality.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {municipality.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {municipality.province}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {municipality.type}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                    Active
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-primary-600 hover:text-primary-900 mr-3">
                    Edit
                  </button>
                  <button className="text-red-600 hover:text-red-900">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Municipality Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium mb-4">Add Municipality</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Municipality Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g., Toronto"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Province
                </label>
                <select
                  value={formData.province}
                  onChange={(e) => setFormData({ ...formData, province: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  required
                >
                  <option value="">Select Province</option>
                  <option value="Ontario">Ontario</option>
                  <option value="Quebec">Quebec</option>
                  <option value="British Columbia">British Columbia</option>
                  <option value="Alberta">Alberta</option>
                  <option value="Manitoba">Manitoba</option>
                  <option value="Saskatchewan">Saskatchewan</option>
                  <option value="Nova Scotia">Nova Scotia</option>
                  <option value="New Brunswick">New Brunswick</option>
                  <option value="Newfoundland and Labrador">Newfoundland and Labrador</option>
                  <option value="Prince Edward Island">Prince Edward Island</option>
                  <option value="Northwest Territories">Northwest Territories</option>
                  <option value="Yukon">Yukon</option>
                  <option value="Nunavut">Nunavut</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Website URL (optional)
                </label>
                <input
                  type="url"
                  value={formData.website_url}
                  onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="https://www.example.ca"
                />
              </div>
            </div>
            
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAdd}
                disabled={loading || !formData.name || !formData.province}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Adding...' : 'Add Municipality'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const ScrapingTab: React.FC<{ municipalities: Municipality[] }> = ({ municipalities }) => {
  const [activeSubTab, setActiveSubTab] = useState('overview')
  const [selectedMunicipality, setSelectedMunicipality] = useState<Municipality | null>(null)

  const { data: scrapingJobs = [], refetch: refetchJobs } = useQuery({
    queryKey: ['scraping-jobs'],
    queryFn: async () => {
      // Mock data for now - replace with real API call
      return []
    },
    refetchInterval: 5000 // Refetch every 5 seconds for real-time updates
  })

  const { data: scrapingStats } = useQuery({
    queryKey: ['scraping-stats'],
    queryFn: async () => {
      // Mock data for now - replace with real API call
      return {
        total_jobs: 0,
        running_jobs: 0,
        success_rate: 0
      }
    },
    refetchInterval: 30000 // Refetch every 30 seconds
  })

  const { data: dataCorrections = [] } = useQuery({
    queryKey: ['data-corrections'],
    queryFn: async () => {
      // Mock data for now - replace with real API call
      return []
    }
  })

  const subTabs = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'configuration', label: 'Configuration', icon: Settings },
    { key: 'jobs', label: 'Jobs Monitor', icon: Activity },
    { key: 'schedule', label: 'Scheduling', icon: Calendar },
    { key: 'corrections', label: 'Data Corrections', icon: Edit }
  ]

  return (
    <div className="space-y-6">
      {/* Sub-tabs */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Scraping Management</h3>
          <div className="flex space-x-4">
            {subTabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveSubTab(key)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeSubTab === key
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {activeSubTab === 'overview' && (
            <ScrapingOverview 
              municipalities={municipalities}
              scrapingJobs={scrapingJobs}
              scrapingStats={scrapingStats}
              dataCorrections={dataCorrections}
            />
          )}
          
          {activeSubTab === 'configuration' && (
            <ScrapingConfiguration 
              municipalities={municipalities}
              selectedMunicipality={selectedMunicipality}
              setSelectedMunicipality={setSelectedMunicipality}
            />
          )}
          
          {activeSubTab === 'jobs' && (
            <ScrapingJobsMonitor 
              municipalities={municipalities}
              scrapingJobs={scrapingJobs}
              refetchJobs={refetchJobs}
            />
          )}
          
          {activeSubTab === 'schedule' && (
            <ScrapingSchedule 
              municipalities={municipalities}
              selectedMunicipality={selectedMunicipality}
              setSelectedMunicipality={setSelectedMunicipality}
            />
          )}
          
          {activeSubTab === 'corrections' && (
            <DataCorrections 
              municipalities={municipalities}
              dataCorrections={dataCorrections}
            />
          )}
        </div>
      </div>
    </div>
  )
}

const UsersTab: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="px-6 py-4 border-b">
        <h3 className="text-lg font-medium text-gray-900">User Management</h3>
      </div>
      <div className="p-6">
        <div className="text-center text-gray-500">
          <Users className="w-12 h-12 mx-auto mb-4 text-gray-300" />
          <p>User management functionality coming soon</p>
        </div>
      </div>
    </div>
  )
}

// Scraping Tab Sub-components
const ScrapingOverview: React.FC<{
  municipalities: Municipality[]
  scrapingJobs: ScrapingJob[]
  scrapingStats: any
  dataCorrections: DataCorrection[]
}> = ({ municipalities, scrapingJobs, scrapingStats, dataCorrections }) => {
  const recentJobs = scrapingJobs.slice(0, 5)
  const pendingCorrections = dataCorrections.filter(c => c.status === 'pending')

  const stats = [
    {
      name: 'Total Jobs',
      value: scrapingStats?.total_jobs || 0,
      icon: Activity,
      color: 'bg-blue-500'
    },
    {
      name: 'Running Jobs',
      value: scrapingStats?.running_jobs || 0,
      icon: Loader,
      color: 'bg-yellow-500'
    },
    {
      name: 'Success Rate',
      value: `${Math.round(scrapingStats?.success_rate || 0)}%`,
      icon: CheckCircle2,
      color: 'bg-green-500'
    },
    {
      name: 'Pending Corrections',
      value: pendingCorrections.length,
      icon: AlertTriangle,
      color: 'bg-red-500'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center">
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Jobs */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-lg font-medium text-gray-900 mb-4">Recent Jobs</h4>
        <div className="space-y-3">
          {recentJobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between p-3 bg-white rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                  job.status === 'completed' ? 'bg-green-500' :
                  job.status === 'running' ? 'bg-yellow-500' :
                  job.status === 'failed' ? 'bg-red-500' :
                  'bg-gray-400'
                }`} />
                <div>
                  <p className="font-medium">{municipalities.find(m => m.id === job.municipality_id)?.name}</p>
                  <p className="text-sm text-gray-500">{job.type} • {job.status}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">
                  {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Unknown'}
                </p>
              </div>
            </div>
          ))}
          {recentJobs.length === 0 && (
            <p className="text-gray-500 text-center py-8">No recent jobs</p>
          )}
        </div>
      </div>
    </div>
  )
}

const ScrapingConfiguration: React.FC<{
  municipalities: Municipality[]
  selectedMunicipality: Municipality | null
  setSelectedMunicipality: (municipality: Municipality | null) => void
}> = ({ municipalities, selectedMunicipality, setSelectedMunicipality }) => {
  const [configForm, setConfigForm] = useState<Partial<MunicipalityConfig>>({})
  const [isEditing, setIsEditing] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResults, setTestResults] = useState<any>(null)

  const { data: municipalityConfig, refetch: refetchConfig } = useQuery({
    queryKey: ['municipality-config', selectedMunicipality?.id],
    queryFn: async () => {
      if (!selectedMunicipality) return null
      // Mock data for now - replace with real API call
      return null
    },
    enabled: !!selectedMunicipality
  })

  useEffect(() => {
    if (municipalityConfig) {
      setConfigForm(municipalityConfig)
    } else if (selectedMunicipality) {
      // Initialize default config
      setConfigForm({
        scraping_enabled: false,
        scraping_schedule: '0 2 * * *',
        scraping_config: {
          base_url: '',
          selectors: {
            bylaw_links: '',
            title: '',
            number: '',
            content: '',
            date_enacted: ''
          },
          pagination: {
            enabled: false,
            selector: '',
            max_pages: 10
          },
          filters: {
            bylaw_types: [BylawType.ZONING, BylawType.ADU, BylawType.BUILDING_CODES],
            keywords: []
          }
        }
      })
    }
  }, [municipalityConfig, selectedMunicipality])

  const handleSave = async () => {
    if (!selectedMunicipality || !configForm.scraping_config) return

    try {
      // Mock save for now - replace with real API call
      console.log('Saving config for municipality:', selectedMunicipality.id, configForm)
      setIsEditing(false)
      refetchConfig()
      alert('Configuration saved successfully')
    } catch (error) {
      console.error('Error saving config:', error)
      alert('Failed to save configuration')
    }
  }

  const handleTest = async () => {
    if (!selectedMunicipality) return

    setIsTesting(true)
    try {
      // Mock test for now - replace with real API call
      console.log('Testing config for municipality:', selectedMunicipality.id, configForm.scraping_config)
      setTestResults({ success: true, message: 'Test completed successfully' })
    } catch (error) {
      console.error('Error testing config:', error)
      setTestResults({ success: false, message: 'Test failed' })
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Municipality Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Municipality
        </label>
        <select
          value={selectedMunicipality?.id || ''}
          onChange={(e) => {
            const municipality = municipalities.find(m => m.id === e.target.value)
            setSelectedMunicipality(municipality || null)
            setIsEditing(false)
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Select a municipality</option>
          {municipalities.map((municipality) => (
            <option key={municipality.id} value={municipality.id}>
              {municipality.name}, {municipality.province}
            </option>
          ))}
        </select>
      </div>

      {selectedMunicipality && (
        <div className="space-y-6">
          {/* Configuration Form */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">
                Configuration for {selectedMunicipality.name}
              </h4>
              <div className="flex space-x-2">
                {!isEditing ? (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Edit</span>
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleTest}
                      disabled={isTesting}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Eye className="w-4 h-4" />
                      <span>{isTesting ? 'Testing...' : 'Test'}</span>
                    </button>
                    <button
                      onClick={handleSave}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      <Save className="w-4 h-4" />
                      <span>Save</span>
                    </button>
                    <button
                      onClick={() => setIsEditing(false)}
                      className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                    >
                      <X className="w-4 h-4" />
                      <span>Cancel</span>
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Basic Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scraping Enabled
                </label>
                <select
                  value={configForm.scraping_enabled ? 'true' : 'false'}
                  onChange={(e) => setConfigForm({
                    ...configForm,
                    scraping_enabled: e.target.value === 'true'
                  })}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                >
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Base URL
                </label>
                <input
                  type="url"
                  value={configForm.scraping_config?.base_url || ''}
                  onChange={(e) => setConfigForm({
                    ...configForm,
                    scraping_config: {
                      ...configForm.scraping_config!,
                      base_url: e.target.value
                    }
                  })}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                  placeholder="https://example.com/bylaws"
                />
              </div>
            </div>

            {/* CSS Selectors */}
            <div className="mt-6">
              <h5 className="text-md font-medium text-gray-900 mb-4">CSS Selectors</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(configForm.scraping_config?.selectors || {}).map(([key, value]) => (
                  <div key={key}>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </label>
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => setConfigForm({
                        ...configForm,
                        scraping_config: {
                          ...configForm.scraping_config!,
                          selectors: {
                            ...configForm.scraping_config!.selectors,
                            [key]: e.target.value
                          }
                        }
                      })}
                      disabled={!isEditing}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                      placeholder={`.${key.replace(/_/g, '-')}`}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Bylaw Types Filter */}
            <div className="mt-6">
              <h5 className="text-md font-medium text-gray-900 mb-4">Bylaw Types to Collect</h5>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.values(BylawType).map((type) => (
                  <label key={type} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={configForm.scraping_config?.filters?.bylaw_types?.includes(type) || false}
                      onChange={(e) => {
                        const currentTypes = configForm.scraping_config?.filters?.bylaw_types || []
                        const newTypes = e.target.checked
                          ? [...currentTypes, type]
                          : currentTypes.filter(t => t !== type)
                        
                        setConfigForm({
                          ...configForm,
                          scraping_config: {
                            ...configForm.scraping_config!,
                            filters: {
                              ...configForm.scraping_config!.filters!,
                              bylaw_types: newTypes
                            }
                          }
                        })
                      }}
                      disabled={!isEditing}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">
                      {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Pagination Settings */}
            <div className="mt-6">
              <h5 className="text-md font-medium text-gray-900 mb-4">Pagination</h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enable Pagination
                  </label>
                  <select
                    value={configForm.scraping_config?.pagination?.enabled ? 'true' : 'false'}
                    onChange={(e) => setConfigForm({
                      ...configForm,
                      scraping_config: {
                        ...configForm.scraping_config!,
                        pagination: {
                          ...configForm.scraping_config!.pagination!,
                          enabled: e.target.value === 'true'
                        }
                      }
                    })}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                  >
                    <option value="true">Enabled</option>
                    <option value="false">Disabled</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Next Page Selector
                  </label>
                  <input
                    type="text"
                    value={configForm.scraping_config?.pagination?.selector || ''}
                    onChange={(e) => setConfigForm({
                      ...configForm,
                      scraping_config: {
                        ...configForm.scraping_config!,
                        pagination: {
                          ...configForm.scraping_config!.pagination!,
                          selector: e.target.value
                        }
                      }
                    })}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                    placeholder=".next-page"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Max Pages
                  </label>
                  <input
                    type="number"
                    value={configForm.scraping_config?.pagination?.max_pages || 10}
                    onChange={(e) => setConfigForm({
                      ...configForm,
                      scraping_config: {
                        ...configForm.scraping_config!,
                        pagination: {
                          ...configForm.scraping_config!.pagination!,
                          max_pages: parseInt(e.target.value)
                        }
                      }
                    })}
                    disabled={!isEditing}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-gray-100"
                    min="1"
                    max="100"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Test Results */}
          {testResults && (
            <div className={`p-4 rounded-lg ${testResults.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex items-center space-x-2">
                {testResults.success ? (
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-600" />
                )}
                <h5 className={`font-medium ${testResults.success ? 'text-green-800' : 'text-red-800'}`}>
                  Test Results
                </h5>
              </div>
              <p className={`mt-2 ${testResults.success ? 'text-green-700' : 'text-red-700'}`}>
                {testResults.message}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const ScrapingJobsMonitor: React.FC<{
  municipalities: Municipality[]
  scrapingJobs: ScrapingJob[]
  refetchJobs: () => void
}> = ({ municipalities, scrapingJobs, refetchJobs }) => {
  const [selectedMunicipalityId, setSelectedMunicipalityId] = useState<string>('')
  const [showJobDetails, setShowJobDetails] = useState<string | null>(null)

  const handleStartManualJob = async (municipalityId: string) => {
    try {
      // Mock job start for now - replace with real API call
      console.log('Starting manual job for municipality:', municipalityId)
      refetchJobs()
      alert('Manual job started successfully')
    } catch (error) {
      console.error('Error starting manual job:', error)
      alert('Failed to start manual job')
    }
  }

  const handleCancelJob = async (jobId: string) => {
    try {
      // Mock job cancel for now - replace with real API call
      console.log('Cancelling job:', jobId)
      refetchJobs()
      alert('Job cancelled successfully')
    } catch (error) {
      console.error('Error cancelling job:', error)
      alert('Failed to cancel job')
    }
  }

  const filteredJobs = selectedMunicipalityId
    ? scrapingJobs.filter(job => job.municipality_id === selectedMunicipalityId)
    : scrapingJobs

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex flex-col sm:flex-row gap-4">
          <select
            value={selectedMunicipalityId}
            onChange={(e) => setSelectedMunicipalityId(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Municipalities</option>
            {municipalities.map((municipality) => (
              <option key={municipality.id} value={municipality.id}>
                {municipality.name}, {municipality.province}
              </option>
            ))}
          </select>

          <button
            onClick={() => refetchJobs()}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {selectedMunicipalityId && (
          <button
            onClick={() => handleStartManualJob(selectedMunicipalityId)}
            className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Play className="w-4 h-4" />
            <span>Start Manual Job</span>
          </button>
        )}
      </div>

      {/* Jobs List */}
      <div className="bg-gray-50 rounded-lg">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Municipality
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Progress
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredJobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {municipalities.find(m => m.id === job.municipality_id)?.name || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {job.type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      job.status === 'completed' ? 'bg-green-100 text-green-800' :
                      job.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                      job.status === 'failed' ? 'bg-red-100 text-red-800' :
                      job.status === 'pending' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {job.progress ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(job.progress.current / job.progress.total) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs">
                          {job.progress.current}/{job.progress.total}
                        </span>
                      </div>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {job.started_at ? new Date(job.started_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setShowJobDetails(job.id)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {(job.status === 'running' || job.status === 'pending') && (
                        <button
                          onClick={() => handleCancelJob(job.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredJobs.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No jobs found</p>
          </div>
        )}
      </div>

      {/* Job Details Modal */}
      {showJobDetails && (
        <JobDetailsModal
          job={scrapingJobs.find(j => j.id === showJobDetails)!}
          municipality={municipalities.find(m => m.id === scrapingJobs.find(j => j.id === showJobDetails)?.municipality_id)!}
          onClose={() => setShowJobDetails(null)}
        />
      )}
    </div>
  )
}

const JobDetailsModal: React.FC<{
  job: ScrapingJob
  municipality: Municipality
  onClose: () => void
}> = ({ job, municipality, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium">Job Details</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Municipality</p>
              <p className="text-sm text-gray-900">{municipality.name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Type</p>
              <p className="text-sm text-gray-900">{job.type}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Status</p>
              <p className="text-sm text-gray-900">{job.status}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Created</p>
              <p className="text-sm text-gray-900">
                {new Date(job.created_at).toLocaleString()}
              </p>
            </div>
          </div>

          {job.progress && (
            <div>
              <p className="text-sm font-medium text-gray-500 mb-2">Progress</p>
              <div className="bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full"
                  style={{ width: `${(job.progress.current / job.progress.total) * 100}%` }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {job.progress.current} / {job.progress.total} • {job.progress.stage}
              </p>
            </div>
          )}

          {job.result && (
            <div>
              <p className="text-sm font-medium text-gray-500 mb-2">Results</p>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Found: {job.result.bylaws_found}</div>
                  <div>Created: {job.result.bylaws_created}</div>
                  <div>Updated: {job.result.bylaws_updated}</div>
                  <div>Skipped: {job.result.bylaws_skipped}</div>
                </div>
              </div>
            </div>
          )}

          {job.error_message && (
            <div>
              <p className="text-sm font-medium text-gray-500 mb-2">Error</p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-700">{job.error_message}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const ScrapingSchedule: React.FC<{
  municipalities: Municipality[]
  selectedMunicipality: Municipality | null
  setSelectedMunicipality: (municipality: Municipality | null) => void
}> = ({ municipalities, selectedMunicipality, setSelectedMunicipality }) => {
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig>({
    frequency: 'daily',
    cron_expression: '0 2 * * *',
    timezone: 'America/Toronto',
    enabled: false
  })

  const handleSaveSchedule = async () => {
    if (!selectedMunicipality) return

    try {
      // Mock schedule save for now - replace with real API call
      console.log('Saving schedule for municipality:', selectedMunicipality.id, scheduleConfig)
      alert('Schedule updated successfully')
    } catch (error) {
      console.error('Error updating schedule:', error)
      alert('Failed to update schedule')
    }
  }

  const timezones = [
    'America/Toronto',
    'America/Vancouver',
    'America/Edmonton',
    'America/Winnipeg',
    'America/Halifax',
    'America/St_Johns'
  ]

  return (
    <div className="space-y-6">
      {/* Municipality Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Municipality
        </label>
        <select
          value={selectedMunicipality?.id || ''}
          onChange={(e) => {
            const municipality = municipalities.find(m => m.id === e.target.value)
            setSelectedMunicipality(municipality || null)
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">Select a municipality</option>
          {municipalities.map((municipality) => (
            <option key={municipality.id} value={municipality.id}>
              {municipality.name}, {municipality.province}
            </option>
          ))}
        </select>
      </div>

      {selectedMunicipality && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">
            Schedule Configuration for {selectedMunicipality.name}
          </h4>

          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Schedule Enabled
                </label>
                <select
                  value={scheduleConfig.enabled ? 'true' : 'false'}
                  onChange={(e) => setScheduleConfig({
                    ...scheduleConfig,
                    enabled: e.target.value === 'true'
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Frequency
                </label>
                <select
                  value={scheduleConfig.frequency}
                  onChange={(e) => setScheduleConfig({
                    ...scheduleConfig,
                    frequency: e.target.value as any
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>

            {scheduleConfig.frequency === 'custom' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cron Expression
                </label>
                <input
                  type="text"
                  value={scheduleConfig.cron_expression || ''}
                  onChange={(e) => setScheduleConfig({
                    ...scheduleConfig,
                    cron_expression: e.target.value
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="0 2 * * *"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Use cron format (minute hour day month weekday)
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timezone
              </label>
              <select
                value={scheduleConfig.timezone}
                onChange={(e) => setScheduleConfig({
                  ...scheduleConfig,
                  timezone: e.target.value
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                {timezones.map(tz => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleSaveSchedule}
                className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                <Save className="w-4 h-4" />
                <span>Save Schedule</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const DataCorrections: React.FC<{
  municipalities: Municipality[]
  dataCorrections: DataCorrection[]
}> = ({ municipalities, dataCorrections }) => {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedMunicipalityId, setSelectedMunicipalityId] = useState<string>('')

  const filteredCorrections = selectedMunicipalityId
    ? dataCorrections.filter(c => c.municipality_id === selectedMunicipalityId)
    : dataCorrections

  const handleApplyCorrection = async (correctionId: string) => {
    try {
      // Mock correction apply for now - replace with real API call
      console.log('Applying correction:', correctionId)
      alert('Correction applied successfully')
    } catch (error) {
      console.error('Error applying correction:', error)
      alert('Failed to apply correction')
    }
  }

  const handleRejectCorrection = async (correctionId: string) => {
    try {
      // Mock correction reject for now - replace with real API call
      console.log('Rejecting correction:', correctionId)
      alert('Correction rejected')
    } catch (error) {
      console.error('Error rejecting correction:', error)
      alert('Failed to reject correction')
    }
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <select
          value={selectedMunicipalityId}
          onChange={(e) => setSelectedMunicipalityId(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          <option value="">All Municipalities</option>
          {municipalities.map((municipality) => (
            <option key={municipality.id} value={municipality.id}>
              {municipality.name}, {municipality.province}
            </option>
          ))}
        </select>

        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          <Plus className="w-4 h-4" />
          <span>Create Correction</span>
        </button>
      </div>

      {/* Corrections List */}
      <div className="bg-gray-50 rounded-lg">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Municipality
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCorrections.map((correction) => (
                <tr key={correction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {municipalities.find(m => m.id === correction.municipality_id)?.name || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {correction.correction_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      correction.status === 'applied' ? 'bg-green-100 text-green-800' :
                      correction.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {correction.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(correction.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {correction.status === 'pending' && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApplyCorrection(correction.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleRejectCorrection(correction.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          <XCircle className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredCorrections.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Edit className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No corrections found</p>
          </div>
        )}
      </div>

      {/* Create Correction Modal */}
      {showCreateModal && (
        <CreateCorrectionModal
          municipalities={municipalities}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </div>
  )
}

const CreateCorrectionModal: React.FC<{
  municipalities: Municipality[]
  onClose: () => void
}> = ({ municipalities, onClose }) => {
  const [formData, setFormData] = useState({
    municipality_id: '',
    correction_type: 'title' as DataCorrection['correction_type'],
    original_value: '',
    corrected_value: '',
    reason: ''
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      // Mock correction creation for now - replace with real API call
      console.log('Creating correction:', {
        ...formData,
        created_by: 'admin',
        status: 'pending'
      })
      onClose()
      alert('Correction created successfully')
    } catch (error) {
      console.error('Error creating correction:', error)
      alert('Failed to create correction')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-medium mb-4">Create Data Correction</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Municipality
            </label>
            <select
              value={formData.municipality_id}
              onChange={(e) => setFormData({ ...formData, municipality_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="">Select Municipality</option>
              {municipalities.map((municipality) => (
                <option key={municipality.id} value={municipality.id}>
                  {municipality.name}, {municipality.province}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correction Type
            </label>
            <select
              value={formData.correction_type}
              onChange={(e) => setFormData({ ...formData, correction_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="title">Title</option>
              <option value="content">Content</option>
              <option value="date">Date</option>
              <option value="number">Number</option>
              <option value="category">Category</option>
              <option value="delete">Delete</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Original Value
            </label>
            <textarea
              value={formData.original_value}
              onChange={(e) => setFormData({ ...formData, original_value: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              rows={3}
              required
            />
          </div>

          {formData.correction_type !== 'delete' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Corrected Value
              </label>
              <textarea
                value={formData.corrected_value}
                onChange={(e) => setFormData({ ...formData, corrected_value: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                rows={3}
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason
            </label>
            <textarea
              value={formData.reason}
              onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              rows={2}
              required
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Create Correction
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}