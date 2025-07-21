import 'dart:convert';
import 'dart:math';
import 'behavioral_data.dart';

class UserBaseline {
  double averageTapPressure;
  double tapPressureStdDev;
  double tapPressureThreshold;
  
  double averageTapDuration;
  double tapDurationStdDev;
  double tapDurationThreshold;
  
  double averageSwipeVelocity;
  double swipeVelocityStdDev;
  double swipeVelocityThreshold;
  
  double averageDeviceTilt;
  double deviceTiltStdDev;
  double deviceTiltThreshold;
  
  double averageTypingRhythm;
  double typingRhythmStdDev;
  double typingRhythmThreshold;
  
  int sampleCount;
  double confidence;
  DateTime lastUpdated;
  
  UserBaseline({
    required this.averageTapPressure,
    required this.tapPressureStdDev,
    required this.tapPressureThreshold,
    required this.averageTapDuration,
    required this.tapDurationStdDev,
    required this.tapDurationThreshold,
    required this.averageSwipeVelocity,
    required this.swipeVelocityStdDev,
    required this.swipeVelocityThreshold,
    required this.averageDeviceTilt,
    required this.deviceTiltStdDev,
    required this.deviceTiltThreshold,
    required this.averageTypingRhythm,
    required this.typingRhythmStdDev,
    required this.typingRhythmThreshold,
    required this.sampleCount,
    required this.confidence,
    required this.lastUpdated,
  });
  
  factory UserBaseline.createDefault() {
    return UserBaseline(
      averageTapPressure: 0.8,
      tapPressureStdDev: 0.2,
      tapPressureThreshold: 2.0,
      averageTapDuration: 150.0,
      tapDurationStdDev: 50.0,
      tapDurationThreshold: 2.0,
      averageSwipeVelocity: 800.0,
      swipeVelocityStdDev: 200.0,
      swipeVelocityThreshold: 2.0,
      averageDeviceTilt: 0.3,
      deviceTiltStdDev: 0.1,
      deviceTiltThreshold: 2.0,
      averageTypingRhythm: 200.0,
      typingRhythmStdDev: 80.0,
      typingRhythmThreshold: 2.0,
      sampleCount: 0,
      confidence: 0.0,
      lastUpdated: DateTime.now(),
    );
  }
  
  void updateWithNewData(BehavioralData data, double alpha) {
    sampleCount++;
    
    // Update averages using exponential moving average
    averageTapPressure = _updateAverage(averageTapPressure, data.averageTapPressure, alpha);
    averageTapDuration = _updateAverage(averageTapDuration, data.averageTapDuration, alpha);
    averageSwipeVelocity = _updateAverage(averageSwipeVelocity, data.averageSwipeVelocity, alpha);
    averageDeviceTilt = _updateAverage(averageDeviceTilt, data.deviceTiltVariation, alpha);
    averageTypingRhythm = _updateAverage(averageTypingRhythm, data.typingRhythm, alpha);
    
    // Update standard deviations
    tapPressureStdDev = _updateStdDev(tapPressureStdDev, data.averageTapPressure, averageTapPressure, alpha);
    tapDurationStdDev = _updateStdDev(tapDurationStdDev, data.averageTapDuration, averageTapDuration, alpha);
    swipeVelocityStdDev = _updateStdDev(swipeVelocityStdDev, data.averageSwipeVelocity, averageSwipeVelocity, alpha);
    deviceTiltStdDev = _updateStdDev(deviceTiltStdDev, data.deviceTiltVariation, averageDeviceTilt, alpha);
    typingRhythmStdDev = _updateStdDev(typingRhythmStdDev, data.typingRhythm, averageTypingRhythm, alpha);
    
    // Adapt thresholds based on user's natural variation
    _adaptThresholds();
    
    // Update confidence
    confidence = min(sampleCount / 50.0, 1.0);
    
    lastUpdated = DateTime.now();
  }
  
  double _updateAverage(double currentAvg, double newValue, double alpha) {
    return alpha * newValue + (1 - alpha) * currentAvg;
  }
  
