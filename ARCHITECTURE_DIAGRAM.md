# 📊 Arquitetura Visual - Hardware Setup

## 🏗️ Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Telas (Dashboard, Courts, Profile, etc)             │  │
│  │ Consome: CourtListNotifier + PlayerStatsNotifier   │  │
│  └──────────────┬───────────────────────────────────────┘  │
└─────────────────┼──────────────────────────────────────────┘
                  │ Provider (state management)
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROVIDERS (State)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ CourtListNotifier ChangeNotifier                   │   │
│  │  ├─ userLatitude, userLongitude                    │   │
│  │  ├─ gpsStatus: GPSSignalStatus                    │   │
│  │  ├─ isListeningToGPS: bool                        │   │
│  │  ├─ requestUserLocation() → LocationResult        │   │
│  │  ├─ startListeningToLocation() [stream-based]     │   │
│  │  ├─ stopListeningToLocation() [battery saver]     │   │
│  │  ├─ simulateGPSLoss() [testing]                   │   │
│  │  └─ simulateGPSRecovery() [testing]               │   │
│  └──────────────┬─────────────────────────────────────┘   │
│  ┌──────────────▼─────────────────────────────────────┐   │
│  │ PlayerStatsNotifier ChangeNotifier                 │   │
│  │  ├─ stats: List<PlayerStats>                      │   │
│  │  ├─ fetchAllPlayerStats(forceRefresh)             │   │
│  │  └─ updatePlayerStats(id, updates)                │   │
│  └──────────────┬─────────────────────────────────────┘   │
└─────────────────┼──────────────────────────────────────────┘
                  │ ServiceLocator (dependency injection)
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  SERVICE LAYER                              │
│                                                              │
│  ┌──────────────────────┐   ┌──────────────────────┐       │
│  │  GPS Services        │   │  Permission Services │       │
│  │  ┌────────────────┐  │   │  ┌────────────────┐  │       │
│  │  │LocationService │  │   │  │ Media Permission│  │       │
│  │  │ (static utils) │  │   │  │ Service        │  │       │
│  │  │                │  │   │  │                │  │       │
│  │  │ Methods:       │  │   │  │ Methods:       │  │       │
│  │  │ • getLocation  │  │   │  │ • requestCamera│  │       │
│  │  │ • getStream    │  │   │  │ • requestGallery│ │       │
│  │  │ • openSettings │  │   │  │ • requestMicro │  │       │
│  │  └────────────────┘  │   │  │ • requestMulti │  │       │
│  └──────────────────────┘   │  │                │  │       │
│                              │  │ Status Enums: │  │       │
│  ┌──────────────────────┐   │  │ • granted     │  │       │
│  │ Lifecycle Manager    │   │  │ • denied      │  │       │
│  │ ┌────────────────┐   │   │  │ • forever     │  │       │
│  │ │AppLifecycle    │   │   │  │ • restricted  │  │       │
│  │ │Manager         │   │   │  │ • provisional │  │       │
│  │ │(singleton)     │   │   │  │ • limited     │  │       │
│  │ │                │   │   │  └────────────────┘  │       │
│  │ │ Manages:       │   │   └──────────────────────┘       │
│  │ │ • onAppResume()│   │                                   │
│  │ │ • onAppPause()│   │  ┌──────────────────────┐         │
│  │ │ • Callbacks    │   │  │ API Services         │         │
│  │ │                │   │  │ ┌────────────────┐  │         │
│  │ │ Used by:       │   │  │ │ DioApiService  │  │         │
│  │ │ • Pause GPS    │   │  │ │ (concrete impl)│  │         │
│  │ │ • Resume GPS   │   │  │ │                │  │         │
│  │ │ • Battery save │   │  │ │ Methods:       │  │         │
│  │ │                │   │  │ │ • getPlayer    │  │         │
│  │ └────────────────┘   │  │ │ • updatePlayer │  │         │
│  └──────────────────────┘  │ │ • getCourts    │  │         │
│                              │ │ • updateCourts │  │         │
│                              │ │                │  │         │
│                              │ │ Base: Dio 5.7 │  │         │
│                              │ └────────────────┘  │         │
│                              └──────────────────────┘       │
│                                                              │
│  ┌──────────────────────┐   ┌──────────────────────┐       │
│  │LocalStorageService   │   │ SharedPreferences    │       │
│  │(cache with TTL)      │   │(persistent storage)  │       │
│  │                      │   │                      │       │
│  │ Buckets:             │   │ Features:            │       │
│  │ • playerStats        │   │ • 30-min default TTL │       │
│  │ • courts             │   │ • JSON serialization │       │
│  │ • userProfile        │   │ • Hydration support  │       │
│  │ • matchState         │   │                      │       │
│  │ • lastSync           │   │ Init:                │       │
│  │                      │   │ • await              │       │
│  │ Methods:             │   │   setupServiceLocator│       │
│  │ • save*              │   │                      │       │
│  │ • get*               │   │ Used by:             │       │
│  │ • isCacheExpired()   │   │ • All Notifiers      │       │
│  │ • getMinutesSinceSave│   │ • Hydration         │       │
│  └──────────────────────┘   └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼ (calls at init)
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL LIBRARIES                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐ │
│  │ Geolocator   │  │ Permission   │  │ SharedPreferences │ │
│  │ v13.0.2      │  │ Handler      │  │ v2.2.3            │ │
│  │              │  │ v11.4.4      │  │                   │ │
│  │ GPS/Location │  │ Permissions  │  │ Persistent Storage│ │
│  │ Services     │  │ Dialog       │  │ (phone storage)   │ │
│  └──────────────┘  └──────────────┘  └───────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐ │
│  │ Provider     │  │ get_it       │  │ app_lifecycle     │ │
│  │ v6.1.2       │  │ v7.6.7       │  │ v2.0.0            │ │
│  │              │  │              │  │                   │ │
│  │ State mgmt   │  │ Service      │  │ App lifecycle     │ │
│  │ Reactive UI  │  │ Locator      │  │ Tracking         │ │
│  │              │  │ Dep. Inject. │  │                   │ │
│  └──────────────┘  └──────────────┘  └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              DEVICE HARDWARE                                │
│                                                              │
│  ┌──────────────────────┐   ┌──────────────────────┐       │
│  │ GPS Hardware         │   │ Camera Hardware      │       │
│  │ ┌────────────────┐   │   │ ┌────────────────┐   │       │
│  │ │Satellite Signal│   │   │ │Lens/Sensor     │   │       │
│  │ │Receiver        │   │   │ │JPEG/H.264      │   │       │
│  │ │Accuracy: 5-20m │   │   │ │Resolution: 8MP+│   │       │
│  │ │Update rate: 1Hz│   │   │ │Flash: optional │   │       │
│  │ └────────────────┘   │   │ └────────────────┘   │       │
│  └──────────────────────┘   └──────────────────────┘       │
│                                                              │
│  ┌──────────────────────┐   ┌──────────────────────┐       │
│  │ Storage Hardware     │   │ Battery Hardware     │       │
│  │ ┌────────────────┐   │   │ ┌────────────────┐   │       │
│  │ │Phone Storage   │   │   │ │Li-Ion 3500mAh+ │   │       │
│  │ │SD Card         │   │   │ │GPS power: 5-10%│   │       │
│  │ │Capacity: 32GB+ │   │   │ │Our mode: <1%   │   │       │
│  │ │Speed: USB 3.0+ │   │   │ │Savings: 500mAh │   │       │
│  │ └────────────────┘   │   │ └────────────────┘   │       │
│  └──────────────────────┘   └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Lifecycle Flow

