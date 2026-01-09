import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Plane, Clock, MapPin, Navigation, Luggage, Shield, Globe, Send, Locate, Route } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Checkpoint {
  id: string;
  name: string;
  type: string;
  terminal: string;
  lat: number;
  lng: number;
  current_wait_minutes: number;
  historical_avg_minutes: number;
  status: string;
  last_updated: string;
}

interface Airport {
  code: string;
  name: string;
  city: string;
  lat: number;
  lng: number;
  terminals: string[];
  checkpoints: Checkpoint[];
}

interface Gate {
  name: string;
  lat: number;
  lng: number;
}

interface JourneyStep {
  step_name: string;
  location: string;
  lat: number;
  lng: number;
  estimated_wait_minutes: number;
  estimated_walk_minutes: number;
  distance_meters: number;
  checkpoint_id: string | null;
}

interface JourneyPlan {
  total_time_minutes: number;
  total_distance_meters: number;
  recommended_arrival_time: string;
  steps: JourneyStep[];
  buffer_minutes: number;
}

interface WaitTimeDistribution {
  p50: number;
  p80: number;
  p90: number;
  p95: number;
  mu: number;
  sigma: number;
  sample_size: number;
  confidence: string;
}

interface SegmentDistribution {
  step_name: string;
  location: string;
  lat: number;
  lng: number;
  wait_distribution: WaitTimeDistribution | null;
  walk_minutes: number;
  walk_distance_meters: number;
  checkpoint_id: string | null;
}

interface WillIMakeItResponse {
  probability_of_making_it: number;
  probability_percentage: number;
  status: string;
  status_message: string;
  total_time_p50: number;
  total_time_p80: number;
  total_time_p90: number;
  total_time_p95: number;
  time_until_boarding: number;
  buffer_minutes: number;
  leave_by_80: string;
  leave_by_90: string;
  leave_by_95: string;
  segments: SegmentDistribution[];
  simulation_runs: number;
  boarding_cutoff_minutes: number;
}

interface AirportSummary {
  code: string;
  name: string;
  city: string;
  lat: number;
  lng: number;
  terminals: string[];
}

const createCheckpointIcon = (waitMinutes: number, _type: string) => {
  let color = '#22c55e';
  if (waitMinutes > 35) color = '#ef4444';
  else if (waitMinutes > 20) color = '#f97316';
  else if (waitMinutes > 10) color = '#eab308';

  return L.divIcon({
    className: 'custom-checkpoint-icon',
    html: `<div style="
      background: ${color};
      color: white;
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: bold;
      border: 3px solid white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    ">${waitMinutes}m</div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
};

const createGateIcon = () => {
  return L.divIcon({
    className: 'custom-gate-icon',
    html: `<div style="
      background: #3b82f6;
      color: white;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 11px;
      font-weight: bold;
      border: 2px solid white;
      box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    ">✈️</div>`,
    iconSize: [32, 24],
    iconAnchor: [16, 12],
  });
};

