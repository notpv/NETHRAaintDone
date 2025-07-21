import 'dart:async';
import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../constants/app_constants.dart';
import '../../shared/models/behavioral_data.dart';
import '../../shared/models/user_baseline.dart';

class PersonalizationService {
  static const String _baselineKey = 'user_baseline';
  static const String _adaptationCountKey = 'adaptation_count';
  static const String _learningPhaseKey = 'learning_phase';
  
  UserBaseline? _currentBaseline;
  bool _isLearningPhase = true;
  int _adaptationCount = 0;
  
  // Personalization parameters
  static const int minSamplesForBaseline = 20;
  static const int learningPhaseThreshold = 50;
  static const double adaptationRate = 0.1;
  static const double confidenceThreshold = 0.8;
  
  UserBaseline? get currentBaseline => _currentBaseline;
  bool get isLearningPhase => _isLearningPhase;
  int get adaptationCount => _adaptationCount;
  double get learningProgress => _adaptationCount / learningPhaseThreshold;
  
  Future<void> initialize() async {
    await _loadBaseline();
    await _loadLearningState();
  }
  
  Future<void> _loadBaseline() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final baselineJson = prefs.getString(_baselineKey);
      
      if (baselineJson != null) {
        _currentBaseline = UserBaseline.fromJson(baselineJson);
      } else {
        _currentBaseline = UserBaseline.createDefault();
      }
    } catch (e) {
      if (kDebugMode) {
        print('Error loading baseline: $e');
      }
      _currentBaseline = UserBaseline.createDefault();
    }
  }
  
  Future<void> _loadLearningState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _adaptationCount = prefs.getInt(_adaptationCountKey) ?? 0;
      _isLearningPhase = prefs.getBool(_learningPhaseKey) ?? true;
    } catch (e) {
      if (kDebugMode) {
        print('Error loading learning state: $e');
      }
    }
  }
  
  Future<void> _saveBaseline() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_baselineKey, _currentBaseline!.toJson());
    } catch (e) {
      if (kDebugMode) {
        print('Error saving baseline: $e');
      }
    }
  }
  
  Future<void> _saveLearningState() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_adaptationCountKey, _adaptationCount);
      await prefs.setBool(_learningPhaseKey, _isLearningPhase);
    } catch (e) {
      if (kDebugMode) {
        print('Error saving learning state: $e');
      }
    }
  }
  
  Future<PersonalizedTrustResult> calculatePersonalizedTrust(BehavioralData behavioralData) async {
    if (_currentBaseline == null) {
      await initialize();
    }
    
    // Update baseline with new data
    await _updateBaseline(behavioralData);
    
    // Calculate personalized trust score
    final personalizedScore = _calculateTrustWithPersonalization(behavioralData);
    
    // Determine if behavior is within personal thresholds
    final deviations = _calculateDeviations(behavioralData);
    final anomalies = _detectPersonalizedAnomalies(deviations);
    
    // Generate personalized recommendations
    final recommendations = _generatePersonalizedRecommendations(personalizedScore, anomalies);
    
    return PersonalizedTrustResult(
      personalizedTrustScore: personalizedScore,
      baselineTrustScore: _calculateBaseTrustScore(behavioralData),
      deviations: deviations,
      anomalies: anomalies,
      recommendations: recommendations,
      learningProgress: learningProgress,
      isLearningPhase: _isLearningPhase,
      adaptationCount: _adaptationCount,
    );
  }
  
  Future<void> _updateBaseline(BehavioralData behavioralData) async {
    if (_currentBaseline == null) return;
    
    _adaptationCount++;
    
    // Check if we should exit learning phase
    if (_isLearningPhase && _adaptationCount >= learningPhaseThreshold) {
      _isLearningPhase = false;
      await _saveLearningState();
    }
    
    // Update baseline using exponential moving average
    final alpha = _isLearningPhase ? 0.2 : adaptationRate;
    
    _currentBaseline!.updateWithNewData(behavioralData, alpha);
    
    await _saveBaseline();
    await _saveLearningState();
  }
  
  double _calculateTrustWithPersonalization(BehavioralData behavioralData) {
    if (_currentBaseline == null) return 50.0;
    
    final deviations = _calculateDeviations(behavioralData);
    
    // Base trust score
    double trustScore = 85.0;
    
    // Apply personalized penalties based on individual thresholds
    trustScore -= deviations.tapPressureDeviation * _currentBaseline!.tapPressureThreshold * 20;
    trustScore -= deviations.tapDurationDeviation * _currentBaseline!.tapDurationThreshold * 15;
    trustScore -= deviations.swipeVelocityDeviation * _currentBaseline!.swipeVelocityThreshold * 18;
    trustScore -= deviations.deviceTiltDeviation * _currentBaseline!.deviceTiltThreshold * 12;
    trustScore -= deviations.typingRhythmDeviation * _currentBaseline!.typingRhythmThreshold * 10;
    
    // Learning phase bonus (more lenient during learning)
    if (_isLearningPhase) {
      trustScore += 10.0 * (1.0 - learningProgress);
    }
    
    // Confidence bonus for well-established baselines
    if (!_isLearningPhase && _adaptationCount > learningPhaseThreshold * 2) {
      trustScore += 5.0;
    }
    
    return trustScore.clamp(0.0, 100.0);
  }
  
  double _calculateBaseTrustScore(BehavioralData behavioralData) {
    // Standard trust calculation without personalization
    double trustScore = 85.0;
    
    // Apply standard thresholds
    if (behavioralData.averageTapPressure > 1.5 || behavioralData.averageTapPressure < 0.3) {
      trustScore -= 15.0;
    }
    
    if (behavioralData.averageSwipeVelocity > 2000 || behavioralData.averageSwipeVelocity < 100) {
      trustScore -= 12.0;
    }
    
    if (behavioralData.deviceTiltVariation > 0.8) {
      trustScore -= 10.0;
    }
    
    return trustScore.clamp(0.0, 100.0);
  }
  
  BehavioralDeviations _calculateDeviations(BehavioralData behavioralData) {
    if (_currentBaseline == null) {
      return BehavioralDeviations.zero();
    }
    
    return BehavioralDeviations(
      tapPressureDeviation: _calculateNormalizedDeviation(
        behavioralData.averageTapPressure,
        _currentBaseline!.averageTapPressure,
        _currentBaseline!.tapPressureStdDev,
      ),
      tapDurationDeviation: _calculateNormalizedDeviation(
        behavioralData.averageTapDuration,
        _currentBaseline!.averageTapDuration,
        _currentBaseline!.tapDurationStdDev,
      ),
      swipeVelocityDeviation: _calculateNormalizedDeviation(
        behavioralData.averageSwipeVelocity,
        _currentBaseline!.averageSwipeVelocity,
        _currentBaseline!.swipeVelocityStdDev,
      ),
      deviceTiltDeviation: _calculateNormalizedDeviation(
        behavioralData.deviceTiltVariation,
        _currentBaseline!.averageDeviceTilt,
        _currentBaseline!.deviceTiltStdDev,
      ),
      typingRhythmDeviation: _calculateNormalizedDeviation(
        behavioralData.typingRhythm,
        _currentBaseline!.averageTypingRhythm,
        _currentBaseline!.typingRhythmStdDev,
      ),
    );
  }
  
  double _calculateNormalizedDeviation(double current, double baseline, double stdDev) {
    if (stdDev == 0) return 0.0;
    return ((current - baseline).abs() / stdDev).clamp(0.0, 5.0);
  }
  
  List<PersonalizedAnomaly> _detectPersonalizedAnomalies(BehavioralDeviations deviations) {
    final anomalies = <PersonalizedAnomaly>[];
    
    if (deviations.tapPressureDeviation > _currentBaseline!.tapPressureThreshold) {
      anomalies.add(PersonalizedAnomaly(
        type: 'tap_pressure',
        severity: _getSeverity(deviations.tapPressureDeviation),
        deviation: deviations.tapPressureDeviation,
        threshold: _currentBaseline!.tapPressureThreshold,
        message: 'Tap pressure differs from your personal pattern',
      ));
    }
    
    if (deviations.swipeVelocityDeviation > _currentBaseline!.swipeVelocityThreshold) {
      anomalies.add(PersonalizedAnomaly(
        type: 'swipe_velocity',
        severity: _getSeverity(deviations.swipeVelocityDeviation),
        deviation: deviations.swipeVelocityDeviation,
        threshold: _currentBaseline!.swipeVelocityThreshold,
        message: 'Swipe velocity differs from your personal pattern',
      ));
    }
    
    if (deviations.deviceTiltDeviation > _currentBaseline!.deviceTiltThreshold) {
      anomalies.add(PersonalizedAnomaly(
        type: 'device_tilt',
        severity: _getSeverity(deviations.deviceTiltDeviation),
        deviation: deviations.deviceTiltDeviation,
        threshold: _currentBaseline!.deviceTiltThreshold,
        message: 'Device handling differs from your personal pattern',
      ));
    }
    
    return anomalies;
  }
  
  String _getSeverity(double deviation) {
    if (deviation > 3.0) return 'critical';
    if (deviation > 2.0) return 'high';
    if (deviation > 1.5) return 'medium';
    return 'low';
  }
  
  List<String> _generatePersonalizedRecommendations(double trustScore, List<PersonalizedAnomaly> anomalies) {
    final recommendations = <String>[];
    
    if (_isLearningPhase) {
      recommendations.add('NETHRA is learning your unique behavioral patterns');
      recommendations.add('Continue using normally to improve accuracy');
    }
    
    if (trustScore < 60 && anomalies.isNotEmpty) {
      recommendations.add('Your behavior differs from your established pattern');
      for (final anomaly in anomalies) {
        recommendations.add('• ${anomaly.message}');
      }
    }
    
    if (trustScore > 80) {
      recommendations.add('Your behavior matches your personal security profile');
    }
    
    return recommendations;
  }
  
  Future<void> resetPersonalization() async {
    _currentBaseline = UserBaseline.createDefault();
    _adaptationCount = 0;
    _isLearningPhase = true;
    
    await _saveBaseline();
    await _saveLearningState();
  }
  
  Map<String, dynamic> getPersonalizationMetrics() {
    return {
      'learning_phase': _isLearningPhase,
      'adaptation_count': _adaptationCount,
      'learning_progress': learningProgress,
      'baseline_confidence': _currentBaseline?.confidence ?? 0.0,
      'personalized_thresholds': _currentBaseline?.getThresholds() ?? {},
    };
  }
}

