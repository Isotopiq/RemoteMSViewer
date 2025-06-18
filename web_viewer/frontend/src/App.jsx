import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
  Chip,
  CircularProgress,
  AppBar,
  Toolbar,
  Container
} from '@mui/material'
import { PlayArrow, Stop, Refresh } from '@mui/icons-material'
import Plot from 'react-plotly.js'
// Choose one approach: either Socket.IO or EventSource
// For direct connection to backend:
import { io } from 'socket.io-client'
// For SSE connection to remote service:
// import EventSource from 'eventsource' // Not needed as EventSource is built into browsers
import KapelczakLogo from './KapelczakLogo'

function App() {
  const [scanData, setScanData] = useState(null)
  const [plotData, setPlotData] = useState({
    centroidData: [],
    noiseData: []
  })
  const [status, setStatus] = useState({
    instrument_connected: false,
    online_access: false,
    acquisition_active: false
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const ws = useRef(null)
  const lastUpdateTime = useRef(0)
  const UPDATE_THROTTLE = 500 // Update plot every 500ms max

  // Choose one approach: either direct connection to backend or remote service
  // Set this to your remote service URL if using the remote approach, or to the backend URL if direct
  const API_BASE_URL = 'http://localhost:5000' // For direct connection
  // const API_BASE_URL = 'https://your-relay-service.com' // For remote service

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/status`)
      const data = await response.json()
      if (response.ok && data.success) {
        setStatus(data.status)
        setError(null)
      } else {
        setError(data.error || 'Failed to fetch status')
      }
    } catch (err) {
      setError('Failed to connect to server')
    }
  }

  const startAcquisition = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/start_acquisition`, {
        method: 'POST'
      })
      const data = await response.json()
      if (response.ok && data.success) {
        setError(null)
        fetchStatus()
      } else {
        setError(data.error || 'Failed to start acquisition')
      }
    } catch (err) {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }
  
  const stopAcquisition = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/stop_acquisition`, {
        method: 'POST'
      })
      const data = await response.json()
      if (response.ok && data.success) {
        setError(null)
        fetchStatus()
      } else {
        setError(data.error || 'Failed to stop acquisition')
      }
    } catch (err) {
      setError('Failed to connect to server')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()

    // Choose one approach: either Socket.IO or EventSource
    // Socket.IO approach (direct connection to backend):
    ws.current = io(API_BASE_URL)

    ws.current.on('connect', () => {
      console.log('Connected to server')
      setError(null)
    })

    ws.current.on('disconnect', () => {
      console.log('Disconnected from server')
      setError('Disconnected from server')
    })

    ws.current.on('scan_data', (data) => {
      const currentTime = Date.now()
      if (currentTime - lastUpdateTime.current >= UPDATE_THROTTLE) {
        setScanData(data)
        lastUpdateTime.current = currentTime
      }
    })

    // EventSource approach (for remote service):
    // Uncomment this block and comment out the Socket.IO block above if using SSE
    /*
    const eventSource = new EventSource(`${API_BASE_URL}/events`)
    
    eventSource.onopen = () => {
      console.log('Connected to event stream')
      setError(null)
    }
  
    eventSource.onerror = (error) => {
      console.error('EventSource error:', error)
      setError('Connection to data stream failed')
    }
  
    eventSource.addEventListener('message', (event) => {
      const currentTime = Date.now()
      if (currentTime - lastUpdateTime.current >= UPDATE_THROTTLE) {
        try {
          const data = JSON.parse(event.data)
          setScanData(data)
          lastUpdateTime.current = currentTime
        } catch (err) {
          console.error('Error parsing event data:', err)
        }
      }
    })
    */

    return () => {
      // Clean up Socket.IO connection
      if (ws.current) {
        ws.current.disconnect()
      }
      
      // Clean up EventSource if using that approach
      // if (eventSource) {
      //   eventSource.close()
      // }
    }
  }, [])

  useEffect(() => {
    if (scanData && scanData.masses && scanData.intensities) {
      // Create centroid lines (vertical lines from baseline to peak height)
      const centroidTrace = {
        x: [],
        y: [],
        type: 'scatter',
        mode: 'lines',
        line: {
          color: '#1976d2',
          width: 1
        },
        name: 'Centroid Data',
        hovertemplate: 'm/z: %{customdata[0]}<br>Intensity: %{customdata[1]}<extra></extra>',
        customdata: []
      }

      // Find the top 5 most abundant peaks
      const peakData = scanData.masses.map((mass, index) => ({
        mass: mass,
        intensity: scanData.intensities[index],
        index: index
      }))
      
      // Sort by intensity (descending) and take top 5
      const top5Peaks = peakData
        .sort((a, b) => b.intensity - a.intensity)
        .slice(0, 5)

      // For each mass/intensity pair, create a vertical line
      for (let i = 0; i < scanData.masses.length; i++) {
        const mass = scanData.masses[i]
        const intensity = scanData.intensities[i]
        
        // Add points for vertical line (from 0 to intensity)
        centroidTrace.x.push(mass, mass, null)
        centroidTrace.y.push(0, intensity, null)
        centroidTrace.customdata.push([mass.toFixed(4), intensity.toFixed(0)], [mass.toFixed(4), intensity.toFixed(0)], [null, null])
      }

      setPlotData({
        centroidData: [centroidTrace],
        top5Peaks: top5Peaks
      })
    }
  }, [scanData])

  const getStatusColor = () => {
    if (!status.instrument_connected) return 'error'
    if (!status.online_access) return 'warning'
    if (status.acquisition_active) return 'success'
    return 'info'
  }

  const getStatusText = () => {
    if (!status.instrument_connected) return 'Instrument Disconnected'
    if (!status.online_access) return 'Offline Access'
    if (status.acquisition_active) return 'Acquisition Active'
    return 'Ready'
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: '100vh', bgcolor: 'grey.50' }}>
      {/* Header */}
      <AppBar position="static" sx={{ bgcolor: 'white', color: 'text.primary', boxShadow: 1 }}>
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
            <KapelczakLogo sx={{ width: 64, height: 64, mr: 2 }} />
            <Box sx={{ borderLeft: 1, borderColor: 'grey.300', pl: 2 }}>
              <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', color: 'grey.900' }}>
                Mass Spectrometry
              </Typography>
              <Typography variant="h6" sx={{ color: 'grey.600' }}>
                Real-time Web Viewer
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip 
              label={getStatusText()} 
              color={getStatusColor()} 
              size="medium"
            />
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchStatus}
              sx={{ color: 'grey.700', borderColor: 'grey.300' }}
            >
              Refresh
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 4 }}>
        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3} sx={{ mb: 4 }}>
          {/* Status Panel */}
          <Grid item xs={12} lg={4}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Instrument Status
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Connected:
                    </Typography>
                    <Chip 
                      label={status.instrument_connected ? 'Yes' : 'No'} 
                      color={status.instrument_connected ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Online Access:
                    </Typography>
                    <Chip 
                      label={status.online_access ? 'Yes' : 'No'} 
                      color={status.online_access ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Acquisition:
                    </Typography>
                    <Chip 
                      label={status.acquisition_active ? 'Active' : 'Inactive'} 
                      color={status.acquisition_active ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Acquisition Controls */}
          <Grid item xs={12} lg={8}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Acquisition Controls
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="success"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
                  onClick={startAcquisition}
                  disabled={loading || !status.instrument_connected || status.acquisition_active}
                >
                  Start Acquisition
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  size="large"
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Stop />}
                  onClick={stopAcquisition}
                  disabled={loading || !status.instrument_connected || !status.acquisition_active}
                >
                  Stop Acquisition
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>

        {/* Mass Spectrum Plot */}
        <Paper sx={{ p: 3, mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Mass Spectrum
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Scan #{scanData?.scan_number || 'N/A'}
            </Typography>
          </Box>
          <Box sx={{ height: 400 }}>
            {plotData.centroidData.length > 0 ? (
              <Plot
                data={plotData.centroidData}
                layout={{
                  title: {
                    text: 'Real-time Mass Spectrum',
                    font: { size: 18, color: '#374151' }
                  },
                  xaxis: {
                    title: { text: 'm/z', font: { size: 14, color: '#6B7280' } },
                    showgrid: true,
                    gridcolor: '#F3F4F6'
                  },
                  yaxis: {
                    title: { text: 'Intensity', font: { size: 14, color: '#6B7280' } },
                    showgrid: true,
                    gridcolor: '#F3F4F6'
                  },
                  showlegend: true,
                  margin: { t: 50, r: 50, b: 50, l: 80 },
                  plot_bgcolor: 'white',
                  paper_bgcolor: 'white',
                  annotations: plotData.top5Peaks ? plotData.top5Peaks.map(peak => ({
                    x: peak.mass,
                    y: peak.intensity,
                    text: peak.mass.toFixed(4),
                    showarrow: false,
                    yshift: 15,
                    font: {
                      size: 10,
                      color: 'black'
                    },
                    bgcolor: 'rgba(255, 255, 255, 0.9)',
                    bordercolor: 'black',
                    borderwidth: 1
                  })) : []
                }}
                style={{ width: '100%', height: '100%' }}
                config={{
                  responsive: true,
                  displayModeBar: true,
                  modeBarButtonsToRemove: ['pan2d', 'lasso2d']
                }}
              />
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <CircularProgress sx={{ mb: 2 }} />
                <Typography color="text.secondary">
                  Waiting for data...
                </Typography>
              </Box>
            )}
          </Box>
        </Paper>

        {/* Data Summary */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {scanData?.scan_number || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Scan Number
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {scanData?.masses?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Data Points
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {scanData?.masses ? Math.min(...scanData.masses).toFixed(2) : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Min m/z
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {scanData?.masses ? Math.max(...scanData.masses).toFixed(2) : 'N/A'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Max m/z
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}

export default App