const createUserIcon = () => {
  return L.divIcon({
    className: 'custom-user-icon',
    html: `<div style="
      background: #8b5cf6;
      color: white;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      border: 3px solid white;
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.3), 0 2px 8px rgba(0,0,0,0.3);
    ">📍</div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
};

function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] != null && center[1] != null) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

function App() {
  const [airports, setAirports] = useState<AirportSummary[]>([]);
  const [selectedAirportCode, setSelectedAirportCode] = useState<string>('JFK');
  const [airportData, setAirportData] = useState<Airport | null>(null);
  const [selectedTerminal, setSelectedTerminal] = useState<string>('');
  const [selectedGate, setSelectedGate] = useState<string>('');
  const [gates, setGates] = useState<Gate[]>([]);
  const [hasTsaPrecheck, setHasTsaPrecheck] = useState(false);
  const [hasCheckedBags, setHasCheckedBags] = useState(true);
  const [mobilityFactor, setMobilityFactor] = useState(1.0);
  const [journeyPlan, setJourneyPlan] = useState<JourneyPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [reportCheckpoint, setReportCheckpoint] = useState<Checkpoint | null>(null);
  const [reportedWaitTime, setReportedWaitTime] = useState('');
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([40.6413, -73.7781]);
  const [mapZoom, setMapZoom] = useState(15);
  
  // Will I Make It? state
  const [departureTime, setDepartureTime] = useState<string>('');
  const [willIMakeIt, setWillIMakeIt] = useState<WillIMakeItResponse | null>(null);
  const [calculatingProbability, setCalculatingProbability] = useState(false);

  useEffect(() => {
    fetchAirports();
  }, []);

  useEffect(() => {
    if (selectedAirportCode) {
      fetchAirportData(selectedAirportCode);
    }
  }, [selectedAirportCode]);

  useEffect(() => {
    if (selectedTerminal && selectedAirportCode) {
      fetchGates(selectedAirportCode, selectedTerminal);
    }
  }, [selectedTerminal, selectedAirportCode]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (selectedAirportCode) {
        fetchAirportData(selectedAirportCode);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [selectedAirportCode]);

  useEffect(() => {
    if (airportData) {
      setMapCenter([airportData.lat, airportData.lng]);
      setMapZoom(16);
    }
  }, [airportData]);

  const fetchAirports = async () => {
    try {
      const response = await fetch(`${API_URL}/api/airports`);
      const data = await response.json();
      setAirports(data.airports);
    } catch (error) {
      console.error('Failed to fetch airports:', error);
    }
  };

    const fetchAirportData = async (code: string) => {
      try {
        const response = await fetch(`${API_URL}/api/airports/${code}`);
        const data = await response.json();
        setAirportData(data);
        if (!selectedTerminal && data.terminals.length > 0) {
          setSelectedTerminal(data.terminals[0]);
        }
        setIsInitialLoading(false);
      } catch (error) {
        console.error('Failed to fetch airport data:', error);
        setIsInitialLoading(false);
      }
    };

  const fetchGates = async (code: string, terminal: string) => {
    try {
      const response = await fetch(`${API_URL}/api/airports/${code}/terminals/${encodeURIComponent(terminal)}/gates`);
      const data = await response.json();
      setGates(data.gates);
      if (data.gates.length > 0 && !selectedGate) {
        setSelectedGate(data.gates[0].name);
      }
    } catch (error) {
      console.error('Failed to fetch gates:', error);
    }
  };

  const getUserLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser');
      return;
    }

    setLocationError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const loc = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        };
        setUserLocation(loc);
        setMapCenter([loc.lat, loc.lng]);
        setMapZoom(17);
      },
      (error) => {
        setLocationError(`Unable to get location: ${error.message}`);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  };

  const calculateJourney = async () => {
    if (!selectedAirportCode || !selectedTerminal || !selectedGate) return;

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/journey/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          airport_code: selectedAirportCode,
          terminal: selectedTerminal,
          gate: selectedGate,
          has_tsa_precheck: hasTsaPrecheck,
          has_checked_bags: hasCheckedBags,
          mobility_factor: mobilityFactor,
          user_lat: userLocation?.lat,
          user_lng: userLocation?.lng,
        }),
      });
      const data = await response.json();
      setJourneyPlan(data);
    } catch (error) {
      console.error('Failed to calculate journey:', error);
    }
    setLoading(false);
  };

  const reportWaitTime = async () => {
    if (!reportCheckpoint || !reportedWaitTime) return;

    try {
      await fetch(`${API_URL}/api/wait-times/report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          airport_code: selectedAirportCode,
          checkpoint_id: reportCheckpoint.id,
          reported_wait_minutes: parseInt(reportedWaitTime),
          user_lat: userLocation?.lat,
          user_lng: userLocation?.lng,
        }),
      });
      setReportDialogOpen(false);
      setReportedWaitTime('');
      fetchAirportData(selectedAirportCode);
    } catch (error) {
      console.error('Failed to report wait time:', error);
    }
  };

  const calculateWillIMakeIt = async () => {
    if (!selectedAirportCode || !selectedTerminal || !selectedGate || !departureTime) return;

    setCalculatingProbability(true);
    setWillIMakeIt(null);
    try {
      const isoTime = new Date(departureTime).toISOString();
      const response = await fetch(`${API_URL}/api/will-i-make-it`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          flight: {
            airport_code: selectedAirportCode,
            terminal: selectedTerminal,
            gate: selectedGate,
            departure_time: isoTime,
          },
          has_tsa_precheck: hasTsaPrecheck,
          has_checked_bags: hasCheckedBags,
          mobility_factor: mobilityFactor,
          user_lat: userLocation?.lat,
          user_lng: userLocation?.lng,
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error('API error:', errorData);
        return;
      }
      const data = await response.json();
      setWillIMakeIt(data);
    } catch (error) {
      console.error('Failed to calculate probability:', error);
    }
    setCalculatingProbability(false);
  };

  const getProbabilityColor = (probability: number): string => {
    if (probability >= 0.95) return '#22c55e'; // green
    if (probability >= 0.80) return '#84cc16'; // lime
    if (probability >= 0.60) return '#eab308'; // yellow
    if (probability >= 0.40) return '#f97316'; // orange
    return '#ef4444'; // red
  };

  const getProbabilityBgClass = (status: string): string => {
    switch (status) {
      case 'safe': return 'from-green-600/20 to-green-500/10 border-green-500/30';
      case 'good': return 'from-lime-600/20 to-lime-500/10 border-lime-500/30';
      case 'risky': return 'from-yellow-600/20 to-yellow-500/10 border-yellow-500/30';
      case 'unlikely': return 'from-orange-600/20 to-orange-500/10 border-orange-500/30';
      case 'very_unlikely': return 'from-red-600/20 to-red-500/10 border-red-500/30';
      default: return 'from-blue-600/20 to-purple-600/20 border-blue-500/30';
    }
  };

  const getWaitTimeColor = (minutes: number): string => {
    if (minutes <= 10) return '#22c55e';
    if (minutes <= 20) return '#eab308';
    if (minutes <= 35) return '#f97316';
    return '#ef4444';
  };

  const getWaitTimeBadgeVariant = (minutes: number): "default" | "secondary" | "destructive" | "outline" => {
    if (minutes <= 10) return 'default';
    if (minutes <= 25) return 'secondary';
    return 'destructive';
  };

  const getCheckpointIcon = (type: string) => {
    switch (type) {
      case 'tsa':
      case 'tsa_precheck':
        return <Shield className="w-4 h-4" />;
      case 'bag_check':
        return <Luggage className="w-4 h-4" />;
      case 'passport_control':
        return <Globe className="w-4 h-4" />;
      default:
        return <MapPin className="w-4 h-4" />;
    }
  };

    // Early return for loading state
    if (isInitialLoading) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
          <div className="text-center">
            <div className="bg-blue-500 p-4 rounded-full inline-block mb-4">
              <Plane className="w-12 h-12 text-white animate-pulse" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">AirportWaze</h1>
            <p className="text-slate-400">Loading airport data...</p>
          </div>
        </div>
      );
    }

    const terminalCheckpoints = airportData?.checkpoints.filter(
      cp => cp.terminal === selectedTerminal
    ) || [];
    
    console.log('Debug - raw checkpoints stringified:', JSON.stringify(terminalCheckpoints));
    console.log('Debug - first checkpoint keys:', terminalCheckpoints[0] ? Object.keys(terminalCheckpoints[0]) : 'none');
    console.log('Debug - first checkpoint lat/lng:', terminalCheckpoints[0]?.lat, terminalCheckpoints[0]?.lng);

    const journeyPath: [number, number][] = journeyPlan?.steps.map(step => [step.lat, step.lng]) || [];
    if (userLocation && journeyPath.length > 0) {
      journeyPath.unshift([userLocation.lat, userLocation.lng]);
    }

    const selectedGateData = gates.find(g => g.name === selectedGate);

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-blue-500 p-2 rounded-lg">
                <Plane className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">AirportWaze</h1>
                <p className="text-xs text-slate-400">Real-time airport navigation with GPS</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={getUserLocation}
                className="text-slate-300 border-slate-600 hover:bg-slate-700"
              >
                <Locate className="w-4 h-4 mr-2" />
                {userLocation ? 'Update Location' : 'Get My Location'}
              </Button>
              <Badge variant="outline" className="text-green-400 border-green-400">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                Live Data
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Navigation className="w-5 h-5 text-blue-400" />
                      Live Airport Map
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      Real GPS coordinates - tap checkpoints for details
                    </CardDescription>
                  </div>
                  <Select value={selectedAirportCode} onValueChange={(value) => {
                    setSelectedAirportCode(value);
                    setSelectedTerminal('');
                    setSelectedGate('');
                    setJourneyPlan(null);
                  }}>
                    <SelectTrigger className="w-48 bg-slate-700 border-slate-600 text-white">
                      <SelectValue placeholder="Select airport" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600">
                      {airports.map((airport) => (
                        <SelectItem key={airport.code} value={airport.code} className="text-white hover:bg-slate-600">
                          {airport.code} - {airport.city}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardHeader>
              <CardContent>
                {locationError && (
                  <div className="mb-3 p-2 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">
                    {locationError}
                  </div>
                )}
                {userLocation && (
                  <div className="mb-3 p-2 bg-purple-900/30 border border-purple-700 rounded text-purple-300 text-sm flex items-center gap-2">
                    <Locate className="w-4 h-4" />
                    Your location: {userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}
                  </div>
                )}

                <div className="rounded-lg overflow-hidden border border-slate-600" style={{ height: '450px' }}>
                  <MapContainer
                    key={`${selectedAirportCode}-${selectedTerminal}`}
                    center={mapCenter}
                    zoom={mapZoom}
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom={true}
                  >
                    <MapController center={mapCenter} zoom={mapZoom} />
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />

                    {/* Test marker with hardcoded coordinates */}
                    <Marker position={[40.6413, -73.7781]} icon={createCheckpointIcon(15, 'tsa')}>
                      <Popup>
                        <div className="text-center">
                          <strong>Test Marker</strong>
                        </div>
                      </Popup>
                    </Marker>

                    {userLocation && (
                      <>
                        <Marker position={[userLocation.lat, userLocation.lng]} icon={createUserIcon()}>
                          <Popup>
                            <div className="text-center">
                              <strong>Your Location</strong>
                              <br />
                              <small>{userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}</small>
                            </div>
                          </Popup>
                        </Marker>
                        <Circle
                          center={[userLocation.lat, userLocation.lng]}
                          radius={30}
                          pathOptions={{ color: '#8b5cf6', fillColor: '#8b5cf6', fillOpacity: 0.2 }}
                        />
                      </>
                    )}

                    {terminalCheckpoints.map((checkpoint) => (
                      <Marker
                        key={checkpoint.id}
                        position={[checkpoint.lat || 40.6413, checkpoint.lng || -73.7781]}
                        icon={createCheckpointIcon(checkpoint.current_wait_minutes, checkpoint.type)}
                        eventHandlers={{
                          click: () => {
                            setReportCheckpoint(checkpoint);
                            setReportDialogOpen(true);
                          },
                        }}
                      >
                        <Popup>
                          <div className="text-center min-w-32">
                            <strong>{checkpoint.name}</strong>
                            <br />
                            <span style={{ color: getWaitTimeColor(checkpoint.current_wait_minutes) }}>
                              {checkpoint.current_wait_minutes} min wait
                            </span>
                            <br />
                            <small className="text-gray-500">Avg: {checkpoint.historical_avg_minutes} min</small>
                            <br />
                            <small className="text-gray-400">
                              {checkpoint.lat?.toFixed(5) ?? 'N/A'}, {checkpoint.lng?.toFixed(5) ?? 'N/A'}
                            </small>
                          </div>
                        </Popup>
                      </Marker>
                    ))}

                    {selectedGateData && selectedGateData.lat != null && selectedGateData.lng != null && (
                      <Marker
                        position={[selectedGateData.lat, selectedGateData.lng]}
                        icon={createGateIcon()}
                      >
                        <Popup>
                          <div className="text-center">
                            <strong>Gate {selectedGateData.name}</strong>
                            <br />
                            <small>{selectedGateData.lat?.toFixed(5) ?? 'N/A'}, {selectedGateData.lng?.toFixed(5) ?? 'N/A'}</small>
                          </div>
                        </Popup>
                      </Marker>
                    )}

                    {journeyPath.length > 1 && (
                      <Polyline
                        positions={journeyPath}
                        pathOptions={{ color: '#3b82f6', weight: 4, dashArray: '10, 10' }}
                      />
                    )}
                  </MapContainer>
                </div>

                <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <span>&lt;10m</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                      <span>10-20m</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                      <span>20-35m</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <span>&gt;35m</span>
                    </div>
                  </div>
                  <span>Tap markers for details</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-400" />
                  Current Wait Times - {selectedTerminal || 'Select Terminal'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {airportData && (
                  <div className="mb-4">
                    <Label className="text-slate-300 text-sm">Terminal</Label>
                    <Select value={selectedTerminal} onValueChange={(value) => {
                      setSelectedTerminal(value);
                      setSelectedGate('');
                      setJourneyPlan(null);
                    }}>
                      <SelectTrigger className="bg-slate-700 border-slate-600 text-white mt-1">
                        <SelectValue placeholder="Select terminal" />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-700 border-slate-600">
                        {airportData.terminals.map((terminal) => (
                          <SelectItem key={terminal} value={terminal} className="text-white hover:bg-slate-600">
                            {terminal}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {terminalCheckpoints.map((checkpoint) => (
                    <div
                      key={checkpoint.id}
                      className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-blue-500/50 transition-all cursor-pointer"
                      onClick={() => {
                        setReportCheckpoint(checkpoint);
                        setReportDialogOpen(true);
                      }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <div className="p-2 rounded-lg bg-slate-600">
                            {getCheckpointIcon(checkpoint.type)}
                          </div>
                          <div>
                            <p className="text-white font-medium text-sm">{checkpoint.name}</p>
                            <p className="text-slate-400 text-xs capitalize">{checkpoint.type.replace('_', ' ')}</p>
                          </div>
                        </div>
                        <Badge variant={getWaitTimeBadgeVariant(checkpoint.current_wait_minutes)}>
                          {checkpoint.current_wait_minutes} min
                        </Badge>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs">
                        <span className="text-slate-400">
                          Avg: {checkpoint.historical_avg_minutes} min
                        </span>
                        <span className="text-slate-500">
                          Click to report
                        </span>
                      </div>
                      <div className="mt-2 h-1.5 bg-slate-600 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${Math.min(100, (checkpoint.current_wait_minutes / 60) * 100)}%`,
                            backgroundColor: getWaitTimeColor(checkpoint.current_wait_minutes)
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-white flex items-center gap-2">
                  <Plane className="w-5 h-5 text-blue-400" />
                  Will I Make It?
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Enter your flight details to calculate your probability
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-slate-300 text-sm">Flight Departure Time</Label>
                  <Input
                    type="datetime-local"
                    value={departureTime}
                    onChange={(e) => setDepartureTime(e.target.value)}
                    className="bg-slate-700 border-slate-600 text-white mt-1"
                  />
                </div>

                <div>
                  <Label className="text-slate-300 text-sm">Gate</Label>
                  <Select value={selectedGate} onValueChange={setSelectedGate}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white mt-1">
                      <SelectValue placeholder="Select gate" />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-700 border-slate-600 max-h-48">
                      {gates.map((gate) => (
                        <SelectItem key={gate.name} value={gate.name} className="text-white hover:bg-slate-600">
                          Gate {gate.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-slate-400" />
                    <Label className="text-slate-300">TSA PreCheck</Label>
                  </div>
                  <Switch checked={hasTsaPrecheck} onCheckedChange={setHasTsaPrecheck} />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Luggage className="w-4 h-4 text-slate-400" />
                    <Label className="text-slate-300">Checked Bags</Label>
                  </div>
                  <Switch checked={hasCheckedBags} onCheckedChange={setHasCheckedBags} />
                </div>

                <div>
                  <Label className="text-slate-300 text-sm">Walking Speed</Label>
                  <div className="flex items-center gap-3 mt-2">
                    <Slider
                      value={[mobilityFactor]}
                      onValueChange={(v) => setMobilityFactor(v[0])}
                      min={0.5}
                      max={2}
                      step={0.1}
                      className="flex-1"
                    />
                    <span className="text-slate-400 text-sm w-16">
                      {mobilityFactor <= 0.7 ? 'Fast' : mobilityFactor >= 1.3 ? 'Slow' : 'Normal'}
                    </span>
                  </div>
                </div>

                <Button
                  onClick={calculateWillIMakeIt}
                  disabled={calculatingProbability || !selectedTerminal || !selectedGate || !departureTime}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                >
                  {calculatingProbability ? 'Calculating Probability...' : 'Will I Make It?'}
                </Button>
              </CardContent>
            </Card>

            {willIMakeIt && (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Clock className="w-5 h-5" style={{ color: getProbabilityColor(willIMakeIt.probability_of_making_it) }} />
                    Your Probability
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`bg-gradient-to-r ${getProbabilityBgClass(willIMakeIt.status)} rounded-lg p-4 mb-4 border`}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-slate-400 text-sm">Chance of Making Flight</p>
                      <Badge 
                        variant={willIMakeIt.probability_percentage >= 80 ? 'default' : willIMakeIt.probability_percentage >= 60 ? 'secondary' : 'destructive'}
                      >
                        {willIMakeIt.status.replace('_', ' ').toUpperCase()}
                      </Badge>
                    </div>
                    <p 
                      className="text-5xl font-bold"
                      style={{ color: getProbabilityColor(willIMakeIt.probability_of_making_it) }}
                    >
                      {willIMakeIt.probability_percentage}%
                    </p>
                    <p className="text-slate-300 text-sm mt-2">{willIMakeIt.status_message}</p>
                    <p className="text-slate-500 text-xs mt-2">
                      Based on {willIMakeIt.simulation_runs.toLocaleString()} Monte Carlo simulations
                    </p>
                  </div>

                  <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
                    <p className="text-slate-400 text-sm mb-3">Time Until Boarding Closes</p>
                    <p className="text-2xl font-bold text-white">{willIMakeIt.time_until_boarding} minutes</p>
                    <p className="text-slate-500 text-xs mt-1">
                      Boarding closes {willIMakeIt.boarding_cutoff_minutes} min before departure
                    </p>
                  </div>

                  <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
                    <p className="text-slate-400 text-sm mb-3">Estimated Journey Time (with confidence)</p>
                    <div className="grid grid-cols-4 gap-2 text-center">
                      <div>
                        <p className="text-lg font-bold text-white">{willIMakeIt.total_time_p50}m</p>
                        <p className="text-slate-500 text-xs">50%</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-yellow-400">{willIMakeIt.total_time_p80}m</p>
                        <p className="text-slate-500 text-xs">80%</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-orange-400">{willIMakeIt.total_time_p90}m</p>
                        <p className="text-slate-500 text-xs">90%</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold text-red-400">{willIMakeIt.total_time_p95}m</p>
                        <p className="text-slate-500 text-xs">95%</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
                    <p className="text-slate-400 text-sm mb-3">Leave By (for confidence level)</p>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">80% confidence</span>
                        <span className="text-yellow-400 font-mono">
                          {new Date(willIMakeIt.leave_by_80).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">90% confidence</span>
                        <span className="text-orange-400 font-mono">
                          {new Date(willIMakeIt.leave_by_90).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">95% confidence</span>
                        <span className="text-red-400 font-mono">
                          {new Date(willIMakeIt.leave_by_95).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <p className="text-slate-400 text-sm">Journey Breakdown</p>
                    {willIMakeIt.segments.map((segment, index) => (
                      <div key={index} className="flex gap-3">
                        <div className="flex flex-col items-center">
                          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                            {index + 1}
                          </div>
                          {index < willIMakeIt.segments.length - 1 && (
                            <div className="w-0.5 h-full bg-slate-600 my-1"></div>
                          )}
                        </div>
                        <div className="flex-1 pb-3">
                          <p className="text-white font-medium">{segment.step_name}</p>
                          <p className="text-slate-400 text-sm">{segment.location}</p>
                          <div className="flex gap-4 mt-1 text-xs flex-wrap">
                            <span className="text-slate-500">Walk: {segment.walk_minutes} min</span>
                            {segment.wait_distribution && (
                              <span className="text-orange-400">
                                Wait: {segment.wait_distribution.p50}-{segment.wait_distribution.p90} min (90%)
                              </span>
                            )}
                            <span className="text-slate-600">{segment.walk_distance_meters}m</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-white flex items-center gap-2">
                  <Route className="w-5 h-5 text-blue-400" />
                  Quick Journey Estimate
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Get a quick estimate without flight details
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={calculateJourney}
                  disabled={loading || !selectedTerminal || !selectedGate}
                  className="w-full bg-slate-600 hover:bg-slate-500"
                >
                  {loading ? 'Calculating...' : 'Calculate Journey Time'}
                </Button>
              </CardContent>
            </Card>

            {journeyPlan && (
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader className="pb-3">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Clock className="w-5 h-5 text-green-400" />
                    Your Journey Plan
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-4 mb-4 border border-blue-500/30">
                    <p className="text-slate-400 text-sm">Recommended Arrival</p>
                    <p className="text-3xl font-bold text-white">
                      {new Date(journeyPlan.recommended_arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    <p className="text-slate-400 text-sm mt-1">
                      Total: {journeyPlan.total_time_minutes} min + {journeyPlan.buffer_minutes} min buffer
                    </p>
                    <p className="text-slate-500 text-xs mt-1">
                      Distance: {(journeyPlan.total_distance_meters / 1000).toFixed(2)} km
                    </p>
                  </div>

                  <div className="space-y-3">
                    {journeyPlan.steps.map((step, index) => (
                      <div key={index} className="flex gap-3">
                        <div className="flex flex-col items-center">
                          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                            {index + 1}
                          </div>
                          {index < journeyPlan.steps.length - 1 && (
                            <div className="w-0.5 h-full bg-slate-600 my-1"></div>
                          )}
                        </div>
                        <div className="flex-1 pb-3">
                          <p className="text-white font-medium">{step.step_name}</p>
                          <p className="text-slate-400 text-sm">{step.location}</p>
                          <div className="flex gap-4 mt-1 text-xs">
                            <span className="text-slate-500">Walk: {step.estimated_walk_minutes} min</span>
                            {step.estimated_wait_minutes > 0 && (
                              <span className="text-orange-400">Wait: {step.estimated_wait_minutes} min</span>
                            )}
                            <span className="text-slate-600">{step.distance_meters}m</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="pb-3">
                <CardTitle className="text-white flex items-center gap-2">
                  <Send className="w-5 h-5 text-blue-400" />
                  Help Others
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Report wait times you experience
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-slate-400 text-sm">
                  Click on any checkpoint on the map or in the list to report the current wait time you're experiencing.
                </p>
                <div className="mt-3 p-3 bg-slate-700/50 rounded-lg border border-slate-600">
                  <p className="text-slate-300 text-sm flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-blue-400" />
                    Your reports help improve accuracy for everyone
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Report Wait Time</DialogTitle>
          </DialogHeader>
          {reportCheckpoint && (
            <div className="space-y-4">
              <div>
                <p className="text-slate-300 font-medium">{reportCheckpoint.name}</p>
                <p className="text-slate-400 text-sm capitalize">{reportCheckpoint.type.replace('_', ' ')}</p>
                <p className="text-slate-500 text-xs mt-1">
                  Location: {reportCheckpoint.lat?.toFixed(5) ?? 'N/A'}, {reportCheckpoint.lng?.toFixed(5) ?? 'N/A'}
                </p>
              </div>
              <div>
                <Label className="text-slate-300">Current wait time (minutes)</Label>
                <Input
                  type="number"
                  value={reportedWaitTime}
                  onChange={(e) => setReportedWaitTime(e.target.value)}
                  placeholder="Enter wait time in minutes"
                  className="bg-slate-700 border-slate-600 text-white mt-1"
                />
              </div>
              <Button onClick={reportWaitTime} className="w-full bg-blue-600 hover:bg-blue-700">
                Submit Report
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;
