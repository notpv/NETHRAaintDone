import 'package:flutter/foundation.dart';
import 'dart:async';
import '../../../core/services/trust_service.dart';
import '../../../core/services/behavioral_service.dart';
import '../../../core/services/api_service.dart';
import '../../../core/services/personalization_service.dart';
import '../../../shared/models/trust_data.dart';
import '../../authentication/providers/auth_provider.dart';

class TrustProvider with ChangeNotifier {
  late final TrustService _trustService;
  late final PersonalizationService _personalizationService;
  late final ApiService _apiService;
  StreamSubscription<TrustData>? _trustSubscription;
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
  
  TrustProvider({AuthProvider? authProvider}) {
    _authProvider = authProvider;
    final behavioralService = BehavioralService();
    _apiService = authProvider?.apiService ?? ApiService();
    _trustService = TrustService(behavioralService, _apiService);
    _personalizationService = PersonalizationService();
    _initializePersonalization();
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
  
  Future<void> _initializePersonalization() async {
    await _personalizationService.initialize();
    _isPersonalized = !_personalizationService.isLearningPhase;
    notifyListeners();
  }
  
  Future<void> startMonitoring() async {
    if (_isMonitoring) return;
    
    try {
      // Create session with backend
      final sessionResult = await _apiService.createSession();
      _currentSessionToken = sessionResult['session_token'];
    } catch (e) {
      if (kDebugMode) {
        print('Failed to create session: $e');
      }
    }
    
    _isMonitoring = true;
    _trustService.startTrustMonitoring();
    
    _trustSubscription = _trustService.trustStream.listen((trustData) {
      _updateTrustScores(trustData);
      _trustLevel = trustData.trustLevel;
      _riskFactors = trustData.riskFactors;
      _shouldShowMirage = _trustScore < 50;
      
      notifyListeners();
      
      // Log security events
      if (_trustScore < 60) {
        _trustService.recordSecurityEvent('LOW_TRUST_SCORE', {
          'score': _trustScore,
          'level': _trustLevel.name,
          'factors': _riskFactors,
        });
      }
    });
    
    // Start periodic trust updates with backend
    _trustUpdateTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
      _updateTrustWithBackend();
    });
    
    notifyListeners();
  }
  
  Future<void> _updateTrustWithBackend() async {
    try {
      final behavioralData = _trustService.getLatestBehavioralData();
      if (behavioralData != null && _authProvider?.userId != null) {
        final userId = int.tryParse(_authProvider!.userId!) ?? 1;
        
        // Prepare behavioral data for backend
        final backendData = {
          'user_id': userId,
          'avg_pressure': behavioralData.averageTapPressure,
          'avg_swipe_velocity': behavioralData.averageSwipeVelocity,
          'avg_swipe_duration': behavioralData.averageTapDuration / 1000,
          'accel_stability': behavioralData.deviceTiltVariation,
          'gyro_stability': behavioralData.deviceTiltVariation * 0.8,
          'touch_frequency': behavioralData.tapCount / (behavioralData.sessionDuration / 60),
          'timestamp': behavioralData.timestamp.toIso8601String(),
        };
        
        // Get trust prediction from backend
        final result = await _apiService.predictTrustScore(backendData);
        
        if (result['success'] == true) {
          _trustScore = result['trust_score']?.toDouble() ?? _trustScore;
          _personalizedTrustScore = result['trust_score']?.toDouble() ?? _personalizedTrustScore;
          _shouldShowMirage = result['mirage_activated'] == true;
          _isPersonalized = result['learning_phase'] == false;
          
          // Update risk factors based on backend response
          if (result['security_action'] == 'maximum_security') {
            _riskFactors = ['High security threat detected', 'Behavioral anomaly'];
          } else if (result['security_action'] == 'elevated_security') {
            _riskFactors = ['Unusual behavior pattern'];
          } else {
            _riskFactors = [];
          }
          
          _trustLevel = _getTrustLevelFromScore(_trustScore);
          notifyListeners();
        }
      }
      
      // Send heartbeat if we have a session
      if (_currentSessionToken != null) {
        try {
          await _apiService.sendHeartbeat(_currentSessionToken!);
        } catch (e) {
          if (kDebugMode) {
            print('Heartbeat failed: $e');
          }
        }
      }
    } catch (e) {
      if (kDebugMode) {
        print('Backend trust update failed: $e');
      }
    }
  }
  
  TrustLevel _getTrustLevelFromScore(double score) {
    if (score >= 80) return TrustLevel.high;
    if (score >= 60) return TrustLevel.medium;
    if (score >= 40) return TrustLevel.low;
    return TrustLevel.critical;
  }
  
  Future<void> _updateTrustScores(TrustData trustData) async {
    _standardTrustScore = trustData.trustScore;
    
    // Get personalized trust score if available
    try {
      final behavioralData = _trustService.getLatestBehavioralData();
      if (behavioralData != null) {
        final result = await _personalizationService.calculatePersonalizedTrust(behavioralData);
        _personalizedTrustScore = result.personalizedTrustScore;
        _isPersonalized = !result.isLearningPhase;
        
        // Use personalized score as the main trust score
        _trustScore = _personalizedTrustScore;
      } else {
        _trustScore = _standardTrustScore;
      }
    } catch (e) {
      _trustScore = _standardTrustScore;
    }
  }
  
  void stopMonitoring() {
    if (!_isMonitoring) return;
    
    _isMonitoring = false;
    _trustService.stopTrustMonitoring();
    _trustSubscription?.cancel();
    _trustSubscription = null;
    _trustUpdateTimer?.cancel();
    _trustUpdateTimer = null;
    
    notifyListeners();
  }
  
  void forceUpdateTrust() {
    // Force an immediate trust score update with backend
    _updateTrustWithBackend();
  }
  
  void simulateThreat() {
    // Simulate a security threat for demo purposes
    _trustScore = 25.0;
    _trustLevel = TrustLevel.critical;
    _riskFactors = [
      'Suspicious tap patterns detected',
      'Unusual device movement',
      'Potential unauthorized access',
    ];
    _shouldShowMirage = true;
    
    notifyListeners();
    
    _trustService.recordSecurityEvent('SIMULATED_THREAT', {
      'score': _trustScore,
      'level': _trustLevel.name,
      'factors': _riskFactors,
    });
  }
  
  void resetTrust() {
    // Reset trust score to normal for demo purposes
    _trustScore = 85.0;
    _trustLevel = TrustLevel.high;
    _riskFactors = [];
    _shouldShowMirage = false;
    
    notifyListeners();
    
    _trustService.recordSecurityEvent('TRUST_RESET', {
      'score': _trustScore,
      'level': _trustLevel.name,
    });
  }
  
  @override
  void dispose() {
    stopMonitoring();
    super.dispose();
  }
}