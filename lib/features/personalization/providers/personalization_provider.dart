import 'package:flutter/foundation.dart';
import '../../../core/services/personalization_service.dart';
import '../../../shared/models/behavioral_data.dart';
import '../screens/personalization_demo_screen.dart';

class PersonalizationProvider with ChangeNotifier {
  final PersonalizationService _personalizationService;
  
  double _learningProgress = 0.0;
  double _baselineConfidence = 0.0;
  int _adaptationCount = 0;
  bool _isLearningPhase = true;
  
  double _standardTrustScore = 0.0;
  double _personalizedTrustScore = 0.0;
  
  PersonalizationProvider(this._personalizationService);
  
  double get learningProgress => _learningProgress;
  double get baselineConfidence => _baselineConfidence;
  int get adaptationCount => _adaptationCount;
  bool get isLearningPhase => _isLearningPhase;
  double get standardTrustScore => _standardTrustScore;
  double get personalizedTrustScore => _personalizedTrustScore;
  
  Future<void> initialize() async {
    await _personalizationService.initialize();
    _updateMetrics();
  }
  
  void _updateMetrics() {
    final metrics = _personalizationService.getPersonalizationMetrics();
    _learningProgress = metrics['learning_progress'] ?? 0.0;
    _baselineConfidence = metrics['baseline_confidence'] ?? 0.0;
    _adaptationCount = metrics['adaptation_count'] ?? 0;
    _isLearningPhase = metrics['learning_phase'] ?? true;
    notifyListeners();
  }
  
  void setCurrentProfile(UserProfile profile) {
    // This would typically update the personalization service with the profile
    notifyListeners();
  }
  
  Future<void> runPersonalizationComparison(UserProfile profile) async {
    // Simulate behavioral data based on user profile
    final behavioralData = BehavioralData(
      sessionDuration: 300,
      tapCount: 25,
      averageTapPressure: profile.tapPressure,
      averageTapDuration: 150.0,
      swipeCount: 10,
      averageSwipeVelocity: profile.swipeVelocity,
      totalSwipeDistance: 2000.0,
      deviceTiltVariation: profile.deviceTilt,
      movementPattern: [0.1, 0.2, 0.1],
      typingRhythm: 200.0,
      navigationFlow: 85.0,
      timestamp: DateTime.now(),
    );
    
    // Calculate personalized trust result
    final result = await _personalizationService.calculatePersonalizedTrust(behavioralData);
    
    _personalizedTrustScore = result.personalizedTrustScore;
    _standardTrustScore = result.baselineTrustScore;
    
    _updateMetrics();
    notifyListeners();
  }
  
  Future<void> simulateLearningPhase(UserProfile profile) async {
    // Simulate multiple behavioral data points to show learning
    for (int i = 0; i < 10; i++) {
      final behavioralData = BehavioralData(
        sessionDuration: 200 + i * 20,
        tapCount: 20 + i * 2,
        averageTapPressure: profile.tapPressure + (i * 0.05 - 0.25),
        averageTapDuration: 150.0 + (i * 10 - 50),
        swipeCount: 8 + i,
        averageSwipeVelocity: profile.swipeVelocity + (i * 50 - 250),
        totalSwipeDistance: 1800.0 + i * 100,
        deviceTiltVariation: profile.deviceTilt + (i * 0.02 - 0.1),
        movementPattern: [0.1, 0.2, 0.1],
        typingRhythm: 200.0 + (i * 20 - 100),
        navigationFlow: 80.0 + i * 2,
        timestamp: DateTime.now().subtract(Duration(minutes: 10 - i)),
      );
      
      await _personalizationService.calculatePersonalizedTrust(behavioralData);
      
      // Update UI every few iterations
      if (i % 3 == 0) {
        _updateMetrics();
        notifyListeners();
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }
    
    _updateMetrics();
    notifyListeners();
  }
  
  Future<void> resetPersonalization() async {
    await _personalizationService.resetPersonalization();
    _standardTrustScore = 0.0;
    _personalizedTrustScore = 0.0;
    _updateMetrics();
    notifyListeners();
  }
}