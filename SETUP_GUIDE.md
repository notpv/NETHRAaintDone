# 🚀 NETHRA Setup Guide

This guide will help you set up and run the NETHRA banking security system on your local machine.

## 📋 Prerequisites

### Required Software
- **Python 3.8+** with pip
- **Flutter SDK 3.0+**
- **Android Studio** or **VS Code**
- **Git** for version control

### Platform-Specific Requirements

#### Windows
- Windows 10/11
- PowerShell or Command Prompt
- Android SDK (via Android Studio)

#### macOS
- macOS 10.14+
- Xcode (for iOS development)
- Homebrew (recommended)

#### Linux
- Ubuntu 18.04+ or equivalent
- Android SDK

## 🔧 Installation Steps

### 1. Clone the Repository
```bash
git clone <repository-url>
cd NETHRA
```

### 2. Backend Setup

#### Navigate to Backend Directory
```bash
cd backend
```

#### Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Initialize Database
```bash
python init_database.py
```

#### Start Backend Server
```bash
python main.py
```

The backend will start on `http://localhost:8000`

**Verify Backend**: Visit `http://localhost:8000/docs` to see the API documentation

### 3. Frontend Setup

#### Navigate to Frontend Directory
```bash
cd member3_flutter_frontend
```

#### Install Flutter Dependencies
```bash
flutter pub get
```

#### Configure API Endpoint
Edit `lib/core/constants/app_constants.dart`:
```dart
static const String baseUrl = 'http://127.0.0.1:8000'; // For local development
// For Android emulator: 'http://10.0.2.2:8000'
// For physical device: 'http://YOUR_IP:8000'
```

#### Run Flutter App
```bash
# For Android emulator
flutter run

# For specific device
flutter devices  # List available devices
flutter run -d <device-id>
```

## 🎮 Testing the Integration

### 1. Start Both Services
- Backend: `http://localhost:8000`
- Frontend: Running on emulator/device

### 2. Login with Demo Credentials
- **Username**: `demo_user`
- **Password**: `demo123`

### 3. Test Features

#### Real-time Trust Monitoring
1. Navigate through the app
2. Watch trust score update in real-time
3. Check Trust Monitor screen for detailed metrics

#### Mirage Interface
1. Go to Trust Monitor
2. Tap "Simulate Threat"
3. Experience the adaptive mirage interface
4. Complete cognitive challenges

#### Personalized Security
1. Use the app for 5-10 minutes
2. Visit Personalization Demo
3. See how thresholds adapt to your behavior

## 🔍 Troubleshooting

### Backend Issues

#### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # macOS/Linux

# Kill the process
taskkill /PID <PID> /F  # Windows
kill -9 <PID>  # macOS/Linux
```

#### Database Issues
```bash
cd backend
python force_db_init.py  # Force recreate database
```

#### Import Errors
```bash
pip install --upgrade -r requirements.txt
python test_imports.py  # Test all imports
```

### Frontend Issues

#### Flutter Dependencies
```bash
flutter clean
flutter pub get
flutter pub deps  # Check dependency tree
```

#### Android Emulator
```bash
flutter doctor  # Check Flutter installation
flutter emulators  # List available emulators
flutter emulators --launch <emulator-name>
```

#### Network Connection
- Ensure backend is running on correct port
- Check firewall settings
- For physical device, use your computer's IP address

### Common Integration Issues

#### CORS Errors
The backend is configured with CORS enabled. If you still see CORS errors:
1. Restart the backend server
2. Check the API base URL in frontend constants
3. Ensure you're using the correct protocol (http/https)

#### Authentication Failures
1. Verify backend is running and accessible
2. Check network connectivity
3. Try the demo credentials: `demo_user` / `demo123`
4. Check backend logs for authentication errors

#### Trust Score Not Updating
1. Ensure both backend and frontend are running
2. Check API connectivity
3. Verify user is logged in
4. Check backend logs for trust prediction errors

## 📊 Monitoring & Logs

### Backend Logs
The backend provides detailed logging:
- Authentication events
- Trust score predictions
- Mirage activations
- API requests and responses

### Frontend Debugging
Enable debug mode in Flutter:
```bash
flutter run --debug
```

Check console logs for:
- API call results
- Trust score updates
- Behavioral data collection
- Error messages

### Health Checks
- Backend health: `http://localhost:8000/health`
- API documentation: `http://localhost:8000/docs`
- System metrics: `http://localhost:8000/api/monitoring/metrics`

## 🎯 Demo Scenarios

### Scenario 1: Normal User Behavior
1. Login with demo credentials
2. Navigate normally through the app
3. Observe high trust scores (80-100)
4. See green trust indicators

### Scenario 2: Suspicious Behavior Simulation
1. In Trust Monitor, tap "Simulate Threat"
2. Trust score drops to critical levels
3. Mirage interface activates automatically
4. Complete challenges to restore access

### Scenario 3: Personalization Learning
1. Use the app for extended periods
2. Visit Personalization Demo
3. See how your behavioral baseline develops
4. Compare standard vs. personalized scores

## 🔧 Advanced Configuration

### Backend Configuration
Edit `backend/config.py`:
- Database settings
- JWT token expiration
- Trust score thresholds
- Mirage activation parameters

### Frontend Configuration
Edit `member3_flutter_frontend/lib/core/constants/app_constants.dart`:
- API endpoints
- Trust thresholds
- Update intervals
- Demo settings

## 📱 Device-Specific Setup

### Android Emulator
1. Open Android Studio
2. Create/start an AVD (Android Virtual Device)
3. Run `flutter run` to deploy to emulator

### Physical Android Device
1. Enable Developer Options
2. Enable USB Debugging
3. Connect device via USB
4. Update API base URL to your computer's IP

### iOS Simulator (macOS only)
1. Install Xcode
2. Open iOS Simulator
3. Run `flutter run` to deploy to simulator

## 🎉 Success Indicators

You'll know the integration is working when:
- ✅ Backend starts without errors on port 8000
- ✅ Frontend connects and shows login screen
- ✅ Demo login succeeds and shows dashboard
- ✅ Trust score updates in real-time
- ✅ Mirage interface can be triggered
- ✅ API calls succeed (check backend logs)

## 🆘 Getting Help

If you encounter issues:
1. Check this troubleshooting guide
2. Review backend logs for errors
3. Verify all prerequisites are installed
4. Ensure both services are running
5. Test API endpoints directly using the docs at `http://localhost:8000/docs`

---

**NETHRA** - Secure, Intelligent, Adaptive 🛡️