class PersonalizedTrustResult {
  final double personalizedTrustScore;
  final double baselineTrustScore;
  final BehavioralDeviations deviations;
  final List<PersonalizedAnomaly> anomalies;
  final List<String> recommendations;
  final double learningProgress;
  final bool isLearningPhase;
  final int adaptationCount;
  
  PersonalizedTrustResult({
    required this.personalizedTrustScore,
    required this.baselineTrustScore,
    required this.deviations,
    required this.anomalies,
    required this.recommendations,
    required this.learningProgress,
    required this.isLearningPhase,
    required this.adaptationCount,
  });
}

class BehavioralDeviations {
  final double tapPressureDeviation;
  final double tapDurationDeviation;
  final double swipeVelocityDeviation;
  final double deviceTiltDeviation;
  final double typingRhythmDeviation;
  
  BehavioralDeviations({
    required this.tapPressureDeviation,
    required this.tapDurationDeviation,
    required this.swipeVelocityDeviation,
    required this.deviceTiltDeviation,
    required this.typingRhythmDeviation,
  });
  
  static BehavioralDeviations zero() {
    return BehavioralDeviations(
      tapPressureDeviation: 0.0,
      tapDurationDeviation: 0.0,
      swipeVelocityDeviation: 0.0,
      deviceTiltDeviation: 0.0,
      typingRhythmDeviation: 0.0,
    );
  }
}

class PersonalizedAnomaly {
  final String type;
  final String severity;
  final double deviation;
  final double threshold;
  final String message;
  
  PersonalizedAnomaly({
    required this.type,
    required this.severity,
    required this.deviation,
    required this.threshold,
    required this.message,
  });
}