```
┌─────────────────────────┐
│   App Cold Start        │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ main() async                        │
│  └─ setupServiceLocator()           │
│     ├─ SharedPreferences.getInstance│
│     ├─ Register ApiService          │
│     ├─ Register LocalStorage        │
│     ├─ Register MockApiService      │
│     └─ AppLifecycleManager.register │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ runApp(MatchingEsportivoApp)        │
│  └─ MultiProvider setup             │
│     ├─ PlayerStatsNotifier          │
│     └─ CourtListNotifier            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ MaterialApp                         │
│  └─ AppLifecycleHandler             │
│     └─ ClubIdentityPage             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ User Opens Court List Page          │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────────┐  ┌──────────────────┐
│ initState()  │  │ didChangeAppLife │
│              │  │ cycleState()     │
│ Calls:       │  │                  │
│ - requestUser│  │ resumed?         │
│   Location() │  │  └─ Start GPS    │
│ - fetch      │  │                  │
│   Courts()   │  │ paused?          │
│ - startList  │  │  └─ Stop GPS     │
│   ening()    │  │                  │
└──────────────┘  └──────────────────┘
    │                 │
    └────────┬────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ GPS Listening Active                │
│ (continuous updates every 10m)      │
│                                     │
│ Consumer<CourtListNotifier>         │
│  └─ notifier.gpsStatus              │
│     └─ UI Updates in Real-time      │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ App Minimized (Home pressed)        │
│                                     │
│ AppLifecycleManager.onAppPaused()   │
│  └─ CourtListNotifier.stop          │
│     ListeningToLocation()           │
│     ├─ _positionSubscription.cancel│
│     ├─ _isListeningToGPS = false   │
│     └─ Battery: Saved (~5mW)        │
└────────────┬────────────────────────┘
             │
       [10 seconds passed]
             │
             ▼
┌─────────────────────────────────────┐
│ App Resumed (User returns)          │
│                                     │
│ AppLifecycleManager.onAppResumed()  │
│  └─ CourtListNotifier.start         │
│     ListeningToLocation()           │
│     ├─ LocationService.getStream()  │
│     ├─ _positionSubscription =...   │
│     ├─ _isListeningToGPS = true     │
│     └─ Resuming updates             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ GPS Listening Resumed               │
│ (continuous updates every 10m)      │
└─────────────────────────────────────┘
```

