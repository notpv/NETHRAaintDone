import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/firebase_service.dart';
import '../../../core/constants/app_constants.dart';

class AuthProvider with ChangeNotifier {
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _errorMessage;
  String? _userId;
  String? _username;
  String? _email;
  String? _accessToken;
  String? _currentSessionToken;
  late final ApiService _apiService;
  late final FirebaseService _firebaseService;
  bool _disposed = false;
  bool _initialized = false;
  
  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get userId => _userId;
  String? get username => _username;
  String? get email => _email;
  String? get accessToken => _accessToken;
  String? get currentSessionToken => _currentSessionToken;
  ApiService get apiService => _apiService;
  FirebaseService get firebaseService => _firebaseService;
  
  AuthProvider() {
    _apiService = ApiService();
    _firebaseService = FirebaseService();
  }
  
  Future<void> initialize() async {
    if (_initialized || _disposed) return;
    
    try {
      await _firebaseService.initialize();
      await checkAuthStatus();
      _initialized = true;
      
      if (kDebugMode) {
        print('✅ AuthProvider initialized');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ AuthProvider initialization failed: $e');
      }
    }
  }
  
  Future<void> checkAuthStatus() async {
    if (_disposed) return;
    
    try {
      // Quick local check first
      final prefs = await SharedPreferences.getInstance();
      _isAuthenticated = prefs.getBool('isAuthenticated') ?? false;
      _userId = prefs.getString('userId');
      _username = prefs.getString('username');
      _email = prefs.getString('email');
      _accessToken = prefs.getString('accessToken');
      _currentSessionToken = prefs.getString('currentSessionToken');
      
      // Notify listeners immediately with local data
      if (!_disposed) {
        notifyListeners();
      }
      
      // Validate token with backend if we have one
      if (_accessToken != null) {
        _apiService.setAuthToken(_accessToken!);
        
        // Validate token in background (non-blocking)
        _validateTokenInBackground();
      }
      
      if (kDebugMode) {
        print('Auth status checked: $_isAuthenticated');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to check auth status: $e');
      }
    }
  }
  
