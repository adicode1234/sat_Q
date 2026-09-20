import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  IconGlobe,
  IconMapPin,
  IconEye,
  IconEyeOff,
  IconPlus,
  IconMinus,
  IconSearch,
  IconCompass,
  IconLayersIntersect,
  IconCrosshair,
  IconInfoCircle,
  IconX,
  IconCheck,
  IconSatellite,
  IconMap2,
  IconArrowRight,
  IconSparkles,
  IconSun,
  IconSunHigh,
  IconPlanet,
  IconRocket,
  IconCopy
} from '@tabler/icons-react';

export interface GeoBounds {
  west: number;
  south: number;
  east: number;
  north: number;
  center?: { lat: number; lng: number };
  location_name?: string;
}

export interface HudCalloutItem {
  id: string;
  title: string;
  subtitle: string;
  color: string;
  icon: string;
  filterType: string;
  tx: number;
  ty: number;
  bx: number;
  by: number;
}

export interface LocationDetails {
  title: string;
  region?: string;
  country?: string;
  category: string;
  categoryIcon: string;
  lat: number;
  lng: number;
  extract: string;
  thumbnail?: string;
  satelliteSensors?: string;
  resolution?: string;
  isLoading?: boolean;
}

interface CesiumGlobeViewerProps {
  imageSrc: string;
  geoBounds?: GeoBounds | null;
  callouts?: HudCalloutItem[];
  activeFilter?: string;
  onFilterChange?: (filter: string) => void;
  showOverlay?: boolean;
  onToggleOverlay?: () => void;
  isProcessing?: boolean;
  sceneName?: string;
  modalityBadge?: string;
  onSwitchTo2D?: () => void;
  onLocationChange?: (bounds: GeoBounds) => void;
  targetLocationQuery?: string;
  uploadedFileName?: string;
  onAnalyzeLocation?: (locationName: string, coords?: { lat: number; lng: number }) => void;
}

// Built-in offline geocode directory for instant responsive fly-to
const PRESET_LOCATIONS: Record<string, { lat: number; lng: number; name: string; bounds: GeoBounds }> = {
  // Top Metros & Requested Hotspots
  kolkata: {
    lat: 22.5726, lng: 88.3639,
    name: 'Kolkata & Hooghly River Basin (West Bengal)',
    bounds: { west: 88.25, south: 22.45, east: 88.48, north: 22.68 }
  },
  calcutta: {
    lat: 22.5726, lng: 88.3639,
    name: 'Kolkata & Hooghly River Basin (West Bengal)',
    bounds: { west: 88.25, south: 22.45, east: 88.48, north: 22.68 }
  },
  howrah: {
    lat: 22.5958, lng: 88.2636,
    name: 'Howrah & Hooghly Riverfront (West Bengal)',
    bounds: { west: 88.20, south: 22.52, east: 88.33, north: 22.66 }
  },
  delhi: {
    lat: 28.6139, lng: 77.2090,
    name: 'New Delhi (National Capital Region, Yamuna)',
    bounds: { west: 77.10, south: 28.50, east: 77.35, north: 28.75 }
  },
  newdelhi: {
    lat: 28.6139, lng: 77.2090,
    name: 'New Delhi (National Capital Region, Yamuna)',
    bounds: { west: 77.10, south: 28.50, east: 77.35, north: 28.75 }
  },
  surat: {
    lat: 21.1800, lng: 72.8300,
    name: 'Tapi River Basin & Surat Estuary (Gujarat)',
    bounds: { west: 72.76, south: 21.12, east: 72.90, north: 21.24 }
  },
  mumbai: {
    lat: 19.0760, lng: 72.8777,
    name: 'Mumbai Urban Coastal Bay (Maharashtra)',
    bounds: { west: 72.75, south: 18.88, east: 72.98, north: 19.25 }
  },
  bombay: {
    lat: 19.0760, lng: 72.8777,
    name: 'Mumbai Urban Coastal Bay (Maharashtra)',
    bounds: { west: 72.75, south: 18.88, east: 72.98, north: 19.25 }
  },
  bengaluru: {
    lat: 12.9716, lng: 77.5946,
    name: 'Bengaluru Tech & Space Corridor (Karnataka)',
    bounds: { west: 77.50, south: 12.85, east: 77.72, north: 13.08 }
  },
  bangalore: {
    lat: 12.9716, lng: 77.5946,
    name: 'Bengaluru Tech & Space Corridor (Karnataka)',
    bounds: { west: 77.50, south: 12.85, east: 77.72, north: 13.08 }
  },
  chennai: {
    lat: 13.0827, lng: 80.2707,
    name: 'Chennai Coastal Bay & Marina (Tamil Nadu)',
    bounds: { west: 80.18, south: 12.98, east: 80.32, north: 13.18 }
  },
  madras: {
    lat: 13.0827, lng: 80.2707,
    name: 'Chennai Coastal Bay & Marina (Tamil Nadu)',
    bounds: { west: 80.18, south: 12.98, east: 80.32, north: 13.18 }
  },
  hyderabad: {
    lat: 17.3850, lng: 78.4867,
    name: 'Hyderabad & Musi Basin (Telangana)',
    bounds: { west: 78.35, south: 17.28, east: 78.58, north: 17.48 }
  },
  ahmedabad: {
    lat: 23.0225, lng: 72.5714,
    name: 'Ahmedabad Sabarmati Riverfront (Gujarat)',
    bounds: { west: 72.48, south: 22.95, east: 72.68, north: 23.12 }
  },
  jaipur: {
    lat: 26.9124, lng: 75.7873,
    name: 'Jaipur Pink City & Aravalli Basin (Rajasthan)',
    bounds: { west: 75.70, south: 26.82, east: 75.88, north: 27.02 }
  },
  pune: {
    lat: 18.5204, lng: 73.8567,
    name: 'Pune Mula-Mutha River Valley (Maharashtra)',
    bounds: { west: 73.76, south: 18.42, east: 73.96, north: 18.62 }
  },
  lucknow: {
    lat: 26.8467, lng: 80.9462,
    name: 'Lucknow Gomti River Corridor (Uttar Pradesh)',
    bounds: { west: 80.85, south: 26.75, east: 81.05, north: 26.95 }
  },
  varanasi: {
    lat: 25.3176, lng: 82.9739,
    name: 'Varanasi Ganga Ghats Basin (Uttar Pradesh)',
    bounds: { west: 82.90, south: 25.25, east: 83.05, north: 25.38 }
  },
  patna: {
    lat: 25.6093, lng: 85.1376,
    name: 'Patna Ganga River Basin (Bihar)',
    bounds: { west: 85.05, south: 25.54, east: 85.22, north: 25.68 }
  },
  bhopal: {
    lat: 23.2599, lng: 77.4126,
    name: 'Bhopal Upper Lake & Urban Zone (Madhya Pradesh)',
    bounds: { west: 77.33, south: 23.18, east: 77.49, north: 23.34 }
  },
  indore: {
    lat: 22.7196, lng: 75.8577,
    name: 'Indore Urban Region (Madhya Pradesh)',
    bounds: { west: 75.78, south: 22.65, east: 75.94, north: 22.79 }
  },
  chandigarh: {
    lat: 30.7333, lng: 76.7794,
    name: 'Chandigarh Capital Region (Punjab/Haryana)',
    bounds: { west: 76.70, south: 30.68, east: 76.86, north: 30.80 }
  },
  bhubaneswar: {
    lat: 20.2961, lng: 85.8245,
    name: 'Bhubaneswar Smart City (Odisha)',
    bounds: { west: 85.74, south: 20.22, east: 85.90, north: 20.37 }
  },
  guwahati: {
    lat: 26.1445, lng: 91.7362,
    name: 'Guwahati Brahmaputra Valley (Assam)',
    bounds: { west: 91.64, south: 26.08, east: 91.84, north: 26.22 }
  },
  nagpur: {
    lat: 21.1458, lng: 79.0882,
    name: 'Nagpur Zero Mile City (Maharashtra)',
    bounds: { west: 79.00, south: 21.08, east: 79.18, north: 21.22 }
  },
  kanpur: {
    lat: 26.4499, lng: 80.3319,
    name: 'Kanpur Ganga River Basin (Uttar Pradesh)',
    bounds: { west: 80.25, south: 26.38, east: 80.42, north: 26.52 }
  },
  agra: {
    lat: 27.1767, lng: 78.0081,
    name: 'Agra Yamuna River Corridor (Uttar Pradesh)',
    bounds: { west: 77.92, south: 27.10, east: 78.10, north: 27.24 }
  },
  amritsar: {
    lat: 31.6340, lng: 74.8723,
    name: 'Amritsar Golden City (Punjab)',
    bounds: { west: 74.80, south: 31.57, east: 74.95, north: 31.70 }
  },
  srinagar: {
    lat: 34.0837, lng: 74.7973,
    name: 'Srinagar Dal Lake & Jhelum Valley (Kashmir)',
    bounds: { west: 74.72, south: 34.02, east: 74.88, north: 34.15 }
  },
  visakhapatnam: {
    lat: 17.6868, lng: 83.2185,
    name: 'Visakhapatnam Coastal Port (Andhra Pradesh)',
    bounds: { west: 17.62, south: 83.12, east: 17.76, north: 83.30 }
  },
  vadodara: {
    lat: 22.3072, lng: 73.1812,
    name: 'Vadodara Vishwamitri River (Gujarat)',
    bounds: { west: 73.10, south: 22.24, east: 73.26, north: 22.38 }
  },
  ranchi: {
    lat: 23.3441, lng: 85.3096,
    name: 'Ranchi Subarnarekha Basin (Jharkhand)',
    bounds: { west: 85.22, south: 23.27, east: 85.40, north: 23.42 }
  },
  raipur: {
    lat: 21.2514, lng: 81.6296,
    name: 'Raipur Mahanadi Basin (Chhattisgarh)',
    bounds: { west: 81.54, south: 21.18, east: 81.72, north: 21.32 }
  },
  dehradun: {
    lat: 30.3165, lng: 78.0322,
    name: 'Dehradun Doon Valley (Uttarakhand)',
    bounds: { west: 77.95, south: 30.25, east: 78.12, north: 30.38 }
  },
  shimla: {
    lat: 31.1048, lng: 77.1734,
    name: 'Shimla Ridge & Himalayan Slopes (Himachal Pradesh)',
    bounds: { west: 77.12, south: 31.06, east: 77.24, north: 31.15 }
  },
  // Strategic & Natural Sites
  sundarbans: {
    lat: 21.9497, lng: 89.1833,
    name: 'Sundarbans Mangrove Delta & Tidal Forest',
    bounds: { west: 88.80, south: 21.60, east: 89.60, north: 22.30 }
  },
  thar: {
    lat: 26.9157, lng: 70.9083,
    name: 'Thar Desert Radar Calibration Field (Jaisalmer)',
    bounds: { west: 70.70, south: 26.70, east: 71.20, north: 27.20 }
  },
  ladakh: {
    lat: 34.1526, lng: 77.5771,
    name: 'Leh Ladakh High-Altitude Plateau (Himalayas)',
    bounds: { west: 77.45, south: 34.05, east: 77.70, north: 34.25 }
  },
  leh: {
    lat: 34.1526, lng: 77.5771,
    name: 'Leh Ladakh High-Altitude Plateau (Himalayas)',
    bounds: { west: 77.45, south: 34.05, east: 77.70, north: 34.25 }
  },
  goa: {
    lat: 15.2993, lng: 74.1240,
    name: 'Goa Coastal Estuaries & Mandovi River',
    bounds: { west: 73.70, south: 15.10, east: 74.25, north: 15.55 }
  },
  kerala: {
    lat: 9.9312, lng: 76.2673,
    name: 'Kochi & Vembanad Backwaters (Kerala)',
    bounds: { west: 76.15, south: 9.80, east: 76.38, north: 10.05 }
  },
  kochi: {
    lat: 9.9312, lng: 76.2673,
    name: 'Kochi & Vembanad Backwaters (Kerala)',
    bounds: { west: 76.15, south: 9.80, east: 76.38, north: 10.05 }
  },
  hassan: {
    lat: 13.1009, lng: 76.3955,
    name: 'ISRO Master Control Facility (Hassan, Karnataka)',
    bounds: { west: 76.36, south: 13.07, east: 76.43, north: 13.13 }
  },
  sriharikota: {
    lat: 13.7199, lng: 80.2305,
    name: 'Satish Dhawan Space Centre (Sriharikota, AP)',
    bounds: { west: 80.18, south: 13.67, east: 80.28, north: 13.77 }
  },
  // Global Landmarks & Metros
  ghana: {
    lat: 9.3137, lng: -1.4488,
    name: 'Volta Lake Basin (Ghana, West Africa)',
    bounds: { west: -1.48, south: 9.28, east: -1.41, north: 9.35 }
  },
  cairo: {
    lat: 29.9792, lng: 31.1342,
    name: 'Giza Plateau & Nile River Valley (Egypt)',
    bounds: { west: 31.05, south: 29.90, east: 31.25, north: 30.10 }
  },
  dubai: {
    lat: 25.2048, lng: 55.2708,
    name: 'Dubai Palm & Coastal Gulf (UAE)',
    bounds: { west: 55.15, south: 25.05, east: 55.38, north: 25.30 }
  },
  london: {
    lat: 51.5074, lng: -0.1278,
    name: 'London Thames River Basin (UK)',
    bounds: { west: -0.25, south: 51.40, east: 0.05, north: 51.60 }
  },
  paris: {
    lat: 48.8566, lng: 2.3522,
    name: 'Paris Seine River Basin (France)',
    bounds: { west: 2.22, south: 48.78, east: 2.45, north: 48.95 }
  },
  newyork: {
    lat: 40.7128, lng: -74.0060,
    name: 'New York Harbor & Hudson Estuary (USA)',
    bounds: { west: -74.15, south: 40.60, east: -73.85, north: 40.85 }
  },
  tokyo: {
    lat: 35.6762, lng: 139.6503,
    name: 'Tokyo Bay Urban Coastal Zone (Japan)',
    bounds: { west: 139.55, south: 35.55, east: 139.85, north: 35.80 }
  },
  singapore: {
    lat: 1.3521, lng: 103.8198,
    name: 'Singapore Island & Marina Bay',
    bounds: { west: 103.65, south: 1.22, east: 103.98, north: 1.48 }
  },
  sydney: {
    lat: -33.8688, lng: 151.2093,
    name: 'Sydney Port Jackson Harbor (Australia)',
    bounds: { west: 151.10, south: -33.95, east: 151.30, north: -33.78 }
  },
  everest: {
    lat: 27.9881, lng: 86.9250,
    name: 'Mount Everest Peak & Khumbu Glacier (Himalayas)',
    bounds: { west: 86.85, south: 27.92, east: 87.00, north: 28.05 }
  }
};