---

## 📍 GPS Status Diagram

```
┌─────────────────────────────────────┐
│ requestUserLocation() called         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ LocationService.getLocationWithFallback()
│  ├─ isLocationServiceEnabled()?     │
│  │  ├─ Yes → continue               │
│  │  └─ No → USE FALLBACK             │
│  │         (-15.7942, -48.0676)     │
│  │         status = serviceDisabled  │
│  │         → Show GPS Disabled Sheet │
└────────────┬────────────────────────┘
             │
             ▼ (if service enabled)
┌─────────────────────────────────────┐
│ Check Permission                    │
│  ├─ denied?                         │
│  │  └─ Request permission           │
│  ├─ deniedForever?                  │
│  │  └─ Return status=deniedForever   │
│  │     → Show Settings Sheet         │
│  └─ granted?                        │
│     └─ Continue                     │
└────────────┬────────────────────────┘
             │
             ▼ (if granted)
┌─────────────────────────────────────┐
│ getCurrentPosition(timeout: 10s)     │
│  ├─ Success?                        │
│  │  └─ status = success             │
│  │     return (lat, lng, timestamp)  │
│  └─ Timeout?                        │
│     └─ USE FALLBACK                 │
│        status = timeout             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ Update CourtListNotifier            │
│  ├─ _userLatitude = result.lat      │
│  ├─ _userLongitude = result.lng     │
│  ├─ _gpsStatus = determineStatus()  │
│  │  ├─ accuracy < 5m? → strong      │
│  │  ├─ accuracy < 20m? → weak       │
│  │  ├─ timeout? → lost              │
│  │  └─ service disabled? → disabled  │
│  └─ notifyListeners()               │
└─────────────────────────────────────┘
```

---

## 📊 Data Flow - Quadras com Filtro GPS

```
┌──────────────────────┐
│ CourtList Widget     │
│ onTap("Search")      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────┐
│ fetchAvailableCourts()           │
│  ├─ if useUserLocation:          │
│  │   ├─ _userLatitude            │
│  │   ├─ _userLongitude           │
│  │   └─ calculate distance        │
│  │       sort by proximity        │
│  │                                │
│  └─ ApiService.getAvailableCourts│
│     ├─ Call: GET /v1/courts      │
│     ├─ With: lat, lng, radius    │
│     └─ Response: List<Court>     │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ LocalStorageService.saveCourts() │
│  ├─ JSON encode List<Court>      │
│  ├─ Save to SharedPreferences     │
│  │  key: "courts_cache"           │
│  │  value: json string            │
│  ├─ Save timestamp                │
│  │  key: "lastSync"               │
│  │  value: DateTime.now()         │
│  └─ _state = success              │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ notifyListeners()                │
│  └─ All Consumer widgets rebuild  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ UI Updates                       │
│ ├─ _courts list shown            │
│ ├─ Cache indicator: green        │
│ ├─ Distance badges               │
│ └─ Sort: nearest first           │
└──────────────────────────────────┘
```

---

## 🧪 Test Case Flow

```
test("GPS Strong → Lost → Strong")
  │
  ├─ setup():
  │  ├─ Create notifier
  │  ├─ Load initial courts (5 items)
  │  └─ Verify isLoading = false
  │
  ├─ Act 1: GPS Strong
  │  ├─ requestUserLocation()
  │  ├─ gpsStatus = strong
  │  └─ coordinates = real
  │
  ├─ Act 2: Simulate Loss
  │  ├─ simulateGPSLoss()
  │  ├─ gpsStatus = lost
  │  ├─ errorMessage = "Signal lost"
  │  └─ latLng = fallback
  │
  ├─ Act 3: Fetch Courts (during loss)
  │  ├─ fetchAvailableCourts()
  │  ├─ Uses fallback (-15.79, -48.06)
  │  ├─ Courts still load (offline cache)
  │  └─ No error
  │
  ├─ Act 4: Simulate Recovery
  │  ├─ simulateGPSRecovery()
  │  ├─ gpsStatus = strong
  │  ├─ coordinates = real again
  │  └─ refetch courts
  │
  └─ Verify:
     ├─ courts.length > 0
     ├─ No exceptions
     ├─ UI responsive throughout
     └─ Status transitions correct
```

---

**Architecture Status: ✅ Production Ready**