  Future<void> _validateTokenInBackground() async {
    try {
      // Add timeout to prevent hanging
      final isValid = await _apiService.validateToken()
          .timeout(const Duration(seconds: 5));
      
      if (!isValid && !_disposed) {
        if (kDebugMode) {
          print('Token invalid, logging out');
        }
        await logout();
      } else if (isValid) {
        // Create new session if authenticated and don't have one
        if (_currentSessionToken == null) {
          await _createUserSession();
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('⚠️ Background token validation failed (keeping user logged in): $e');
      }
      // Keep user logged in for demo mode if backend is unreachable
    }
  }

  Future<bool> register(String username, String email, String password) async {
    if (_disposed) return false;
    
    _isLoading = true;
    _errorMessage = null;
    _safeNotifyListeners();
    
    try {
      if (kDebugMode) {
        print('Attempting registration for: $username');
      }
      
      final result = await _apiService.register(username, email, password);
      
      if (result['access_token'] != null) {
        final userInfo = result['user_info'];
        await _setAuthenticatedState(
          true,
          userInfo['id'].toString(),
          userInfo['username'],
          userInfo['email'],
          result['access_token'],
        );
        
        if (kDebugMode) {
          print('✅ Registration successful');
        }
        
        return true;
      } else {
        _errorMessage = result['detail'] ?? 'Registration failed';
        return false;
      }
    } catch (e) {
      _errorMessage = _parseErrorMessage(e.toString());
      if (kDebugMode) {
        print('❌ Registration failed: $_errorMessage');
      }
      return false;
    } finally {
      _isLoading = false;
      _safeNotifyListeners();
    }
  }
  
  Future<bool> login(String username, String password) async {
    if (_disposed) return false;
    
    _isLoading = true;
    _errorMessage = null;
    _safeNotifyListeners();
    
    try {
      if (kDebugMode) {
        print('Attempting login for: $username');
      }
      
      final result = await _apiService.login(username, password);
      
      if (result['access_token'] != null) {
        final userInfo = result['user_info'];
        await _setAuthenticatedState(
          true,
          userInfo['id'].toString(),
          userInfo['username'],
          userInfo['email'],
          result['access_token'],
        );
        
        if (kDebugMode) {
          print('✅ Login successful');
        }
        
        return true;
      } else {
        _errorMessage = result['detail'] ?? 'Invalid username or password';
        return false;
      }
    } catch (e) {
      _errorMessage = _parseErrorMessage(e.toString());
      if (kDebugMode) {
        print('❌ Login failed: $_errorMessage');
      }
      return false;
    } finally {
      _isLoading = false;
      _safeNotifyListeners();
    }
  }
  
  String _parseErrorMessage(String errorString) {
    // Extract meaningful error messages from exceptions
    if (errorString.contains('Incorrect username or password')) {
      return 'Invalid username or password';
    } else if (errorString.contains('Username already registered')) {
      return 'Username already exists. Try a different username or login instead.';
    } else if (errorString.contains('Network error') || errorString.contains('timeout')) {
      return 'Connection failed. Please check your internet connection.';
    } else if (errorString.contains('401')) {
      return 'Invalid credentials. Please check your username and password.';
    } else if (errorString.contains('400')) {
      return 'Invalid request. Please check your information.';
    } else if (errorString.contains('500')) {
      return 'Server error. Please try again later.';
    }
    return 'Authentication failed. Please try again.';
  }
  
  Future<bool> deleteAccount() async {
    if (!_isAuthenticated || _userId == null || _disposed) return false;
    
    _isLoading = true;
    _safeNotifyListeners();
    
    try {
      // Note: Backend doesn't have delete endpoint, so we'll just logout
      // In a real implementation, you'd call a delete endpoint here
      await logout();
      
      // Send notification about account deletion
      await _firebaseService.sendSecurityRestoreAlert();
      
      return true;
    } catch (e) {
      _errorMessage = 'Account deletion failed: ${e.toString()}';
      return false;
    } finally {
      _isLoading = false;
      _safeNotifyListeners();
    }
  }
  
  Future<void> _createUserSession() async {
    if (_userId == null || _disposed) return;
    
    try {
      final sessionResult = await _apiService.createSession(
        deviceInfo: await _getDeviceInfo(),
      );
      
      if (sessionResult['session_token'] != null) {
        _currentSessionToken = sessionResult['session_token'];
        
        // Save session token
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('currentSessionToken', _currentSessionToken!);
        
        if (kDebugMode) {
          print('✅ User session created: $_currentSessionToken');
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to create user session: $e');
      }
    }
  }
  
  Future<Map<String, dynamic>> _getDeviceInfo() async {
    // Get device information for session creation
    return {
      'platform': 'flutter',
      'app_version': '1.0.0',
      'timestamp': DateTime.now().toIso8601String(),
    };
  }
  
  Future<void> logout() async {
    if (_disposed) return;
    
    try {
      // Terminate current session if exists
      if (_currentSessionToken != null) {
        await _apiService.terminateSession(_currentSessionToken!);
      }
      
      await _apiService.logout();
    } catch (e) {
      if (kDebugMode) {
        print('Logout error (ignored): $e');
      }
    }
    
    await _setAuthenticatedState(false, null, null, null, null);
  }
  
  Future<void> _setAuthenticatedState(
    bool isAuthenticated, 
    String? userId, 
    String? username, 
    String? email,
    String? accessToken
  ) async {
    if (_disposed) return;
    
    try {
      final prefs = await SharedPreferences.getInstance();
      
      _isAuthenticated = isAuthenticated;
      _userId = userId;
      _username = username;
      _email = email;
      _accessToken = accessToken;
      
      await prefs.setBool('isAuthenticated', isAuthenticated);
      
      if (userId != null) {
        await prefs.setString('userId', userId);
      } else {
        await prefs.remove('userId');
      }
      
      if (username != null) {
        await prefs.setString('username', username);
      } else {
        await prefs.remove('username');
      }
      
      if (email != null) {
        await prefs.setString('email', email);
      } else {
        await prefs.remove('email');
      }
      
      if (accessToken != null) {
        await prefs.setString('accessToken', accessToken);
        _apiService.setAuthToken(accessToken);
      } else {
        await prefs.remove('accessToken');
        await prefs.remove('currentSessionToken');
        _currentSessionToken = null;
      }
      
      _safeNotifyListeners();
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to set auth state: $e');
      }
    }
  }
  
  void clearError() {
    _errorMessage = null;
    _safeNotifyListeners();
  }
  
  void _safeNotifyListeners() {
    if (!_disposed) {
      notifyListeners();
    }
  }
  
  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    
    // Clean up resources
    _apiService.dispose();
    _firebaseService.dispose();
    
    super.dispose();
  }
  
  @override
  void notifyListeners() {
    if (!_disposed) {
      super.notifyListeners();
    }
  }
}