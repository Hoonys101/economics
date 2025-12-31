import { useState, useEffect } from 'react'
import { DashboardSnapshot } from '../types/dashboard'

export const useSimulation = () => {
  const [data, setData] = useState<DashboardSnapshot | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/simulation/dashboard')
        const json = await response.json()
        setData(json)
        setLoading(false)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      }
    }

    const interval = setInterval(fetchData, 1000)
    fetchData()

    return () => clearInterval(interval)
  }, [])

  return { data, loading }
}
