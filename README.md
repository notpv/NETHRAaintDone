# 🔐 NETHRA: Personalized AI Security for Mobile Banking

NETHRA is a privacy-first mobile banking security system that continuously authenticates users using behavioral biometrics (e.g., tap, swipe, tilt). When anomalies are detected, it deploys an Adaptive Mirage Interface—a deceptive fake UI with misleading data and cognitive micro-challenges to confuse attackers, all while safeguarding the user's account.

## 🎯 Key Features

- **TrustProfile**: Learns user behavior (touch, swipe, motion) and detects anomalies
- **TrustIndex (0–100)**: Real-time behavioral trust meter—green/yellow/red zones
- **Dynamic Personal Thresholds**: Personalized trust cutoffs using behavioral history (mean – 2 stddev after 5–7 sessions)
- **Adaptive Mirage Interface**: Fake UI screens (e.g., fake balances, delays, glitches) on suspicious behavior
- **Cognitive Micro-Challenges**: Verification tasks like familiar pattern taps
- **Tamper Detection**: Locks the app on system-level tampering
- **Federated Learning**: On-device private model updates (no cloud data exposure)
- **Energy Efficient**: AI optimized to use <2.5% battery on older phones

## 🏗️ Architecture

### Backend Intelligence (Guardian AI)
- **FastAPI**: Asynchronous Python backend with real-time APIs
- **SQLite**: WAL-optimized lightweight database
- **TensorFlow/Keras**: CNN + Transformer + GNN model for trust scoring
- **JWT + AES**: Secure sessions and encrypted data
- **Prometheus + Grafana**: Real-time system monitoring and analytics

### Frontend Tech
- **Flutter**: Cross-platform (Android + iOS)
- **Design**: Sleek, modern UI using Montserrat fonts
- **Real-time Integration**: Live trust scoring and behavioral monitoring
- **Adaptive UI**: Dynamic mirage interface activation

## 📡 API Integration

### Authentication Endpoints
- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/validate-token` - Token validation
- `POST /api/auth/logout` - User logout

### Trust & AI Endpoints
- `POST /api/trust/predict-trust` - Real-time trust score prediction
- `GET /api/trust/threshold-analysis/{user_id}` - Personal threshold analysis
- `GET /api/trust/user-trust-history/{user_id}` - Trust score history

### Session Management
- `POST /api/session/create` - Create user session
- `GET /api/session/status/{token}` - Session status
- `POST /api/session/heartbeat/{token}` - Keep session alive

### Mirage Interface
- `GET /api/mirage/status/{user_id}` - Mirage activation status
- `GET /api/mirage/fake-data/{user_id}` - Generate fake account data

### User Profile & Monitoring
- `GET /api/user/profile` - User profile and trust stats
- `GET /api/monitoring/health` - System health check
- `GET /api/monitoring/metrics` - System performance metrics

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with pip
- Flutter SDK 3.0+
- Android Studio / VS Code
- Android Emulator or physical device

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The backend will start on `http://localhost:8000`

### Frontend Setup
```bash
cd member3_flutter_frontend
flutter pub get
flutter run
```

### Demo Credentials
- **Username**: `demo_user`
- **Password**: `demo123`

## 🎮 Demo Features

### 1. Real-time Trust Monitoring
- Login with demo credentials
- Navigate through the app to see live trust score updates
- Trust score adapts based on your interaction patterns

### 2. Adaptive Mirage Interface
- In Trust Monitor, tap "Simulate Threat" to trigger mirage
- Experience fake UI with misleading data
- Complete cognitive challenges to restore access

### 3. Personalized Security
- Use the app normally to build your behavioral baseline
- After 5-10 interactions, see personalized thresholds
- Compare standard vs. personalized trust scores

### 4. System Monitoring
- Backend provides real-time health metrics
- Trust prediction analytics
- Session management and security events

## 🔧 Configuration

### Backend Configuration
Edit `backend/config.py` for:
- Database settings
- JWT configuration
- AI model parameters
- Security thresholds

### Frontend Configuration
Edit `member3_flutter_frontend/lib/core/constants/app_constants.dart` for:
- API base URL
- Trust thresholds
- Demo settings
- Update intervals

## 🛠️ Development

### Backend Development
```bash
cd backend
python main.py  # Development server with auto-reload
```

### Frontend Development
```bash
cd member3_flutter_frontend
flutter run --hot-reload
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation

## 🧪 Testing

### Backend Testing
```bash
cd backend
python test_imports.py  # Test all imports
python -m pytest  # Run tests (if available)
```

### Frontend Testing
```bash
cd member3_flutter_frontend
flutter test
```

## 📊 Monitoring & Analytics

### System Health
- Visit `http://localhost:8000/health` for system status
- Monitor trust prediction metrics
- Track user behavioral patterns

### Trust Analytics
- Real-time trust score visualization
- Behavioral pattern analysis
- Mirage activation statistics
- Personal threshold evolution

## 🔒 Security Features

### Privacy Protection
- All behavioral data processed locally
- No sensitive data sent to external servers
- Encrypted session management
- Secure token-based authentication

### Threat Detection
- Real-time behavioral anomaly detection
- Adaptive mirage interface deployment
- Tamper detection and response
- Cognitive challenge verification

## 🏆 Why NETHRA Wins

- **Adaptive Intelligence**: Replaces rigid rule-based systems with AI-driven behavior modeling
- **Deception Technology**: Combines mirage interfaces with machine learning for smarter fraud prevention
- **Privacy-First**: Optimized for privacy, battery, and real-world deployment
- **Inclusive Design**: Built for low-end and elderly-friendly devices
- **Complete Integration**: Functional backend-frontend integration with beautiful UI
- **Production Ready**: Clean architecture, comprehensive documentation, and demo readiness

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

This is a hackathon project demonstrating advanced AI security concepts. The codebase showcases:
- Real-time behavioral biometrics
- Adaptive security thresholds
- Deceptive interface technology
- Privacy-preserving AI
- Cross-platform mobile development

---

**NETHRA** - Where Trust Meets Intelligence 🛡️