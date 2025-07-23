import 'package:flutter/foundation.dart';
import 'dart:async';
import '../../../core/services/api_service.dart';
import '../../../core/services/firebase_service.dart';

class DemoProvider with ChangeNotifier {
  final ApiService _apiService;
  final FirebaseService _firebaseService;
  
  String _currentUserType = 'normal';
  bool _isDemoMode = false;
  Timer? _criticalThreatTimer;
  bool _disposed = false;
  
  DemoProvider(this._apiService, this._firebaseService);
  
  String get currentUserType => _currentUserType;
  bool get isDemoMode => _isDemoMode;
  
  void setDemoUser(String userType) {
    if (_disposed) return;
    
    _currentUserType = userType;
    _isDemoMode = userType != 'normal';
    
    // Handle critical threat auto-logout timer
    if (userType == 'user4_critical_threat') {
      _startCriticalThreatTimer();
    } else {
      _criticalThreatTimer?.cancel();
      _criticalThreatTimer = null;
    }
    
    if (kDebugMode) {
      print('🎭 Demo user set: $userType');
    }
    
    notifyListeners();
  }
  
  void _startCriticalThreatTimer() {
    _criticalThreatTimer?.cancel();
    _criticalThreatTimer = Timer(const Duration(seconds: 10), () {
      if (!_disposed) {
        _handleCriticalThreatLogout();
      }
    });
  }
  
  void _handleCriticalThreatLogout() {
    // This will be handled by the dashboard screen
    if (kDebugMode) {
      print('🚨 Critical threat auto-logout triggered');
    }
  }
  
  Future<void> sendMirageAlert(int userId, double trustScore) async {
    try {
      // Send email alert for mirage activation
      await _firebaseService.sendMirageActivationAlert(trustScore, 'high');
      
      if (kDebugMode) {
        print('📧 Mirage alert sent for user $userId');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to send mirage alert: $e');
      }
    }
  }
  
  void resetDemo() {
    if (_disposed) return;
    
    _currentUserType = 'normal';
    _isDemoMode = false;
    _criticalThreatTimer?.cancel();
    _criticalThreatTimer = null;
    
    notifyListeners();
  }
  
  @override
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    
    _criticalThreatTimer?.cancel();
    super.dispose();
  }
}