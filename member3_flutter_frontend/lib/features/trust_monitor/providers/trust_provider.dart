import 'package:flutter/foundation.dart';
import 'dart:async';
import '../../../core/services/behavioral_service.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/firebase_service.dart';
import '../../../core/services/personalization_service.dart';
import '../../../shared/models/trust_data.dart';
import '../../../shared/models/behavioral_data.dart';
import '../../authentication/providers/auth_provider.dart';

class TrustProvider with ChangeNotifier {
  late final BehavioralService _behavioralService;
  late final PersonalizationService _personalizationService;
  late final ApiService _apiService;
  late final FirebaseService _firebaseService;
  Timer? _trustUpdateTimer;
  bool _disposed = false;
  
  double _trustScore = 85.0;
  TrustLevel _trustLevel = TrustLevel.high;
  List<String> _riskFactors = [];
  bool _isMonitoring = false;
  bool _shouldShowMirage = false;
  bool _isPersonalized = false;
  double _personalizedTrustScore = 85.0;
  double _standardTrustScore = 85.0;
  String? _currentSessionToken;
  AuthProvider? _authProvider;
  Map<String, dynamic>? _lastBackendResponse;
  bool _sessionCreated = false;
  int _retryCount = 0;
  static const int _maxRetries = 3;
  
  // For demo user simulation
  String _currentUserType = 'normal';
  int _demoSessionCount = 0;
  
  TrustProvider({AuthProvider? authProvider}) {
    _authProvider = authProvider;
    _apiService = authProvider?.apiService ?? ApiService();
    _firebaseService = FirebaseService();
    _behavioralService = BehavioralService(_apiService);
    _personalizationService = PersonalizationService();
    _initializeServices();
  }
  
  double get trustScore => _trustScore;
  TrustLevel get trustLevel => _trustLevel;
  List<String> get riskFactors => _riskFactors;
  bool get isMonitoring => _isMonitoring;
  bool get shouldShowMirage => _shouldShowMirage;
  bool get isPersonalized => _isPersonalized;
  double get personalizedTrustScore => _personalizedTrustScore;
  double get standardTrustScore => _standardTrustScore;
  String? get currentSessionToken => _currentSessionToken;
  Map<String, dynamic>? get lastBackendResponse => _lastBackendResponse;
  String get currentUserType => _currentUserType;
  
  // Method to get current behavioral data
  BehavioralData? getBehavioralData() {
    if (_behavioralService.isMonitoring) {
      return _behavioralService.generateBehavioralData();
    }
    return null;
  }
  
  Future<void> _initializeServices() async {
    try {
      await _firebaseService.initialize();
      await _personalizationService.initialize();
      _isPersonalized = !_personalizationService.isLearningPhase;
      
      // Set up behavioral service callback
      _behavioralService.setTrustScoreCallback(_handleTrustScoreUpdate);
      
      if (kDebugMode) {
        print('✅ Trust services initialized');
      }
      
      _safeNotifyListeners();
    } catch (e) {
      if (kDebugMode) {
        print('❌ Trust services initialization failed: $e');
      }
    }
  }
  
  // Demo user simulation methods
  void setUserType(String userType) {
    _currentUserType = userType;
    _demoSessionCount = 0;
    
    switch (userType) {
      case 'user1_low_threat':
        _trustScore = 85.0;
        _trustLevel = TrustLevel.high;
        _riskFactors = [];
        _shouldShowMirage = false;
        break;
      case 'user2_medium_threat':
        _trustScore = 65.0;
        _trustLevel = TrustLevel.medium;
        _riskFactors = ['Slight behavioral variation detected'];
        _shouldShowMirage = false;
        break;
      case 'user3_high_threat':
        _trustScore = 25.0;
        _trustLevel = TrustLevel.critical;
        _riskFactors = [
          'Suspicious behavioral patterns',
          'Unusual device handling',
          'Potential security threat'
        ];
        _shouldShowMirage = true;
        break;
      case 'user4_critical_threat':
        _trustScore = 5.0;
        _trustLevel = TrustLevel.critical;
        _riskFactors = [
          'Critical security threat detected',
          'Immediate action required',
          'Session will be terminated'
        ];
        _shouldShowMirage = true;
        break;
      default:
        _trustScore = 75.0;
        _trustLevel = TrustLevel.high;
        _riskFactors = [];
        _shouldShowMirage = false;
    }
    
    _safeNotifyListeners();
  }
  