// Detect marine/oceanic basin when coordinates fall outside landmass reverse geocoding
const identifyMarineRegion = (lat: number, lng: number): { name: string; category: string; description: string } => {
  if (lat >= 5 && lat <= 24 && lng >= 78 && lng <= 96) {
    return {
      name: 'Bay of Bengal (North Indian Ocean)',
      category: 'Marine & Oceanic Basin',
      description: 'The Bay of Bengal is the northeastern part of the Indian Ocean, bounded by India, Bangladesh, and Myanmar. It receives massive discharge from the Ganges-Brahmaputra and Mahanadi river networks, observed by multi-spectral optical and radar satellites.'
    };
  }
  if (lat >= 8 && lat <= 26 && lng >= 55 && lng <= 77) {
    return {
      name: 'Arabian Sea (Northwestern Indian Ocean)',
      category: 'Marine & Oceanic Basin',
      description: 'The Arabian Sea is a region of the northern Indian Ocean bounded to the north by Pakistan and Iran, to the west by the Gulf of Oman, and to the east by India. Monsoonal upwelling and maritime lanes are continuously imaged via Sentinel SAR backscatter.'
    };
  }
  if (lat >= -50 && lat < 8 && lng >= 30 && lng <= 115) {
    return {
      name: 'Indian Ocean Open Waters',
      category: 'Deep Marine Basin',
      description: 'The Indian Ocean is the third-largest of the world\'s five oceanic divisions. It encompasses critical global shipping lanes and equatorial circulation patterns monitored via spaceborne radar altimetry.'
    };
  }
  if (lat >= 30 && lat <= 46 && lng >= -6 && lng <= 37) {
    return {
      name: 'Mediterranean Sea Basin',
      category: 'Enclosed Marine Basin',
      description: 'The Mediterranean Sea is an intercontinental sea connected to the Atlantic Ocean, surrounded by southern Europe, northern Africa, and the Levant.'
    };
  }
  if (lat >= 23 && lat <= 31 && lng >= 48 && lng <= 57) {
    return {
      name: 'Persian Gulf (Arabian Gulf)',
      category: 'Marine Estuary & Gulf',
      description: 'The Persian Gulf is a shallow Mediterranean sea in Western Asia, an extension of the Indian Ocean through the Strait of Hormuz, with high satellite surveillance of coastal energy infrastructure.'
    };
  }
  if (lat >= 12 && lat <= 30 && lng >= 32 && lng <= 44) {
    return {
      name: 'Red Sea Coastal Basin',
      category: 'Marine Rift Basin',
      description: 'The Red Sea is a seawater inlet of the Indian Ocean between Africa and Asia, featuring hypersaline currents and diverse reef systems visible from high-resolution optical bands.'
    };
  }
  if (lat >= 0 && lat <= 45 && lng >= 100 && lng <= 160) {
    return {
      name: 'Western Pacific Ocean & South China Sea',
      category: 'Pelagic Oceanic Basin',
      description: 'The Western Pacific Ocean features marginal seas, active maritime shipping corridors, and tropical archipelagos covered by high-frequency Sentinel SAR and optical constellations.'
    };
  }
  if (lat > 66) {
    return {
      name: 'Arctic Oceanic Ice Zone',
      category: 'Cryospheric Polar Basin',
      description: 'High-latitude polar marine basin dominated by pack-ice dynamics, mapped via dual-polarization Sentinel-1 radar backscatter for ice shelf tracking and climate monitoring.'
    };
  }
  if (lat < -60) {
    return {
      name: 'Southern Ocean & Antarctic Ice Zone',
      category: 'Cryospheric Polar Basin',
      description: 'Circumpolar Antarctic waters and ice shelves monitored through microwave SAR and radar altimetry passes.'
    };
  }
  if (lng < -20 && lng > -100) {
    return {
      name: 'Atlantic Ocean Marine Waters',
      category: 'Pelagic Oceanic Basin',
      description: 'The Atlantic Ocean is the second-largest of the world\'s oceans. Continuous earth observation monitoring tracks oceanic circulation, weather fronts, and surface roughness.'
    };
  }
  return {
    name: 'Open Oceanic Water Body',
    category: 'Marine & Oceanic Basin',
    description: 'International open oceanic expanse with active satellite altimetry coverage and global Sentinel SAR vessel & surface roughness detection passes.'
  };
};

