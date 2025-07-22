import 'package:flutter/foundation.dart';
import 'dart:async';
import '../../../core/services/behavioral_service.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/firebase_service.dart';
import '../../../core/services/personalization_service.dart';
import '../../../shared/models/trust_data.dart';
import '../../authentication/providers/auth_provider.dart';

class TrustProvider with ChangeNotifier {
  late final BehavioralService _behavioralService;
  late final PersonalizationService _personalizationService;
  late final ApiService _apiService;
  late final FirebaseService _firebaseService;
  Timer? _trustUpdateTimer;
  
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
  
  Future<void> _initializeServices() async {
    await _firebaseService.initialize();
    await _personalizationService.initialize();
    _isPersonalized = !_personalizationService.isLearningPhase;
    
    // Set up behavioral service callback
    _behavioralService.setTrustScoreCallback(_handleTrustScoreUpdate);
    
    notifyListeners();
  }
  
  Future<void> startMonitoring() async {
    if (_isMonitoring) return;
    
    try {
      // Set user session info for behavioral service
      if (_authProvider?.userId != null && _authProvider?.currentSessionToken != null) {
        final userId = int.tryParse(_authProvider!.userId!) ?? 1;
        _behavioralService.setUserSession(userId, _authProvider!.currentSessionToken);
        _currentSessionToken = _authProvider!.currentSessionToken;
      }
      
      _isMonitoring = true;
      _behavioralService.startMonitoring();
      
      // Start periodic trust updates
      _trustUpdateTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
        _updateTrustWithBackend();
      });
      
      if (kDebugMode) {
        print('🎯 Trust monitoring started');
      }
      
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to start monitoring: $e');
      }
    }
    
    notifyListeners();
  }
  
  void _handleTrustScoreUpdate(double trustScore, bool mirageActivated, Map<String, dynamic> response) {
    _lastBackendResponse = response;
    _trustScore = trustScore;
    _trustLevel = _getTrustLevelFromScore(trustScore);
    _shouldShowMirage = mirageActivated;
    _isPersonalized = response['learning_phase'] == false;
    
    // Update risk factors based on backend response
    _updateRiskFactors(response);
    
    // Send Firebase notifications based on trust score and events
    _handleFirebaseNotifications(trustScore, mirageActivated, response);
    
    notifyListeners();
  }
  
  void _updateRiskFactors(Map<String, dynamic> response) {
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
    if (!_isMonitoring || _authProvider?.userId == null) return;
    
    try {
      final behavioralData = _behavioralService.generateBehavioralData();
      final userId = int.tryParse(_authProvider!.userId!) ?? 1;
      final backendData = behavioralData.toBackendFormat(userId);
      
      final result = await _apiService.predictTrustScore(backendData);
      
      if (result['success'] == true) {
        _handleTrustScoreUpdate(
          result['trust_score']?.toDouble() ?? _trustScore,
          result['mirage_activated'] == true,
          result
        );
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
      if (kDebugMode) {
        print('❌ Backend trust update failed: $e');
      }
    }
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
    _behavioralService.stopMonitoring();
    _trustUpdateTimer?.cancel();
    _trustUpdateTimer = null;
    
    if (kDebugMode) {
      print('🛑 Trust monitoring stopped');
    }
    
    notifyListeners();
  }
  
  void forceUpdateTrust() {
    _updateTrustWithBackend();
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
    
    // Send Firebase alerts
    await _firebaseService.sendTrustScoreAlert(_trustScore, _trustLevel.name);
    await _firebaseService.sendMirageActivationAlert(_trustScore, 'high');
    
    notifyListeners();
  }
  
  Future<void> resetTrust() async {
    // Reset trust score to normal for demo purposes
    _trustScore = 85.0;
    _trustLevel = TrustLevel.high;
    _riskFactors = [];
    _shouldShowMirage = false;
    
    // Send restoration alert
    await _firebaseService.sendSecurityRestoreAlert();
    
    notifyListeners();
  }
  
  // Record behavioral interactions
  void recordTap(double x, double y, double pressure) {
    _behavioralService.recordTap(x, y, pressure, const Duration(milliseconds: 100));
  }
  
  void recordSwipe(double startX, double startY, double endX, double endY, double velocity) {
    _behavioralService.recordSwipe(startX, startY, endX, endY, velocity, const Duration(milliseconds: 300));
  }
  
  @override
  void dispose() {
    stopMonitoring();
    _behavioralService.dispose();
    super.dispose();
  }
}