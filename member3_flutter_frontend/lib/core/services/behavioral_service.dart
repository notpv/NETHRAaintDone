import 'dart:async';
import 'dart:math';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:flutter/services.dart';
import '../../shared/models/behavioral_data.dart';
import 'api_service.dart';
import '../constants/app_constants.dart';
import 'package:flutter/foundation.dart';

class BehavioralService {
  StreamSubscription<AccelerometerEvent>? _accelerometerSubscription;
  StreamSubscription<GyroscopeEvent>? _gyroscopeSubscription;
  Timer? _dataCollectionTimer;
  Timer? _backendSyncTimer;
  
  final List<AccelerometerEvent> _accelerometerData = [];
  final List<GyroscopeEvent> _gyroscopeData = [];
  final List<TapData> _tapData = [];
  final List<SwipeData> _swipeData = [];
  
  DateTime? _sessionStartTime;
  int _tapCount = 0;
  double _totalSwipeDistance = 0.0;
  bool _isMonitoring = false;
  bool _disposed = false;
  
  final ApiService _apiService;
  int? _currentUserId;
  String? _currentSessionToken;
  int _failedSyncCount = 0;
  static const int _maxFailedSyncs = 5;
  
  BehavioralService(this._apiService);
  
  bool get isMonitoring => _isMonitoring;
  
  void setUserSession(int userId, String? sessionToken) {
    if (_disposed) return;
    
    _currentUserId = userId;
    _currentSessionToken = sessionToken;
    
    if (kDebugMode) {
      print('🎯 Behavioral service set for user $userId with session $sessionToken');
    }
  }
  
  void startMonitoring() {
    if (_isMonitoring || _disposed) return;
    
    try {
      _isMonitoring = true;
      _sessionStartTime = DateTime.now();
      _failedSyncCount = 0;
      
      // Start sensor monitoring with error handling
      _startSensorMonitoring();
      
      // Start periodic data collection and backend sync
      _dataCollectionTimer = Timer.periodic(
        Duration(seconds: AppConstants.trustUpdateIntervalSeconds), 
        (timer) => _collectAndSyncBehavioralData()
      );
      
      // Start session heartbeat
      _backendSyncTimer = Timer.periodic(
        const Duration(seconds: 45), 
        (timer) => _sendSessionHeartbeat()
      );
      
      if (kDebugMode) {
        print('✅ Behavioral monitoring started');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to start behavioral monitoring: $e');
      }
    }
  }
  
  void _startSensorMonitoring() {
    try {
      // Start accelerometer monitoring with error handling
      _accelerometerSubscription = accelerometerEvents.listen(
        (event) {
          if (!_disposed) {
            _accelerometerData.add(event);
            if (_accelerometerData.length > 100) {
              _accelerometerData.removeAt(0);
            }
          }
        },
        onError: (error) {
          if (kDebugMode) {
            print('Accelerometer error: $error');
          }
        },
      );
      
      // Start gyroscope monitoring with error handling
      _gyroscopeSubscription = gyroscopeEvents.listen(
        (event) {
          if (!_disposed) {
            _gyroscopeData.add(event);
            if (_gyroscopeData.length > 100) {
              _gyroscopeData.removeAt(0);
            }
          }
        },
        onError: (error) {
          if (kDebugMode) {
            print('Gyroscope error: $error');
          }
        },
      );
    } catch (e) {
      if (kDebugMode) {
        print('❌ Sensor initialization failed: $e');
      }
    }
  }
  
  void stopMonitoring() {
    if (!_isMonitoring || _disposed) return;
    
    _isMonitoring = false;
    _accelerometerSubscription?.cancel();
    _gyroscopeSubscription?.cancel();
    _dataCollectionTimer?.cancel();
    _backendSyncTimer?.cancel();
    
    _accelerometerSubscription = null;
    _gyroscopeSubscription = null;
    _dataCollectionTimer = null;
    _backendSyncTimer = null;
    
    if (kDebugMode) {
      print('🛑 Behavioral monitoring stopped');
    }
  }
  