export const CesiumGlobeViewer: React.FC<CesiumGlobeViewerProps> = ({
  imageSrc,
  geoBounds,
  callouts = [],
  activeFilter = 'all',
  onFilterChange,
  showOverlay = true,
  onToggleOverlay,
  isProcessing = false,
  sceneName = 'Satellite Scene Footprint',
  modalityBadge = 'Optical (RGB)',
  onSwitchTo2D,
  onLocationChange,
  targetLocationQuery,
  uploadedFileName,
  onAnalyzeLocation
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasFallbackRef = useRef<HTMLCanvasElement | null>(null);
  const cesiumViewerRef = useRef<any>(null);
  const [isCesiumReady, setIsCesiumReady] = useState(false);
  const [baseMapType, setBaseMapType] = useState<'satellite' | 'street'>('satellite');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [selectedCallout, setSelectedCallout] = useState<HudCalloutItem | null>(null);
  const [is3DAngled, setIs3DAngled] = useState(false);
  const [sunLighting, setSunLighting] = useState(true);
  const [isSunAnimating, setIsSunAnimating] = useState(false);
  const [locationInfo, setLocationInfo] = useState<LocationDetails | null>(null);
  const [copiedCoords, setCopiedCoords] = useState(false);

  // Check if query or image filename mentions any preset location
  const combinedQueryOrFile = `${targetLocationQuery || ''} ${uploadedFileName || ''} ${sceneName || ''}`.toLowerCase();
  const queryResolvedLoc = combinedQueryOrFile
    ? PRESET_LOCATIONS[
        Object.keys(PRESET_LOCATIONS).find(
          (k) => k === combinedQueryOrFile || combinedQueryOrFile.includes(k)
        ) || ''
      ]
    : null;

  // Maintain active currentBounds state - default to Kolkata if not specified
  const [currentBounds, setCurrentBounds] = useState<GeoBounds>(() => {
    if (geoBounds && geoBounds.center) return geoBounds;
    if (queryResolvedLoc) return queryResolvedLoc.bounds;
    return PRESET_LOCATIONS.kolkata.bounds;
  });

  const [currentLocationName, setCurrentLocationName] = useState<string>(
    geoBounds?.location_name || (queryResolvedLoc ? queryResolvedLoc.name : PRESET_LOCATIONS.kolkata.name)
  );
  const [currentCoords, setCurrentCoords] = useState<{ lat: number; lng: number }>({
    lat: geoBounds?.center?.lat ?? (queryResolvedLoc ? queryResolvedLoc.lat : PRESET_LOCATIONS.kolkata.lat),
    lng: geoBounds?.center?.lng ?? (queryResolvedLoc ? queryResolvedLoc.lng : PRESET_LOCATIONS.kolkata.lng)
  });

  // Sync Cesium solar clock to shine sunlight on the target coordinates
  const syncSunTime = useCallback((lng: number) => {
    const viewer = cesiumViewerRef.current;
    const Cesium = (window as any).Cesium;
    if (!viewer?.clock || !Cesium) return;
    try {
      const d = new Date();
      let solarUtcHour = 12 - lng / 15.0;
      while (solarUtcHour < 0) solarUtcHour += 24;
      while (solarUtcHour >= 24) solarUtcHour -= 24;
      d.setUTCHours(Math.floor(solarUtcHour), Math.floor((solarUtcHour % 1) * 60), 0, 0);
      viewer.clock.currentTime = Cesium.JulianDate.fromDate(d);
    } catch (_) {}
  }, []);

  // 2. Camera Flight Function - Centers directly over (lng, lat) looking nadir
  const flyTo = useCallback((lat: number, lng: number, bounds?: GeoBounds, tiltDeg?: number) => {
    setCurrentCoords({ lat, lng });
    syncSunTime(lng);
    const Cesium = (window as any).Cesium;
    const viewer = cesiumViewerRef.current;

    if (viewer && Cesium) {
      const latSpan = bounds ? Math.abs(bounds.north - bounds.south) : 0.08;
      const lngSpan = bounds ? Math.abs(bounds.east - bounds.west) : 0.08;
      const maxSpan = Math.max(latSpan, lngSpan, 0.04);
      // Clean high-detail city/scene zoom altitude (~8,000 to 25,000 meters)
      const targetAltitude = Math.min(Math.max(maxSpan * 65000, 7500), 450000);

      // Default: -90 degrees pitch = NADIR (looking straight down onto city center)
      const pitchValue = typeof tiltDeg === 'number' ? tiltDeg : (is3DAngled ? -55 : -90);

      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lng, lat, targetAltitude),
        orientation: {
          heading: Cesium.Math.toRadians(0), // Heading 0 = True North UP
          pitch: Cesium.Math.toRadians(pitchValue), // Straight down (nadir)
          roll: 0.0
        },
        duration: 1.8
      });
    }
  }, [is3DAngled, syncSunTime]);

  // Universal Jump & Relocate function
  const jumpToLocation = useCallback((lat: number, lng: number, name: string, customBounds?: GeoBounds) => {
    const span = 0.05;
    const b: GeoBounds = customBounds || {
      west: lng - span,
      south: lat - span,
      east: lng + span,
      north: lat + span,
      center: { lat, lng },
      location_name: name
    };
    setCurrentBounds(b);
    setCurrentCoords({ lat, lng });
    setCurrentLocationName(name);
    flyTo(lat, lng, b, -90);
    setSearchMessage(`🎯 Centered on: ${name} (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`);
    if (onLocationChange) {
      onLocationChange(b);
    }
  }, [flyTo, onLocationChange]);

  // 🎯 Select any location on Earth: Reverse geocodes, identifies waterbody/city/terrain, fetches Wikipedia & satellite metadata
  const selectLocationByCoordinates = useCallback(
    async (lat: number, lng: number, shouldZoomIn = false, directTitle?: string) => {
      setCurrentCoords({ lat, lng });
      syncSunTime(lng);

      const span = 0.05;
      const b: GeoBounds = {
        west: lng - span,
        south: lat - span,
        east: lng + span,
        north: lat + span,
        center: { lat, lng },
        location_name: directTitle || `${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`
      };
      setCurrentBounds(b);
      if (directTitle) {
        setCurrentLocationName(directTitle);
      }
      if (onLocationChange) {
        onLocationChange(b);
      }

      // Smooth camera pan or fly in closer
      const viewer = cesiumViewerRef.current;
      const Cesium = (window as any).Cesium;
      if (viewer && Cesium) {
        if (shouldZoomIn) {
          flyTo(lat, lng, b, -90);
        } else {
          const currentHeight = viewer.camera.positionCartographic?.height || 220000;
          const targetHeight = Math.min(Math.max(currentHeight * 0.85, 25000), 750000);
          viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(lng, lat, targetHeight),
            orientation: {
              heading: Cesium.Math.toRadians(0),
              pitch: viewer.camera.pitch || Cesium.Math.toRadians(-90),
              roll: 0.0
            },
            duration: 1.2
          });
        }
      }

      // Immediate visual feedback in info HUD
      setLocationInfo({
        title: directTitle || `Scanning Coordinates...`,
        category: 'Orbital Reconnaissance',
        categoryIcon: '🛰️',
        lat,
        lng,
        extract: `Acquiring Sentinel-2 multispectral & SAR radar backscatter telemetry for (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)...`,
        satelliteSensors: 'Sentinel-2 MSI (10m) · Sentinel-1 SAR C-Band',
        resolution: '10.0m Spatial GSD',
        isLoading: true
      });

      setSearchMessage(`🛰️ Selected target: ${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E — Geodata load ho raha hai...`);

      // 1. Perform Reverse Geocode via OSM Nominatim
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 4500);
        const res = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat.toFixed(5)}&lon=${lng.toFixed(5)}&zoom=14&addressdetails=1`,
          { signal: controller.signal }
        );
        clearTimeout(timeoutId);
        const data = await res.json();

        if (data && (data.address || data.display_name)) {
          const addr = data.address || {};
          const detectedCity =
            directTitle ||
            addr.city ||
            addr.town ||
            addr.village ||
            addr.municipality ||
            addr.suburb ||
            addr.county ||
            addr.state_district ||
            data.name ||
            'Regional Terrain';
          const detectedState = addr.state || addr.province || addr.region || '';
          const detectedCountry = addr.country || '';

          // Determine category & icon
          let category = 'Geographic Terrain';
          let categoryIcon = '🗺️';
          const combinedStr = `${data.type || ''} ${data.class || ''} ${addr.water || ''} ${addr.natural || ''}`.toLowerCase();

          if (
            combinedStr.includes('water') ||
            combinedStr.includes('bay') ||
            combinedStr.includes('river') ||
            combinedStr.includes('lake') ||
            combinedStr.includes('ocean') ||
            combinedStr.includes('sea')
          ) {
            category = 'Hydrological Water Basin';
            categoryIcon = '🌊';
          } else if (
            addr.city ||
            addr.town ||
            addr.suburb ||
            combinedStr.includes('place') ||
            combinedStr.includes('building') ||
            combinedStr.includes('residential')
          ) {
            category = 'Urban Settlement & Built-Up Grid';
            categoryIcon = '🏙️';
          } else if (
            combinedStr.includes('wood') ||
            combinedStr.includes('forest') ||
            combinedStr.includes('park')
          ) {
            category = 'Forest & Protected Vegetation';
            categoryIcon = '🌲';
          } else if (combinedStr.includes('farm') || combinedStr.includes('orchard')) {
            category = 'Agricultural Land & Crops';
            categoryIcon = '🌾';
          } else if (addr.state || addr.country) {
            category = 'Administrative Region';
            categoryIcon = '📍';
          }

          const resolvedName = directTitle || (detectedState ? `${detectedCity}, ${detectedState}` : detectedCity);
          setCurrentLocationName(resolvedName);

          // 2. Enrich with Wikipedia summary
          let wikiData: any = null;
          try {
            const wikiSearchTerm = directTitle || detectedCity;
            const wikiRes = await fetch(
              `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(wikiSearchTerm.split(',')[0].trim())}`
            );
            if (wikiRes.ok) {
              wikiData = await wikiRes.json();
            }
          } catch (_) {}

          setLocationInfo({
            title: directTitle || wikiData?.title || detectedCity,
            region: detectedState,
            country: detectedCountry,
            category,
            categoryIcon,
            lat,
            lng,
            extract:
              wikiData?.extract ||
              `${detectedCity} is situated in ${detectedState ? detectedState + ', ' : ''}${detectedCountry}. This georeferenced sector (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E) is monitored by active multi-spectral optical and C-band SAR satellite constellations.`,
            thumbnail: wikiData?.thumbnail?.source,
            satelliteSensors: 'Sentinel-2 MSI (Optical) · Sentinel-1 SAR (Radar)',
            resolution: '10.0m GSD · Multi-Spectral bands B2, B3, B4, B8, B11',
            isLoading: false
          });

          setSearchMessage(`🎯 Target Locked: ${detectedCity} (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`);
          return;
        }
      } catch (err) {
        console.warn('Reverse geocode note:', err);
      }

      // 3. Fallback for Ocean / Marine / Remote International Expanses
      const marine = identifyMarineRegion(lat, lng);
      setCurrentLocationName(marine.name);

      let wikiMarine: any = null;
      try {
        const wRes = await fetch(
          `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(marine.name.split('(')[0].trim())}`
        );
        if (wRes.ok) {
          wikiMarine = await wRes.json();
        }
      } catch (_) {}

      setLocationInfo({
        title: wikiMarine?.title || marine.name,
        region: 'International Waters',
        country: 'Global Maritime Basin',
        category: marine.category,
        categoryIcon: '⚓',
        lat,
        lng,
        extract: wikiMarine?.extract || marine.description,
        thumbnail: wikiMarine?.thumbnail?.source,
        satelliteSensors: 'Sentinel-1 SAR C-Band (VV+VH) · Sentinel-3 Ocean Altimetry',
        resolution: '10m SAR Backscatter · Radar Wave/Roughness Imaging',
        isLoading: false
      });

      setSearchMessage(`🌊 Marine Target: ${marine.name} (${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E)`);
    },
    [flyTo, onLocationChange, syncSunTime]
  );

  // Ref to always provide latest selector to Cesium & canvas click handlers without re-binding
  const selectLocationRef = useRef(selectLocationByCoordinates);
  useEffect(() => {
    selectLocationRef.current = selectLocationByCoordinates;
  });

  // ☀️ Toggle photorealistic Sun & solar lighting with shadows
  const toggleSunLighting = () => {
    const next = !sunLighting;
    setSunLighting(next);
    const viewer = cesiumViewerRef.current;
    if (viewer?.scene?.globe) {
      viewer.scene.globe.enableLighting = next;
      viewer.scene.globe.showGroundAtmosphere = true;
      if (viewer.scene.sun) viewer.scene.sun.show = next;
      if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = true;
    }
    setSearchMessage(
      next
        ? '☀️ Suraj & Solar Lighting ON: Realistic Sun rays, atmosphere haze & day/night shadows active!'
        : '💡 Uniform GIS Lighting ON (Shadows off)'
    );
  };

  // ⏳ Animate continuous Sun rotation (day-night cycle)
  const toggleSunAnimation = () => {
    const viewer = cesiumViewerRef.current;
    if (!viewer?.clock) return;
    const next = !isSunAnimating;
    setIsSunAnimating(next);
    viewer.clock.shouldAnimate = next;
    viewer.clock.multiplier = next ? 3600 : 1; // 1 hour per second = smooth sunrise/sunset
    setSearchMessage(
      next
        ? '⏳ Day-Night Cycle Rotating: Suraj chal raha hai (Earth pe sunrise & sunset live dikhega)!'
        : '⏸️ Sun rotation paused'
    );
  };

  // 🌍 Space Earth Orbit View (Full globe in cosmos with Sun, Stars & Atmosphere)
  const flyToSpaceOrbit = () => {
    const viewer = cesiumViewerRef.current;
    const Cesium = (window as any).Cesium;
    if (!viewer || !Cesium) return;

    syncSunTime(currentCoords.lng);

    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(currentCoords.lng - 22, currentCoords.lat - 6, 23000000),
      orientation: {
        heading: Cesium.Math.toRadians(18),
        pitch: Cesium.Math.toRadians(-70),
        roll: 0.0
      },
      duration: 2.4
    });
    setSearchMessage('🌍 Space Earth View: Pura Earth floating in cosmos with glowing Sun, atmosphere & stars!');
  };

  // 1. Initialize Cesium with reliable ESRI satellite & OSM imagery (no API key needed!)
  useEffect(() => {
    let viewer: any = null;
    let isMounted = true;

    const initCesium = () => {
      const Cesium = (window as any).Cesium;
      if (!Cesium || !containerRef.current) return false;

      try {
        try {
          Cesium.Ion.defaultAccessToken = '';
        } catch (_) {}

        let baseLayer: any = undefined;
        try {
          const esriProvider = new Cesium.UrlTemplateImageryProvider({
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            maximumLevel: 19,
            credit: 'Esri, Maxar, Earthstar Geographics'
          });
          baseLayer = new Cesium.ImageryLayer(esriProvider, {
            brightness: 1.05,
            contrast: 1.08,
            saturation: 1.05
          });
        } catch (layerErr) {
          console.warn('ESRI imagery provider setup error:', layerErr);
        }

        viewer = new Cesium.Viewer(containerRef.current, {
          animation: false,
          baseLayerPicker: false,
          fullscreenButton: false,
          geocoder: false,
          homeButton: false,
          infoBox: false,
          sceneModePicker: false,
          selectionIndicator: false,
          timeline: false,
          navigationHelpButton: false,
          scene3DOnly: true,
          shadows: true,
          skyBox: new Cesium.SkyBox({ show: true }),
          skyAtmosphere: new Cesium.SkyAtmosphere(),
          baseLayer: baseLayer
        });

        // High-definition crisp canvas rendering
        try {
          viewer.resolutionScale = Math.min(window.devicePixelRatio || 1, 2.0);
          viewer.scene.postProcessStages.fxaa.enabled = true;
          viewer.scene.globe.maximumScreenSpaceError = 1.33; // Higher detail tile loading
        } catch (_) {}

        if (baseLayer && viewer.imageryLayers.length === 0) {
          viewer.imageryLayers.add(baseLayer);
        }

        if (viewer.bottomContainer) {
          viewer.bottomContainer.style.display = 'none';
        }

        // ── Photorealistic Celestial Environment: Sun, Stars, Earth Atmosphere ──
        try {
          viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#020612');
          viewer.scene.globe.enableLighting = true;
          viewer.scene.globe.dynamicAtmosphereLighting = true;
          viewer.scene.globe.dynamicAtmosphereLightingFromSun = true;
          viewer.scene.globe.showGroundAtmosphere = true;
          viewer.scene.globe.nightImageWaterMask = true;
          viewer.scene.globe.depthTestAgainstTerrain = false;

          // Real Sun in outer space with bright solar glare
          if (!viewer.scene.sun) viewer.scene.sun = new Cesium.Sun();
          viewer.scene.sun.show = true;
          try {
            viewer.scene.sunBloom = true;
          } catch (_) {}

          // Moon
          if (!viewer.scene.moon) viewer.scene.moon = new Cesium.Moon();
          viewer.scene.moon.show = true;

          // Sky Atmosphere: Earth rim glow & atmospheric scattering haze
          if (!viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere = new Cesium.SkyAtmosphere();
          viewer.scene.skyAtmosphere.show = true;
          try {
            viewer.scene.skyAtmosphere.brightnessShift = 0.15;
            viewer.scene.skyAtmosphere.saturationShift = 0.18;
          } catch (_) {}

          // Skybox: Stars and deep space cosmos
          if (viewer.scene.skyBox) {
            viewer.scene.skyBox.show = true;
          }

          // Position Sun to shine sunlight on target coordinates
          syncSunTime(currentCoords.lng);
        } catch (envErr) {
          console.warn('Cesium atmospheric celestial setup notice:', envErr);
        }

        // ScreenSpaceEventHandler: Click anywhere on Earth to inspect, and double click to fly in
        let handler: any = null;
        try {
          handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

          // Single click: Select coordinate and open location information panel
          handler.setInputAction((movement: any) => {
            const cartesian = viewer.camera.pickEllipsoid(movement.position, viewer.scene.globe.ellipsoid);
            if (cartesian) {
              const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
              const lng = Cesium.Math.toDegrees(cartographic.longitude);
              const lat = Cesium.Math.toDegrees(cartographic.latitude);
              if (selectLocationRef.current) {
                selectLocationRef.current(lat, lng, false);
              }
            }
          }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

          // Double click: Select coordinate, open info panel AND fly in close (nadir zoom)
          handler.setInputAction((movement: any) => {
            const cartesian = viewer.camera.pickEllipsoid(movement.position, viewer.scene.globe.ellipsoid);
            if (cartesian) {
              const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
              const lng = Cesium.Math.toDegrees(cartographic.longitude);
              const lat = Cesium.Math.toDegrees(cartographic.latitude);
              if (selectLocationRef.current) {
                selectLocationRef.current(lat, lng, true);
              }
            }
          }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
        } catch (hErr) {
          console.warn('ScreenSpaceEventHandler setup notice:', hErr);
        }

        cesiumViewerRef.current = viewer;
        if (isMounted) {
          setIsCesiumReady(true);
          setTimeout(() => {
            flyTo(currentCoords.lat, currentCoords.lng, currentBounds, -90);
          }, 350);
        }
        return true;
      } catch (err) {
        console.warn('Cesium initialization notice (using 3D canvas fallback):', err);
        return false;
      }
    };

    if (!initCesium()) {
      const interval = setInterval(() => {
        if (initCesium()) {
          clearInterval(interval);
        }
      }, 500);
      const timeout = setTimeout(() => clearInterval(interval), 6000);
      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
        isMounted = false;
        if (viewer && !viewer.isDestroyed()) {
          viewer.destroy();
        }
      };
    }

    return () => {
      isMounted = false;
      if (viewer && !viewer.isDestroyed()) {
        viewer.destroy();
      }
    };
  }, []);

  const toggleBaseMap = (type: 'satellite' | 'street') => {
    setBaseMapType(type);
    const viewer = cesiumViewerRef.current;
    const Cesium = (window as any).Cesium;
    if (!viewer || !Cesium) return;

    try {
      viewer.imageryLayers.removeAll();
      const url =
        type === 'street'
          ? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
          : 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

      const provider = new Cesium.UrlTemplateImageryProvider({ url, maximumLevel: 19 });
      viewer.imageryLayers.add(new Cesium.ImageryLayer(provider));
    } catch (e) {
      console.warn('Base map switch error:', e);
    }
  };

  // 3. Render Georeferenced Footprint & 3D Feature Pins in Cesium
  useEffect(() => {
    const viewer = cesiumViewerRef.current;
    const Cesium = (window as any).Cesium;
    if (!viewer || !Cesium || !isCesiumReady) return;

    try {
      viewer.entities.removeAll();

      const b = currentBounds;
      const rect = Cesium.Rectangle.fromDegrees(b.west, b.south, b.east, b.north);
      const cLat = (b.south + b.north) / 2;
      const cLng = (b.west + b.east) / 2;

      // If we have location info (user clicked or searched a place), draw highlighted boundary box + pinpoint marker
      if (locationInfo) {
        viewer.entities.add({
          name: 'Searched Region',
          rectangle: {
            coordinates: rect,
            material: Cesium.Color.fromCssColorString('#00f0ff').withAlpha(0.12),
            height: 15,
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString('#00f0ff').withAlpha(0.85),
            outlineWidth: 3
          },
          position: Cesium.Cartesian3.fromDegrees(cLng, cLat, 50),
          label: {
            text: `${locationInfo.categoryIcon || '📍'} ${locationInfo.title.toUpperCase()}`,
            font: 'bold 14px sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 4,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -12),
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        });

        // Exact glowing pinpoint marker at clicked coordinates
        viewer.entities.add({
          name: 'Selected Pinpoint',
          position: Cesium.Cartesian3.fromDegrees(locationInfo.lng, locationInfo.lat, 25),
          point: {
            pixelSize: 12,
            color: Cesium.Color.fromCssColorString('#00f0ff'),
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2.5,
            disableDepthTestDistance: Number.POSITIVE_INFINITY
          }
        });
      } else {
        // Only add a very subtle, transparent boundary outline if desired, but we remove the draped image and center label
        // so the 3D view stays completely clean and photorealistic.
        viewer.entities.add({
          name: 'Footprint Extent',
          rectangle: {
            coordinates: rect,
            material: Cesium.Color.TRANSPARENT,
            height: 12,
            outline: true,
            outlineColor: Cesium.Color.fromCssColorString('#00f0ff').withAlpha(0.3),
            outlineWidth: 2
          }
        });
      }

      // Add AI Land-Cover Points only if explicit and discreet (compact single-line badge or dots)
      if (showOverlay && callouts.length > 0 && activeFilter !== 'none') {
        callouts.forEach((item) => {
          const isMatched = activeFilter === 'all' || activeFilter === item.filterType;
          if (!isMatched) return;

          const pLng = b.west + (item.tx / 1000) * (b.east - b.west);
          const pLat = b.north - (item.ty / 1000) * (b.north - b.south);

          viewer.entities.add({
            name: item.title,
            position: Cesium.Cartesian3.fromDegrees(pLng, pLat, 30),
            point: {
              pixelSize: 10,
              color: Cesium.Color.fromCssColorString(item.color),
              outlineColor: Cesium.Color.WHITE,
              outlineWidth: 2
            },
            // If activeFilter is specifically selected, show small label; otherwise keep map clean!
            label: activeFilter !== 'all' ? {
              text: `${item.icon} ${item.title}`,
              font: '600 11px sans-serif',
              fillColor: Cesium.Color.WHITE,
              outlineColor: Cesium.Color.BLACK,
              outlineWidth: 2,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
              pixelOffset: new Cesium.Cartesian2(0, -12),
              disableDepthTestDistance: Number.POSITIVE_INFINITY
            } : undefined
          });
        });
      }
    } catch (e) {
      console.warn('Error updating Cesium entities:', e);
    }
  }, [isCesiumReady, imageSrc, currentBounds, callouts, activeFilter, showOverlay, sceneName, currentLocationName, locationInfo]);

  // 4. Interactive 3D Canvas Fallback Globe
  useEffect(() => {
    if (isCesiumReady) return;
    const canvas = canvasFallbackRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let rotation = (currentCoords.lng * Math.PI) / 180;
    let targetRotation = rotation;
    let isDragging = false;
    let startX = 0;
    let startY = 0;
    let hasDragged = false;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      hasDragged = false;
      startX = e.clientX;
      startY = e.clientY;
    };
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
        hasDragged = true;
      }
      startX = e.clientX;
      startY = e.clientY;
      targetRotation += dx * 0.008;
    };
    const onMouseUp = (e: MouseEvent) => {
      if (isDragging && !hasDragged && canvas) {
        const rect = canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const R = Math.min(canvas.width, canvas.height) * 0.38;
        const dx = clickX - cx;
        const dy = clickY - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist <= R) {
          const lat = Math.asin(-dy / R) * (180 / Math.PI);
          const rawLng = ((rotation * 180) / Math.PI + Math.asin(dx / R) * (180 / Math.PI));
          const lng = ((rawLng + 180) % 360 + 360) % 360 - 180;
          if (selectLocationRef.current) {
            selectLocationRef.current(lat, lng, false);
          }
        }
      }
      isDragging = false;
    };

    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);

    const render = () => {
      rotation += (targetRotation - rotation) * 0.1;
      const w = canvas.width;
      const h = canvas.height;
      const cx = w / 2;
      const cy = h / 2;
      const R = Math.min(w, h) * 0.38;

      ctx.clearRect(0, 0, w, h);

      // Deep outer space with cosmic stars
      ctx.fillStyle = '#010308';
      ctx.fillRect(0, 0, w, h);

      // Glittering starfield
      ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
      for (let s = 0; s < 75; s++) {
        const sx = (s * 139.7) % w;
        const sy = (s * 277.3) % h;
        const sSize = s % 4 === 0 ? 1.8 : 1;
        ctx.fillRect(sx, sy, sSize, sSize);
      }

      // Blazing Sun in deep space (Top-Left)
      const sunX = w * 0.16;
      const sunY = h * 0.16;
      const sunFlare = ctx.createRadialGradient(sunX, sunY, 6, sunX, sunY, 110);
      sunFlare.addColorStop(0, 'rgba(255, 255, 250, 1)');
      sunFlare.addColorStop(0.12, 'rgba(255, 230, 130, 0.95)');
      sunFlare.addColorStop(0.3, 'rgba(255, 170, 50, 0.4)');
      sunFlare.addColorStop(0.7, 'rgba(255, 100, 20, 0.1)');
      sunFlare.addColorStop(1, 'rgba(255, 80, 0, 0)');
      ctx.fillStyle = sunFlare;
      ctx.beginPath();
      ctx.arc(sunX, sunY, 110, 0, Math.PI * 2);
      ctx.fill();

      // Sun core
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(sunX, sunY, 10, 0, Math.PI * 2);
      ctx.fill();

      const gradGlow = ctx.createRadialGradient(cx, cy, R * 0.9, cx, cy, R * 1.35);
      gradGlow.addColorStop(0, 'rgba(0, 180, 255, 0.45)');
      gradGlow.addColorStop(0.5, 'rgba(0, 100, 200, 0.18)');
      gradGlow.addColorStop(1, 'rgba(0, 30, 80, 0)');
      ctx.fillStyle = gradGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, R * 1.35, 0, Math.PI * 2);
      ctx.fill();

      const gradEarth = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R);
      gradEarth.addColorStop(0, '#103960');
      gradEarth.addColorStop(0.7, '#071f38');
      gradEarth.addColorStop(1, '#020d1c');
      ctx.fillStyle = gradEarth;
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.fill();
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = '#00f0ff';
      ctx.stroke();

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.clip();

      ctx.strokeStyle = 'rgba(56, 189, 248, 0.22)';
      ctx.lineWidth = 1;

      for (let lat = -60; lat <= 60; lat += 30) {
        const y = cy - Math.sin((lat * Math.PI) / 180) * R;
        const radLat = Math.cos((lat * Math.PI) / 180) * R;
        ctx.beginPath();
        ctx.ellipse(cx, y, radLat, radLat * 0.22, 0, 0, Math.PI * 2);
        ctx.stroke();
      }

      for (let lon = 0; lon < 360; lon += 45) {
        const angle = (lon * Math.PI) / 180 + rotation;
        const xOffset = Math.sin(angle) * R;
        if (Math.cos(angle) > 0) {
          ctx.beginPath();
          ctx.ellipse(cx + xOffset * 0.5, cy, Math.abs(xOffset) * 0.5, R, 0, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      const targetAngle = (currentCoords.lng * Math.PI) / 180 + rotation;
      const isVisible = Math.cos(targetAngle) > 0;

      if (isVisible) {
        const px = cx + Math.sin(targetAngle) * Math.cos((currentCoords.lat * Math.PI) / 180) * R;
        const py = cy - Math.sin((currentCoords.lat * Math.PI) / 180) * R;

        const pingR = 14 + (Date.now() % 1500) / 75;
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.arc(px, py, pingR, 0, Math.PI * 2);
        ctx.stroke();

        ctx.fillStyle = '#ff9a42';
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = 'rgba(0, 240, 255, 0.25)';
        ctx.strokeStyle = '#00f0ff';
        ctx.lineWidth = 2;
        ctx.strokeRect(px - 28, py - 20, 56, 40);
        ctx.fillRect(px - 28, py - 20, 56, 40);

        ctx.fillStyle = 'rgba(2, 14, 30, 0.85)';
        ctx.fillRect(px + 14, py - 28, 140, 32);
        ctx.strokeStyle = '#00f0ff';
        ctx.strokeRect(px + 14, py - 28, 140, 32);
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(currentLocationName.slice(0, 20), px + 20, py - 16);
        ctx.fillStyle = '#38bdf8';
        ctx.font = '9px monospace';
        ctx.fillText(`${currentCoords.lat.toFixed(2)}° N, ${currentCoords.lng.toFixed(2)}° E`, px + 20, py - 4);
      }

      ctx.restore();

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      canvas.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [isCesiumReady, currentCoords, currentLocationName]);

  // 5. Universal Place Search & Fly-To Handler
  const handleLocationSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const q = searchQuery.trim().toLowerCase();
    if (!q) return;

    setIsSearching(true);
    setSearchMessage(null);

    // 1) Match in local offline directory
    const matchedKey = Object.keys(PRESET_LOCATIONS).find(
      (k) => k === q || k.includes(q) || PRESET_LOCATIONS[k].name.toLowerCase().includes(q)
    );

    if (matchedKey) {
      const loc = PRESET_LOCATIONS[matchedKey];
      jumpToLocation(loc.lat, loc.lng, loc.name, loc.bounds);
      selectLocationByCoordinates(loc.lat, loc.lng, true, loc.name);
      setIsSearching(false);
      return;
    }

    // 2) Check if user entered numbers e.g. "22.57, 88.36" or "22.5726 88.3639"
    const cleanQ = q.replace(/[°NSEWnsew]/g, '').trim();
    const coordMatch = cleanQ.match(/^(-?\d+(\.\d+)?)[,\s]+(-?\d+(\.\d+)?)$/);
    if (coordMatch) {
      const lat = parseFloat(coordMatch[1]);
      const lng = parseFloat(coordMatch[3]);
      if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        selectLocationByCoordinates(lat, lng, true);
        setIsSearching(false);
        return;
      }
    }

    // 3) Query OpenStreetMap Nominatim for any arbitrary global place/landmark
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`)
      .then((r) => r.json())
      .then((data) => {
        if (data && data.length > 0) {
          const first = data[0];
          const lat = parseFloat(first.lat);
          const lng = parseFloat(first.lon);
          const bb = first.boundingbox;
          const bounds: GeoBounds =
            bb && bb.length >= 4
              ? {
                  south: parseFloat(bb[0]),
                  north: parseFloat(bb[1]),
                  west: parseFloat(bb[2]),
                  east: parseFloat(bb[3]),
                  center: { lat, lng }
                }
              : {
                  south: lat - 0.05,
                  north: lat + 0.05,
                  west: lng - 0.05,
                  east: lng + 0.05,
                  center: { lat, lng }
                };

          const placeName = first.display_name.split(',').slice(0, 3).join(', ');
          jumpToLocation(lat, lng, placeName, bounds);
          selectLocationByCoordinates(lat, lng, true, first.name || placeName);
        } else {
          setSearchMessage(`Location "${q}" not found. Try entering coordinates (e.g. 22.57, 88.36).`);
        }
      })
      .catch(() => {
        setSearchMessage('Network geocoder unreachable. Please enter coordinates or check connection.');
      })
      .finally(() => {
        setIsSearching(false);
      });
  };

  return (
    <div className="satt-cesium-wrapper">
      {/* ── Top Floating Location Search & Fly-To Navigation Bar ── */}
      <div className="satt-cesium-nav-bar">
        <div className="satt-cesium-nav-top-row">
          <form onSubmit={handleLocationSearch} className="satt-cesium-search-form">
            <div className="satt-cesium-search-input-wrap">
              <button
                type="submit"
                disabled={isSearching}
                style={{
                  background: 'transparent',
                  border: 'none',
                  padding: 0,
                  margin: 0,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#38bdf8'
                }}
                title="Search location"
              >
                {isSearching ? (
                  <IconGlobe size={15} className="animate-spin text-cyan-400" />
                ) : (
                  <IconSearch size={15} className="text-cyan-400 hover:text-cyan-300" />
                )}
              </button>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search global location or coordinates (e.g. Kolkata, Tokyo, 22.57, 88.36)..."
                className="satt-cesium-search-input"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="satt-search-clear-btn"
                  onClick={() => setSearchQuery('')}
                >
                  <IconX size={13} />
                </button>
              )}
            </div>
          </form>

          {/* Map Layer Switcher: Satellite vs Streets */}
          <div className="satt-cesium-layer-switch">
            <button
              type="button"
              className={`satt-layer-chip ${baseMapType === 'satellite' ? 'satt-layer-active' : ''}`}
              onClick={() => toggleBaseMap('satellite')}
              title="ESRI World Satellite Imagery"
            >
              <IconSatellite size={13} />
              <span>Satellite</span>
            </button>
            <button
              type="button"
              className={`satt-layer-chip ${baseMapType === 'street' ? 'satt-layer-active' : ''}`}
              onClick={() => toggleBaseMap('street')}
              title="OpenStreetMap Hybrid"
            >
              <IconMap2 size={13} />
              <span>Streets</span>
            </button>
          </div>
        </div>

        {searchMessage && (
          <div className="satt-cesium-search-feedback">
            <IconInfoCircle size={13} className="text-cyan-400" />
            <span>{searchMessage}</span>
          </div>
        )}
      </div>

      {/* ── 3D Viewport Stage: Cesium Globe or High-Fidelity Canvas Fallback ── */}
      <div className="satt-cesium-container">
        <div ref={containerRef} className="satt-cesium-globe-canvas" />

        {!isCesiumReady && (
          <div className="satt-cesium-fallback-wrap">
            <canvas
              ref={canvasFallbackRef}
              width={960}
              height={580}
              className="satt-globe-fallback-canvas"
            />
            <div className="satt-cesium-loading-badge">
              <IconGlobe size={16} className="text-cyan-400 animate-spin" />
              <span>3D Earth Globe Active · Rendering Planetary Surface</span>
            </div>
          </div>
        )}

        {/* Floating Right HUD Toolbar - Compact & Sleek */}
        <div className="satt-cesium-toolbar">
          {onSwitchTo2D && (
            <button
              type="button"
              className="satt-vp-btn"
              title="Switch to 2D High-Res Analysis View"
              onClick={onSwitchTo2D}
            >
              <IconLayersIntersect size={14} />
            </button>
          )}
          <button
            type="button"
            className="satt-vp-btn text-cyan-400"
            title="Center Camera Straight Down (Nadir View)"
            onClick={() => flyTo(currentCoords.lat, currentCoords.lng, currentBounds, -90)}
          >
            <IconCrosshair size={14} />
          </button>
          <button
            type="button"
            className={`satt-vp-btn ${is3DAngled ? 'satt-vp-btn-active text-cyan-400' : ''}`}
            title={is3DAngled ? "2D Top-Down View" : "3D Tilted View (-55°)"}
            onClick={() => {
              const next = !is3DAngled;
              setIs3DAngled(next);
              flyTo(currentCoords.lat, currentCoords.lng, currentBounds, next ? -55 : -90);
            }}
          >
            <IconGlobe size={14} />
          </button>
          <button
            type="button"
            className="satt-vp-btn text-amber-300"
            title="🌍 Space Earth View: View Full Earth from Cosmos"
            onClick={flyToSpaceOrbit}
          >
            <IconPlanet size={14} />
          </button>
          <button
            type="button"
            className={`satt-vp-btn ${sunLighting ? 'satt-vp-btn-active text-amber-400' : ''}`}
            title={sunLighting ? "☀️ Sun & Solar Day/Night Lighting ON (Click to toggle)" : "💡 Uniform GIS Lighting ON"}
            onClick={toggleSunLighting}
          >
            <IconSun size={14} />
          </button>
          <button
            type="button"
            className={`satt-vp-btn ${isSunAnimating ? 'satt-vp-btn-active text-amber-300 animate-pulse' : ''}`}
            title={isSunAnimating ? "Pause Sun Rotation" : "Rotate Day/Night Live"}
            onClick={toggleSunAnimation}
          >
            <IconSunHigh size={14} />
          </button>
          <div className="satt-vp-divider" />
          <button
            type="button"
            className="satt-vp-btn"
            title="Zoom In"
            onClick={() => {
              const viewer = cesiumViewerRef.current;
              if (viewer) viewer.camera.zoomIn(viewer.camera.positionCartographic.height * 0.4);
            }}
          >
            <IconPlus size={14} />
          </button>
          <button
            type="button"
            className="satt-vp-btn"
            title="Zoom Out"
            onClick={() => {
              const viewer = cesiumViewerRef.current;
              if (viewer) viewer.camera.zoomOut(viewer.camera.positionCartographic.height * 0.6);
            }}
          >
            <IconMinus size={14} />
          </button>
        </div>

        {/* Top Left Cockpit Coordinate Overlay */}
        <div className="satt-cesium-coords-hud">
          <div className="satt-coords-title-row">
            <IconMapPin size={13} className="text-cyan-400" />
            <span className="satt-coords-title">GEOREFERENCED FOOTPRINT</span>
          </div>
          <div className="satt-coords-name">{currentLocationName}</div>
          <div className="satt-coords-metrics">
            <span>LAT: {currentCoords.lat.toFixed(4)}° N</span>
            <span>LON: {currentCoords.lng.toFixed(4)}° E</span>
          </div>
          <div className="satt-coords-badge">
            <span>WGS84 EPSG:4326 · True Optical/SAR Projection</span>
          </div>
          <div className="satt-coords-hint">
            💡 Earth par kisi bhi jagah click karein to uska naam, details aur AI analysis card dikhega!
          </div>
        </div>

        {/* ── Rich Satellite & Geographic Location Information Card ── */}
        {locationInfo && (
          <div
            className="satt-location-info-hud"
            style={{
              position: 'absolute',
              bottom: '52px',
              left: '16px',
              width: '330px',
              maxWidth: 'calc(100vw - 32px)',
              background: 'rgba(2, 12, 26, 0.94)',
              border: '1px solid rgba(0, 240, 255, 0.4)',
              borderRadius: '10px',
              padding: '14px',
              color: '#ffffff',
              backdropFilter: 'blur(14px)',
              WebkitBackdropFilter: 'blur(14px)',
              zIndex: 120,
              boxShadow: '0 14px 40px rgba(0, 0, 0, 0.8), 0 0 24px rgba(0, 240, 255, 0.15)',
              animation: 'fadeIn 0.22s ease-out'
            }}
          >
            {/* Header: Category Icon, Classification Badge, and Close Button */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '15px' }}>{locationInfo.categoryIcon || '📍'}</span>
                <span
                  style={{
                    fontSize: '10px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.06em',
                    color: '#38bdf8',
                    background: 'rgba(56, 189, 248, 0.12)',
                    padding: '2px 7px',
                    borderRadius: '4px',
                    border: '1px solid rgba(56, 189, 248, 0.25)'
                  }}
                >
                  {locationInfo.category}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setLocationInfo(null)}
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  borderRadius: '4px',
                  padding: '3px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.15s ease'
                }}
                title="Card Band Karein"
              >
                <IconX size={14} />
              </button>
            </div>

            {/* Title & Region */}
            <div style={{ marginBottom: '8px' }}>
              <h3
                style={{
                  margin: 0,
                  fontSize: '15px',
                  fontWeight: 700,
                  color: '#ffffff',
                  lineHeight: '1.25',
                  letterSpacing: '-0.01em'
                }}
              >
                {locationInfo.title}
              </h3>
              {(locationInfo.region || locationInfo.country) && (
                <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '3px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <IconMapPin size={12} className="text-cyan-400 shrink-0" />
                  <span>
                    {[locationInfo.region, locationInfo.country].filter(Boolean).join(', ')}
                  </span>
                </div>
              )}
            </div>

            {/* Telemetry Coordinate Pill */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: 'rgba(0, 0, 0, 0.5)',
                padding: '6px 9px',
                borderRadius: '6px',
                fontSize: '10.5px',
                fontFamily: 'monospace',
                color: '#67e8f9',
                marginBottom: '10px',
                border: '1px solid rgba(0, 240, 255, 0.2)'
              }}
            >
              <span>{locationInfo.lat.toFixed(4)}° N, {locationInfo.lng.toFixed(4)}° E</span>
              <span style={{ color: '#94a3b8', fontSize: '9.5px' }}>WGS84 EPSG:4326</span>
            </div>

            {/* Thumbnail Image (if Wikipedia has one) */}
            {locationInfo.thumbnail && (
              <div
                style={{
                  width: '100%',
                  height: '115px',
                  overflow: 'hidden',
                  borderRadius: '6px',
                  marginBottom: '10px',
                  position: 'relative',
                  border: '1px solid rgba(255, 255, 255, 0.12)'
                }}
              >
                <img
                  src={locationInfo.thumbnail}
                  alt={locationInfo.title}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    height: '24px',
                    background: 'linear-gradient(to top, rgba(2, 12, 26, 0.9), transparent)'
                  }}
                />
              </div>
            )}

            {/* Satellite Sensor Specs */}
            <div
              style={{
                background: 'rgba(8, 25, 45, 0.55)',
                borderRadius: '6px',
                padding: '7px 9px',
                marginBottom: '10px',
                border: '1px solid rgba(0, 240, 255, 0.18)',
                fontSize: '10px',
                color: '#94a3b8'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#38bdf8', fontWeight: 600, marginBottom: '2px' }}>
                <IconSatellite size={12} />
                <span>ORBITAL SENSORS & RESOLUTION</span>
              </div>
              <div style={{ color: '#e2e8f0', fontSize: '10px' }}>
                {locationInfo.satelliteSensors || 'Sentinel-2 MSI (10m) · Sentinel-1 SAR C-Band'}
              </div>
            </div>

            {/* Description Text or Loading Spinner */}
            <div style={{ marginBottom: '12px' }}>
              {locationInfo.isLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8', fontSize: '11px', padding: '6px 0' }}>
                  <IconGlobe size={15} className="animate-spin text-cyan-400 shrink-0" />
                  <span>Orbit telemetry lock ho raha hai & geospatial details fetch ho rahi hain...</span>
                </div>
              ) : (
                <p
                  style={{
                    margin: 0,
                    fontSize: '11px',
                    color: '#cbd5e1',
                    lineHeight: '1.5',
                    maxHeight: '100px',
                    overflowY: 'auto',
                    paddingRight: '4px'
                  }}
                >
                  {locationInfo.extract}
                </p>
              )}
            </div>

            {/* ── Action Buttons ── */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {/* Primary AI Analysis Trigger */}
              {onAnalyzeLocation && (
                <button
                  type="button"
                  onClick={() => {
                    onAnalyzeLocation(locationInfo.title, { lat: locationInfo.lat, lng: locationInfo.lng });
                  }}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    border: 'none',
                    background: 'linear-gradient(135deg, #0284c7 0%, #00f0ff 100%)',
                    color: '#020b17',
                    fontWeight: 700,
                    fontSize: '11.5px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    cursor: 'pointer',
                    boxShadow: '0 2px 10px rgba(0, 240, 255, 0.35)',
                    transition: 'all 0.15s ease'
                  }}
                  title="Is jagah ka satellite optical/SAR AI analysis shuru karein"
                >
                  <IconRocket size={14} />
                  <span>Is Location Ka AI Analysis Karein</span>
                </button>
              )}

              {/* Secondary Row: Fly Closer & Copy Coords */}
              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  type="button"
                  onClick={() => {
                    flyTo(locationInfo.lat, locationInfo.lng, undefined, -90);
                  }}
                  style={{
                    flex: 1,
                    padding: '6px 10px',
                    borderRadius: '5px',
                    border: '1px solid rgba(0, 240, 255, 0.25)',
                    background: 'rgba(0, 240, 255, 0.08)',
                    color: '#38bdf8',
                    fontSize: '10.5px',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                    cursor: 'pointer'
                  }}
                  title="Zoom in nadir view"
                >
                  <IconCrosshair size={12} />
                  <span>Zoom In</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(`${locationInfo.lat.toFixed(5)}, ${locationInfo.lng.toFixed(5)}`);
                    setCopiedCoords(true);
                    setTimeout(() => setCopiedCoords(false), 2000);
                  }}
                  style={{
                    flex: 1,
                    padding: '6px 10px',
                    borderRadius: '5px',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    background: 'rgba(255, 255, 255, 0.05)',
                    color: copiedCoords ? '#4ade80' : '#e2e8f0',
                    fontSize: '10.5px',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '4px',
                    cursor: 'pointer'
                  }}
                  title="Coordinate copy karein"
                >
                  {copiedCoords ? <IconCheck size={12} className="text-emerald-400" /> : <IconCopy size={12} />}
                  <span>{copiedCoords ? 'Copied!' : 'Copy Coords'}</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Active 3D Callout Card Modal */}
        {selectedCallout && (
          <div className="satt-cesium-popup-card">
            <div className="satt-popup-header">
              <div className="satt-popup-title">
                <span>{selectedCallout.icon}</span>
                <strong>{selectedCallout.title}</strong>
              </div>
              <button
                type="button"
                className="satt-popup-close"
                onClick={() => setSelectedCallout(null)}
              >
                <IconX size={14} />
              </button>
            </div>
            <p className="satt-popup-sub">{selectedCallout.subtitle}</p>
            <div className="satt-popup-footer">
              <span className="satt-popup-tag" style={{ borderColor: selectedCallout.color }}>
                Class: {selectedCallout.filterType.toUpperCase()}
              </span>
              <span className="satt-popup-verified">
                <IconCheck size={12} className="text-emerald-400" /> Verified Feature
              </span>
            </div>
          </div>
        )}

        {/* Bottom Interactive Feature Filter Bar - Clean, Compact & Text Only */}
        <div className="satt-viewport-legend">
          <button
            type="button"
            className={`satt-legend-btn ${activeFilter === 'all' ? 'satt-legend-btn-active' : ''}`}
            onClick={() => onFilterChange && onFilterChange('all')}
            title="All detected features"
          >
            <span className="legend-box legend-all" /> All
          </button>
          <button
            type="button"
            className={`satt-legend-btn ${activeFilter === 'road' ? 'satt-legend-btn-active' : ''}`}
            onClick={() => onFilterChange && onFilterChange(activeFilter === 'road' ? 'all' : 'road')}
            title="Roads"
          >
            <span className="legend-box legend-roads" /> Road
          </button>
          <button
            type="button"
            className={`satt-legend-btn ${activeFilter === 'built' ? 'satt-legend-btn-active' : ''}`}
            onClick={() => onFilterChange && onFilterChange(activeFilter === 'built' ? 'all' : 'built')}
            title="Buildings"
          >
            <span className="legend-box legend-built" /> Building
          </button>
          <button
            type="button"
            className={`satt-legend-btn ${activeFilter === 'forest' ? 'satt-legend-btn-active' : ''}`}
            onClick={() => onFilterChange && onFilterChange(activeFilter === 'forest' ? 'all' : 'forest')}
            title="Forest"
          >
            <span className="legend-box legend-veg" /> Forest
          </button>
          <button
            type="button"
            className={`satt-legend-btn ${activeFilter === 'river' ? 'satt-legend-btn-active' : ''}`}
            onClick={() => onFilterChange && onFilterChange(activeFilter === 'river' ? 'all' : 'river')}
            title="River"
          >
            <span className="legend-box legend-river" /> River
          </button>
          <button
            type="button"
            className={`satt-legend-btn ${activeFilter === 'pond' ? 'satt-legend-btn-active' : ''}`}
            onClick={() => onFilterChange && onFilterChange(activeFilter === 'pond' ? 'all' : 'pond')}
            title="Pond"
          >
            <span className="legend-box legend-pond" /> Pond
          </button>
        </div>

        {/* Scale Indicator */}
        <div className="satt-viewport-scale">
          <div className="satt-scale-line" />
          <div className="satt-scale-labels">
            <span>0</span>
            <span>250</span>
            <span>500</span>
            <span>1,000 m</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CesiumGlobeViewer;