  double _updateStdDev(double currentStdDev, double newValue, double currentAvg, double alpha) {
    final deviation = (newValue - currentAvg).abs();
    return alpha * deviation + (1 - alpha) * currentStdDev;
  }
  
  void _adaptThresholds() {
    // Adaptive thresholds based on user's natural variation
    // Users with naturally high variation get higher thresholds
    tapPressureThreshold = max(1.5, min(3.0, 1.5 + tapPressureStdDev * 2));
    tapDurationThreshold = max(1.5, min(3.0, 1.5 + tapDurationStdDev / 50.0));
    swipeVelocityThreshold = max(1.5, min(3.0, 1.5 + swipeVelocityStdDev / 200.0));
    deviceTiltThreshold = max(1.5, min(3.0, 1.5 + deviceTiltStdDev * 10));
    typingRhythmThreshold = max(1.5, min(3.0, 1.5 + typingRhythmStdDev / 100.0));
  }
  
  Map<String, dynamic> getThresholds() {
    return {
      'tap_pressure': tapPressureThreshold,
      'tap_duration': tapDurationThreshold,
      'swipe_velocity': swipeVelocityThreshold,
      'device_tilt': deviceTiltThreshold,
      'typing_rhythm': typingRhythmThreshold,
    };
  }
  
  String toJson() {
    return jsonEncode({
      'averageTapPressure': averageTapPressure,
      'tapPressureStdDev': tapPressureStdDev,
      'tapPressureThreshold': tapPressureThreshold,
      'averageTapDuration': averageTapDuration,
      'tapDurationStdDev': tapDurationStdDev,
      'tapDurationThreshold': tapDurationThreshold,
      'averageSwipeVelocity': averageSwipeVelocity,
      'swipeVelocityStdDev': swipeVelocityStdDev,
      'swipeVelocityThreshold': swipeVelocityThreshold,
      'averageDeviceTilt': averageDeviceTilt,
      'deviceTiltStdDev': deviceTiltStdDev,
      'deviceTiltThreshold': deviceTiltThreshold,
      'averageTypingRhythm': averageTypingRhythm,
      'typingRhythmStdDev': typingRhythmStdDev,
      'typingRhythmThreshold': typingRhythmThreshold,
      'sampleCount': sampleCount,
      'confidence': confidence,
      'lastUpdated': lastUpdated.toIso8601String(),
    });
  }
  
  factory UserBaseline.fromJson(String jsonStr) {
    final json = jsonDecode(jsonStr);
    return UserBaseline(
      averageTapPressure: json['averageTapPressure']?.toDouble() ?? 0.8,
      tapPressureStdDev: json['tapPressureStdDev']?.toDouble() ?? 0.2,
      tapPressureThreshold: json['tapPressureThreshold']?.toDouble() ?? 2.0,
      averageTapDuration: json['averageTapDuration']?.toDouble() ?? 150.0,
      tapDurationStdDev: json['tapDurationStdDev']?.toDouble() ?? 50.0,
      tapDurationThreshold: json['tapDurationThreshold']?.toDouble() ?? 2.0,
      averageSwipeVelocity: json['averageSwipeVelocity']?.toDouble() ?? 800.0,
      swipeVelocityStdDev: json['swipeVelocityStdDev']?.toDouble() ?? 200.0,
      swipeVelocityThreshold: json['swipeVelocityThreshold']?.toDouble() ?? 2.0,
      averageDeviceTilt: json['averageDeviceTilt']?.toDouble() ?? 0.3,
      deviceTiltStdDev: json['deviceTiltStdDev']?.toDouble() ?? 0.1,
      deviceTiltThreshold: json['deviceTiltThreshold']?.toDouble() ?? 2.0,
      averageTypingRhythm: json['averageTypingRhythm']?.toDouble() ?? 200.0,
      typingRhythmStdDev: json['typingRhythmStdDev']?.toDouble() ?? 80.0,
      typingRhythmThreshold: json['typingRhythmThreshold']?.toDouble() ?? 2.0,
      sampleCount: json['sampleCount'] ?? 0,
      confidence: json['confidence']?.toDouble() ?? 0.0,
      lastUpdated: DateTime.parse(json['lastUpdated'] ?? DateTime.now().toIso8601String()),
    );
  }
}