  Future<void> startMonitoring() async {
    if (_isMonitoring || _disposed) return;
    
    try {
      // Set user session info for behavioral service
      if (_authProvider?.userId != null && !_sessionCreated) {
        final userId = int.tryParse(_authProvider!.userId!) ?? 1;
        await _createSingleSession(userId);
      }
      
      _isMonitoring = true;
      _behavioralService.startMonitoring();
      
      // Start periodic trust updates with retry logic
      _trustUpdateTimer = Timer.periodic(const Duration(seconds: 8), (timer) {
        _updateTrustWithBackend();
        _simulateUserBehavior(); // For demo purposes
      });
      
      if (kDebugMode) {
        print('🎯 Trust monitoring started');
      }
      
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to start monitoring: $e');
      }
    }
    
    _safeNotifyListeners();
  }
  
  void _simulateUserBehavior() {
    _demoSessionCount++;
    
    switch (_currentUserType) {
      case 'user1_low_threat':
        // Gradual improvement in trust score
        _trustScore = (85.0 + (_demoSessionCount * 0.5)).clamp(85.0, 95.0);
        _trustLevel = TrustLevel.high;
        _riskFactors = [];
        _shouldShowMirage = false;
        break;
        
      case 'user2_medium_threat':
        // Fluctuating trust score
        final variation = (_demoSessionCount % 4 - 2) * 5.0;
        _trustScore = (65.0 + variation).clamp(55.0, 75.0);
        _trustLevel = _trustScore >= 70 ? TrustLevel.high : TrustLevel.medium;
        _riskFactors = _trustScore < 60 ? ['Behavioral inconsistency detected'] : [];
        _shouldShowMirage = false;
        break;
        
      case 'user3_high_threat':
        // Declining trust score
        _trustScore = (35.0 - (_demoSessionCount * 2.0)).clamp(15.0, 35.0);
        _trustLevel = TrustLevel.critical;
        _riskFactors = [
          'Suspicious behavioral patterns',
          'Potential unauthorized access',
          if (_trustScore < 25) 'Critical security alert'
        ];
        _shouldShowMirage = true;
        break;
        
      case 'user4_critical_threat':
        // Immediate critical threat - auto logout after 5 updates
        if (_demoSessionCount >= 5) {
          _handleAutoLogout();
          return;
        }
        _trustScore = (10.0 - (_demoSessionCount * 1.0)).clamp(1.0, 10.0);
        _trustLevel = TrustLevel.critical;
        _riskFactors = [
          'Critical security threat',
          'Automated behavior detected',
          'Session termination imminent'
        ];
        _shouldShowMirage = true;
        break;
    }
    
    _safeNotifyListeners();
  }
  
  void _handleAutoLogout() {
    if (_authProvider != null) {
      _authProvider!.logout();
      _firebaseService.sendTamperAlert({
        'reason': 'Critical trust score detected',
        'trust_score': _trustScore,
        'user_type': _currentUserType,
      });
    }
    stopMonitoring();
  }
  
  Future<void> _createSingleSession(int userId) async {
    if (_sessionCreated || _disposed) return;
    
    try {
      final sessionResult = await _authProvider!.apiService.createSession(
        deviceInfo: {'platform': 'flutter', 'user_id': userId},
      );
      
      if (sessionResult['session_token'] != null) {
        _currentSessionToken = sessionResult['session_token'];
        _behavioralService.setUserSession(userId, _currentSessionToken);
        _sessionCreated = true;
        
        if (kDebugMode) {
          print('✅ Trust session created: $_currentSessionToken');
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to create trust session: $e');
      }
    }
  }
  
  void _handleTrustScoreUpdate(double trustScore, bool mirageActivated, Map<String, dynamic> response) {
    if (_disposed) return;
    
    _lastBackendResponse = response;
    
    // Only update if not in demo simulation mode
    if (_currentUserType == 'normal') {
      _trustScore = trustScore;
      _trustLevel = _getTrustLevelFromScore(trustScore);
      _shouldShowMirage = mirageActivated;
      _isPersonalized = response['learning_phase'] == false;
      
      // Update risk factors based on backend response
      _updateRiskFactors(response);
    }
    
    _retryCount = 0; // Reset retry count on successful update
    
    // Send Firebase notifications based on trust score and events
    _handleFirebaseNotifications(trustScore, mirageActivated, response);
    
    _safeNotifyListeners();
  }
  
  void _updateRiskFactors(Map<String, dynamic> response) {
    if (_currentUserType != 'normal') return; // Don't override demo risk factors
    
    _riskFactors.clear();
    
    final securityAction = response['security_action'] ?? '';
    final userMessage = response['user_message'] ?? '';
    
    if (securityAction == 'maximum_security') {
      _riskFactors.addAll([
        'Critical security threat detected',
        'Behavioral anomaly identified',
        'Enhanced protection activated'
      ]);
    } else if (securityAction == 'elevated_security') {
      _riskFactors.addAll([
        'Unusual behavior pattern detected',
        'Additional monitoring active'
      ]);
    } else if (securityAction == 'activate_mirage') {
      _riskFactors.addAll([
        'Suspicious activity detected',
        'Mirage interface deployed'
      ]);
    }
    
    if (userMessage.isNotEmpty && !userMessage.contains('Welcome')) {
      _riskFactors.add(userMessage);
    }
  }
  
  Future<void> _handleFirebaseNotifications(double trustScore, bool mirageActivated, Map<String, dynamic> response) async {
    try {
      // Send email alerts for mirage activation (User 3 & 4)
      if (mirageActivated && _authProvider?.email != null) {
        final emailService = EmailAlertService();
        final userId = int.tryParse(_authProvider!.userId ?? '0') ?? 0;
        
        await emailService.sendMirageActivationAlert(
          userEmail: _authProvider!.email!,
          userId: userId,
          trustScore: trustScore,
          intensity: response['mirage_intensity'] ?? 'moderate',
        );
      }
      
      // Log audit events
      final auditService = AuditService();
      final userId = int.tryParse(_authProvider?.userId ?? '0') ?? 0;
      
      auditService.logTrustScoreUpdate(
        userId: userId,
        oldScore: _trustScore,
        newScore: trustScore,
        behavioralData: response,
        sessionId: _currentSessionToken,
      );
      
      if (mirageActivated) {
        auditService.logMirageActivation(
          userId: userId,
          trustScore: trustScore,
          intensity: response['mirage_intensity'] ?? 'moderate',
          sessionId: _currentSessionToken,
        );
      }
      
      // Send trust score alert if low
      if (trustScore < 40) {
        final level = _getTrustLevelFromScore(trustScore).name;
        await _firebaseService.sendTrustScoreAlert(trustScore, level);
      }
      
      // Send mirage activation alert
      if (mirageActivated) {
        final intensity = response['mirage_intensity'] ?? 'moderate';
        await _firebaseService.sendMirageActivationAlert(trustScore, intensity);
      }
      
      // Send learning progress updates
      if (response['session_count'] != null && response['learning_phase'] == true) {
        final sessionCount = response['session_count'] as int;
        final learningProgress = sessionCount / 50.0; // Assuming 50 sessions for full learning
        await _firebaseService.sendPersonalizationUpdate(sessionCount, learningProgress);
      }
      
    } catch (e) {
      if (kDebugMode) {
        print('❌ Firebase notification failed: $e');
      }
    }
  }
  
  Future<void> _updateTrustWithBackend() async {
    if (!_isMonitoring || _authProvider?.userId == null || _disposed) return;
    
    try {
      final behavioralData = _behavioralService.generateBehavioralData();
      final userId = int.tryParse(_authProvider!.userId!) ?? 1;
      final backendData = behavioralData.toBackendFormat(userId);
      
      if (kDebugMode) {
        print('Sending trust update to backend...');
      }
      
      final result = await _apiService.predictTrustScore(backendData);
      
      if (result['success'] == true) {
        _handleTrustScoreUpdate(
          result['trust_score']?.toDouble() ?? _trustScore,
          result['mirage_activated'] == true,
          result
        );
        
        if (kDebugMode) {
          print('✅ Trust update successful: ${result['trust_score']}');
        }
      }
      
      // Send session heartbeat
      if (_currentSessionToken != null) {
        try {
          await _apiService.sendHeartbeat(_currentSessionToken!);
        } catch (e) {
          if (kDebugMode) {
            print('❌ Heartbeat failed: $e');
          }
        }
      }
      
    } catch (e) {
      _retryCount++;
      if (kDebugMode) {
        print('❌ Backend trust update failed (attempt $_retryCount): $e');
      }
      
      // Handle rate limiting gracefully
      if (e.toString().contains('Rate limit')) {
        // Slow down requests
        _trustUpdateTimer?.cancel();
        _trustUpdateTimer = Timer.periodic(const Duration(seconds: 15), (timer) {
          _updateTrustWithBackend();
          _simulateUserBehavior();
        });
        return;
      }
      
      // If max retries reached, use fallback behavior
      if (_retryCount >= _maxRetries) {
        _useFallbackTrustBehavior();
      }
    }
  }
  
  void _useFallbackTrustBehavior() {
    if (_disposed || _currentUserType != 'normal') return;
    
    // Simulate trust score variations for demo when backend is unavailable
    final behavioralData = _behavioralService.generateBehavioralData();
    
    // Simple local trust calculation
    double localTrustScore = 75.0;
    
    // Adjust based on basic behavioral metrics
    if (behavioralData.averageTapPressure < 0.3) localTrustScore -= 10;
    if (behavioralData.averageSwipeVelocity < 100) localTrustScore -= 15;
    if (behavioralData.deviceTiltVariation > 0.8) localTrustScore -= 8;
    
    localTrustScore = localTrustScore.clamp(0.0, 100.0);
    
    _trustScore = localTrustScore;
    _trustLevel = _getTrustLevelFromScore(localTrustScore);
    _shouldShowMirage = localTrustScore < 40;
    
    if (kDebugMode) {
      print('🔄 Using fallback trust behavior: $localTrustScore');
    }
    
    _safeNotifyListeners();
  }
  
  TrustLevel _getTrustLevelFromScore(double score) {
    if (score >= 80) return TrustLevel.high;
    if (score >= 60) return TrustLevel.medium;
    if (score >= 40) return TrustLevel.low;
    return TrustLevel.critical;
  }
  
  void stopMonitoring() {
    if (!_isMonitoring) return;
    
    _isMonitoring = false;
    _sessionCreated = false;
    _behavioralService.stopMonitoring();
    _trustUpdateTimer?.cancel();
    _trustUpdateTimer = null;
    _retryCount = 0;
    _demoSessionCount = 0;
    
    if (kDebugMode) {
      print('🛑 Trust monitoring stopped');
    }
    
    _safeNotifyListeners();
  }
  
  void forceUpdateTrust() {
    if (_isMonitoring) {
      _updateTrustWithBackend();
    }
  }
  
  Future<void> simulateThreat() async {
    // Simulate a security threat for demo purposes
    _trustScore = 25.0;
    _trustLevel = TrustLevel.critical;
    _riskFactors = [
      'Suspicious tap patterns detected',
      'Unusual device movement',
      'Potential unauthorized access',
    ];
    _shouldShowMirage = true;
    
    // Send Firebase alerts (but suppress during demo mode)
    if (_currentUserType == 'normal') {
      await _firebaseService.sendTrustScoreAlert(_trustScore, _trustLevel.name);
      await _firebaseService.sendMirageActivationAlert(_trustScore, 'high');
    }
    
    _safeNotifyListeners();
  }
  
  Future<void> resetTrust() async {
    // Reset trust score to normal for demo purposes
    _trustScore = 85.0;
    _trustLevel = TrustLevel.high;
    _riskFactors = [];
    _shouldShowMirage = false;
    _retryCount = 0;
    _currentUserType = 'normal';
    _demoSessionCount = 0;
    
    // Send restoration alert (but suppress during demo mode)
    if (_currentUserType == 'normal') {
      await _firebaseService.sendSecurityRestoreAlert();
    }
    
    _safeNotifyListeners();
  }
  
  // Record behavioral interactions
  void recordTap(double x, double y, double pressure) {
    if (!_disposed) {
      _behavioralService.recordTap(x, y, pressure, const Duration(milliseconds: 100));
    }
  }
  
  void recordSwipe(double startX, double startY, double endX, double endY, double velocity) {
    if (!_disposed) {
      _behavioralService.recordSwipe(startX, startY, endX, endY, velocity, const Duration(milliseconds: 300));
    }
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
    
    stopMonitoring();
    _behavioralService.dispose();
    super.dispose();
  }
  
  @override
  void notifyListeners() {
    if (!_disposed) {
      super.notifyListeners();
    }
  }
}