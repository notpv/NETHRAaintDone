import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../core/services/api_service.dart';
import '../../../core/constants/app_constants.dart';

class AuthProvider with ChangeNotifier {
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _errorMessage;
  String? _userId;
  String? _username;
  String? _accessToken;
  final ApiService _apiService = ApiService();
  
  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get userId => _userId;
  String? get username => _username;
  String? get accessToken => _accessToken;
  ApiService get apiService => _apiService;
  
  Future<void> checkAuthStatus() async {
    final prefs = await SharedPreferences.getInstance();
    _isAuthenticated = prefs.getBool('isAuthenticated') ?? false;
    _userId = prefs.getString('userId');
    _username = prefs.getString('username');
    _accessToken = prefs.getString('accessToken');
    
    if (_accessToken != null) {
      _apiService.setAuthToken(_accessToken!);
      
      // Validate token with backend
      final isValid = await _apiService.validateToken();
      if (!isValid) {
        await logout();
      }
    }
    
    notifyListeners();
  }
  
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      // API authentication with backend
      final result = await _apiService.login(username, password);
      
      if (result['access_token'] != null) {
        final userInfo = result['user_info'];
        await _setAuthenticatedState(
          true, 
          userInfo['id'].toString(), 
          userInfo['username'],
          result['access_token'],
        );
        return true;
      } else {
        _errorMessage = result['detail'] ?? 'Invalid username or password';
        return false;
      }
    } catch (e) {
      _errorMessage = 'Authentication failed: ${e.toString()}';
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
  
  Future<void> logout() async {
    try {
      await _apiService.logout();
    } catch (e) {
      // Ignore logout errors
    }
    await _setAuthenticatedState(false, null, null, null);
  }
  
  Future<void> _setAuthenticatedState(bool isAuthenticated, String? userId, String? username, String? accessToken) async {
    final prefs = await SharedPreferences.getInstance();
    
    _isAuthenticated = isAuthenticated;
    _userId = userId;
    _username = username;
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
    
    if (accessToken != null) {
      await prefs.setString('accessToken', accessToken);
      _apiService.setAuthToken(accessToken);
    } else {
      await prefs.remove('accessToken');
    }
    
    notifyListeners();
  }
  
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}