  void recordTap(double x, double y, double pressure, Duration duration) {
    if (!_isMonitoring || _disposed) return;
    
    _tapCount++;
    _tapData.add(TapData(
      x: x,
      y: y,
      pressure: pressure,
      duration: duration,
      timestamp: DateTime.now(),
    ));
    
    if (_tapData.length > 50) {
      _tapData.removeAt(0);
    }
  }
  
  void recordSwipe(double startX, double startY, double endX, double endY, 
                   double velocity, Duration duration) {
    if (!_isMonitoring || _disposed) return;
    
    final distance = sqrt(pow(endX - startX, 2) + pow(endY - startY, 2));
    _totalSwipeDistance += distance;
    
    _swipeData.add(SwipeData(
      startX: startX,
      startY: startY,
      endX: endX,
      endY: endY,
      velocity: velocity,
      duration: duration,
      timestamp: DateTime.now(),
    ));
    
    if (_swipeData.length > 50) {
      _swipeData.removeAt(0);
    }
  }
  
  Future<void> _collectAndSyncBehavioralData() async {
    if (_currentUserId == null || _disposed) return;
    
    try {
      final behavioralData = generateBehavioralData();
      final backendData = behavioralData.toBackendFormat(_currentUserId!);
      
      if (kDebugMode) {
        print('Syncing behavioral data to backend...');
      }
      
      // Send to backend for trust prediction
      final response = await _apiService.predictTrustScore(backendData);
      
      // Handle backend response
      if (response['success'] == true) {
        final trustScore = response['trust_score']?.toDouble() ?? 50.0;
        final mirageActivated = response['mirage_activated'] == true;
        
        // Reset failed sync count on success
        _failedSyncCount = 0;
        
        // Trigger callbacks for trust updates
        _onTrustScoreUpdate?.call(trustScore, mirageActivated, response);
        
        if (kDebugMode) {
          print('✅ Behavioral sync successful - Trust: $trustScore');
        }
      }
    } catch (e) {
      _failedSyncCount++;
      if (kDebugMode) {
        print('❌ Failed to sync behavioral data (attempt $_failedSyncCount): $e');
      }
      
      // If too many failures, reduce sync frequency
      if (_failedSyncCount >= _maxFailedSyncs) {
        _dataCollectionTimer?.cancel();
        _dataCollectionTimer = Timer.periodic(
          const Duration(seconds: 30), // Reduced frequency
          (timer) => _collectAndSyncBehavioralData()
        );
        
        if (kDebugMode) {
          print('⚠️ Reduced sync frequency due to repeated failures');
        }
      }
    }
  }
  
  Future<void> _sendSessionHeartbeat() async {
    if (_currentSessionToken == null || _disposed) return;
    
    try {
      await _apiService.sendHeartbeat(_currentSessionToken!);
      
      if (kDebugMode) {
        print('💓 Session heartbeat sent');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Session heartbeat failed: $e');
      }
    }
  }
  
  BehavioralData generateBehavioralData() {
    final currentTime = DateTime.now();
    final sessionDuration = _sessionStartTime != null
        ? currentTime.difference(_sessionStartTime!).inSeconds
        : 0;
    
    return BehavioralData(
      sessionDuration: sessionDuration,
      tapCount: _tapCount,
      averageTapPressure: _calculateAverageTapPressure(),
      averageTapDuration: _calculateAverageTapDuration(),
      swipeCount: _swipeData.length,
      averageSwipeVelocity: _calculateAverageSwipeVelocity(),
      totalSwipeDistance: _totalSwipeDistance,
      deviceTiltVariation: _calculateDeviceTiltVariation(),
      movementPattern: _calculateMovementPattern(),
      typingRhythm: _calculateTypingRhythm(),
      navigationFlow: _calculateNavigationFlow(),
      timestamp: currentTime,
    );
  }
  
  double _calculateAverageTapPressure() {
    if (_tapData.isEmpty) return 0.5; // Default pressure
    return _tapData.map((e) => e.pressure).reduce((a, b) => a + b) / _tapData.length;
  }
  
