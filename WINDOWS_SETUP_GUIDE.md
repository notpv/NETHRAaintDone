# 🪟 NETHRA Windows Setup Guide (VS Code)

Complete step-by-step setup guide for running NETHRA on Windows using VS Code.

## 📋 Prerequisites Installation

### 1. Install Python 3.8+
1. Download from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT**: Check "Add Python to PATH" during installation
3. Verify installation:
```cmd
python --version
pip --version
```

### 2. Install Flutter SDK
1. Download Flutter SDK from [flutter.dev](https://flutter.dev/docs/get-started/install/windows)
2. Extract to `C:\src\flutter` (or your preferred location)
3. Add Flutter to PATH:
   - Open System Properties → Environment Variables
   - Add `C:\src\flutter\bin` to PATH
4. Verify installation:
```cmd
flutter doctor
```

### 3. Install Android Studio
1. Download from [developer.android.com](https://developer.android.com/studio)
2. Install with default settings
3. Open Android Studio → Configure → SDK Manager
4. Install Android SDK (API level 30+)
5. Create an Android Virtual Device (AVD)

### 4. Install VS Code
1. Download from [code.visualstudio.com](https://code.visualstudio.com/)
2. Install these extensions:
   - Python
   - Flutter
   - Dart
   - REST Client (optional, for API testing)

### 5. Install Git
1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Install with default settings

## 🚀 Project Setup

### 1. Clone and Open Project
```cmd
git clone <repository-url>
cd NETHRA
code .
```

### 2. Backend Setup in VS Code

#### Open Integrated Terminal
- Press `Ctrl + `` (backtick) or View → Terminal
- Ensure you're in the project root directory

#### Navigate to Backend
```cmd
cd backend
```

#### Create Virtual Environment
```cmd
python -m venv venv
```

#### Activate Virtual Environment
```cmd
venv\Scripts\activate
```
You should see `(venv)` in your terminal prompt.

#### Install Dependencies
```cmd
pip install -r requirements.txt
```

If you encounter errors, try:
```cmd
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

#### Initialize Database
```cmd
python init_database.py
```

Expected output:
```
✅ All database tables created successfully
🎯 NETHRA database initialized successfully!
```

#### Test Backend Imports
```cmd
python test_imports.py
```

Should show:
```
🎉 ALL IMPORTS SUCCESSFUL!
```

#### Start Backend Server
```cmd
python main.py
```

Expected output:
```
🚀 Starting NETHRA Backend Server...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal running!**

### 3. Frontend Setup in VS Code

#### Open New Terminal
- Press `Ctrl + Shift + `` to open a new terminal
- Or click the `+` button in the terminal panel

#### Navigate to Frontend
```cmd
cd member3_flutter_frontend
```

#### Install Flutter Dependencies
```cmd
flutter pub get
```

#### Check Flutter Setup
```cmd
flutter doctor
```

Fix any issues shown (Android licenses, etc.)

#### Configure API Endpoint
1. Open `lib/core/constants/app_constants.dart`
2. Update the baseUrl:
```dart
static const String baseUrl = 'http://10.0.2.2:8000'; // For Android emulator
// Use 'http://127.0.0.1:8000' for web or if emulator doesn't work
```

#### Start Android Emulator
In VS Code terminal:
```cmd
flutter emulators
flutter emulators --launch <emulator-name>
```

Or start from Android Studio:
1. Open Android Studio
2. AVD Manager → Start emulator

#### Run Flutter App
```cmd
flutter run
```

For specific device:
```cmd
flutter devices
flutter run -d <device-id>
```

## 🔧 VS Code Configuration

### 1. Workspace Settings
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./backend/venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "dart.flutterSdkPath": "C:\\src\\flutter",
    "files.exclude": {
        "**/venv/": true,
        "**/.dart_tool/": true,
        "**/build/": true
    }
}
```

### 2. Launch Configuration
Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "NETHRA Backend",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/backend/main.py",
            "cwd": "${workspaceFolder}/backend",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/backend"
            }
        },
        {
            "name": "NETHRA Flutter",
            "type": "dart",
            "request": "launch",
            "program": "${workspaceFolder}/member3_flutter_frontend/lib/main.dart",
            "cwd": "${workspaceFolder}/member3_flutter_frontend"
        }
    ]
}
```

### 3. Tasks Configuration
Create `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start NETHRA Backend",
            "type": "shell",
            "command": "python",
            "args": ["main.py"],
            "options": {
                "cwd": "${workspaceFolder}/backend"
            },
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "panel": "new"
            }
        },
        {
            "label": "Start Flutter App",
            "type": "shell",
            "command": "flutter",
            "args": ["run"],
            "options": {
                "cwd": "${workspaceFolder}/member3_flutter_frontend"
            },
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "panel": "new"
            }
        }
    ]
}
```

## 🧪 Testing the Setup

### 1. Verify Backend
1. Open browser to `http://localhost:8000`
2. Should see NETHRA API welcome message
3. Visit `http://localhost:8000/docs` for API documentation
4. Test health endpoint: `http://localhost:8000/health`

### 2. Verify Frontend
1. Flutter app should launch on emulator
2. Login screen should appear
3. Use demo credentials:
   - Username: `demo_user`
   - Password: `demo123`

### 3. Test Integration
1. Login with demo credentials
2. Navigate to dashboard
3. Check Trust Monitor for real-time updates
4. Try "Simulate Threat" to test mirage interface

## 🐛 Common Windows Issues & Solutions

### Python PATH Issues
```cmd
# Check Python installation
where python
python --version

# If not found, add to PATH manually:
# System Properties → Environment Variables → PATH
# Add: C:\Users\<username>\AppData\Local\Programs\Python\Python3x\
```

### Flutter PATH Issues
```cmd
# Check Flutter installation
where flutter
flutter --version

# If not found, add to PATH:
# Add: C:\src\flutter\bin
```

### Virtual Environment Issues
```cmd
# If activation fails:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again:
venv\Scripts\activate
```

### Android Emulator Issues
```cmd
# Check Android SDK
flutter doctor -v

# Accept licenses
flutter doctor --android-licenses

# If emulator won't start:
# Open Android Studio → AVD Manager → Wipe Data
```

### Port 8000 Already in Use
```cmd
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F

# Or use different port in backend/main.py:
# uvicorn.run("main:app", host="0.0.0.0", port=8001)
```

### CORS Issues
If you see CORS errors:
1. Restart backend server
2. Check API base URL in frontend
3. Try using `http://127.0.0.1:8000` instead of `localhost`

### Database Issues
```cmd
cd backend
python force_db_init.py  # Force recreate database
```

### Flutter Build Issues
```cmd
cd member3_flutter_frontend
flutter clean
flutter pub get
flutter run
```

## 🎯 VS Code Debugging

### Backend Debugging
1. Set breakpoints in Python files
2. Press `F5` or Run → Start Debugging
3. Select "NETHRA Backend" configuration

### Frontend Debugging
1. Set breakpoints in Dart files
2. Press `F5` or Run → Start Debugging
3. Select "NETHRA Flutter" configuration

### API Testing in VS Code
Install REST Client extension and create `test.http`:
```http
### Test Backend Health
GET http://localhost:8000/health

### Test Login
POST http://localhost:8000/api/auth/login
Content-Type: application/x-www-form-urlencoded

username=demo_user&password=demo123
```

## 📱 Device Configuration

### Android Emulator
1. Recommended: Pixel 4 API 30+
2. RAM: 4GB+
3. Enable hardware acceleration

### Physical Android Device
1. Enable Developer Options
2. Enable USB Debugging
3. Connect via USB
4. Update API base URL to your computer's IP:
```dart
static const String baseUrl = 'http://192.168.1.XXX:8000';
```

Find your IP:
```cmd
ipconfig | findstr IPv4
```

## 🎉 Success Checklist

- ✅ Python virtual environment activated
- ✅ Backend dependencies installed
- ✅ Database initialized successfully
- ✅ Backend running on port 8000
- ✅ Flutter dependencies installed
- ✅ Android emulator running
- ✅ Flutter app deployed to emulator
- ✅ Demo login successful
- ✅ Trust score updating in real-time
- ✅ Mirage interface triggerable

## 🆘 Getting Help

### Check Logs
- Backend logs in VS Code terminal
- Flutter logs in VS Code debug console
- Android logs: `flutter logs`

### Common Commands
```cmd
# Restart everything
cd backend && python main.py
cd member3_flutter_frontend && flutter run

# Clean restart
flutter clean && flutter pub get && flutter run

# Check system status
flutter doctor
python --version
```

### Useful VS Code Shortcuts
- `Ctrl + `` - Toggle terminal
- `Ctrl + Shift + `` - New terminal
- `F5` - Start debugging
- `Ctrl + Shift + P` - Command palette

---

**NETHRA on Windows** - Secure, Intelligent, Ready! 🛡️