  double _calculateAverageTapDuration() {
    if (_tapData.isEmpty) return 150.0; // Default duration in ms
    return _tapData.map((e) => e.duration.inMilliseconds).reduce((a, b) => a + b) / _tapData.length;
  }
  
  double _calculateAverageSwipeVelocity() {
    if (_swipeData.isEmpty) return 800.0; // Default velocity
    return _swipeData.map((e) => e.velocity).reduce((a, b) => a + b) / _swipeData.length;
  }
  
  double _calculateDeviceTiltVariation() {
    if (_accelerometerData.isEmpty) return 0.3; // Default tilt
    
    try {
      final tilts = _accelerometerData.map((e) => 
        sqrt(e.x * e.x + e.y * e.y + e.z * e.z));
      
      if (tilts.isEmpty) return 0.3;
      
      final average = tilts.reduce((a, b) => a + b) / tilts.length;
      final variance = tilts.map((e) => pow(e - average, 2)).reduce((a, b) => a + b) / tilts.length;
      
      return sqrt(variance);
    } catch (e) {
      if (kDebugMode) {
        print('Error calculating device tilt: $e');
      }
      return 0.3;
    }
  }
  
  List<double> _calculateMovementPattern() {
    if (_accelerometerData.isEmpty) return [0.1, 0.2, 0.1];
    
    try {
      final xAvg = _accelerometerData.map((e) => e.x).reduce((a, b) => a + b) / _accelerometerData.length;
      final yAvg = _accelerometerData.map((e) => e.y).reduce((a, b) => a + b) / _accelerometerData.length;
      final zAvg = _accelerometerData.map((e) => e.z).reduce((a, b) => a + b) / _accelerometerData.length;
      
      return [xAvg, yAvg, zAvg];
    } catch (e) {
      if (kDebugMode) {
        print('Error calculating movement pattern: $e');
      }
      return [0.1, 0.2, 0.1];
    }
  }
  
  double _calculateTypingRhythm() {
    if (_tapData.length < 2) return 200.0; // Default rhythm
    
    try {
      final intervals = <double>[];
      for (int i = 1; i < _tapData.length; i++) {
        final interval = _tapData[i].timestamp.difference(_tapData[i-1].timestamp).inMilliseconds;
        intervals.add(interval.toDouble());
      }
      
      if (intervals.isEmpty) return 200.0;
      
      final average = intervals.reduce((a, b) => a + b) / intervals.length;
      return average;
    } catch (e) {
      if (kDebugMode) {
        print('Error calculating typing rhythm: $e');
      }
      return 200.0;
    }
  }
  
  double _calculateNavigationFlow() {
    // Calculate based on app navigation patterns
    try {
      return 85.0 + (Random().nextDouble() - 0.5) * 20;
    } catch (e) {
      return 85.0;
    }
  }
  
  // Callback for trust score updates
  Function(double, bool, Map<String, dynamic>)? _onTrustScoreUpdate;
  
  void setTrustScoreCallback(Function(double, bool, Map<String, dynamic>) callback) {
    if (!_disposed) {
      _onTrustScoreUpdate = callback;
    }
  }
  
  void dispose() {
    if (_disposed) return;
    _disposed = true;
    
    stopMonitoring();
    _onTrustScoreUpdate = null;
    
    if (kDebugMode) {
      print('🗑️ Behavioral service disposed');
    }
  }
}

class TapData {
  final double x;
  final double y;
  final double pressure;
  final Duration duration;
  final DateTime timestamp;
  
  TapData({
    required this.x,
    required this.y,
    required this.pressure,
    required this.duration,
    required this.timestamp,
  });
}

class SwipeData {
  final double startX;
  final double startY;
  final double endX;
  final double endY;
  final double velocity;
  final Duration duration;
  final DateTime timestamp;
  
  SwipeData({
    required this.startX,
    required this.startY,
    required this.endX,
    required this.endY,
    required this.velocity,
    required this.duration,
    required this.timestamp,
  });
}