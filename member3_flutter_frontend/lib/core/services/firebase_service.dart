import 'dart:async';
import 'package:flutter/foundation.dart';

class FirebaseService {
  static final FirebaseService _instance = FirebaseService._internal();
  factory FirebaseService() => _instance;
  FirebaseService._internal();
  
  bool _isInitialized = false;
  final StreamController<FirebaseNotification> _notificationController = 
      StreamController<FirebaseNotification>.broadcast();
  
  Stream<FirebaseNotification> get notificationStream => _notificationController.stream;
  
  Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      // Simulated Firebase initialization for demo
      await Future.delayed(const Duration(milliseconds: 500));
      _isInitialized = true;
      
      if (kDebugMode) {
        print('🔥 Firebase Service initialized successfully (Demo Mode)');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Firebase initialization failed: $e');
      }
    }
  }
  
  Future<void> sendTamperAlert(Map<String, dynamic> tamperData) async {
    if (!_isInitialized) await initialize();
    
    final notification = FirebaseNotification(
      id: 'tamper_${DateTime.now().millisecondsSinceEpoch}',
      title: '🚨 Security Alert',
      body: 'Potential tampering detected on your device',
      type: NotificationType.tamperDetection,
      priority: NotificationPriority.critical,
      data: tamperData,
      timestamp: DateTime.now(),
    );
    
    _notificationController.add(notification);
    
    if (kDebugMode) {
      print('🚨 Tamper alert sent: ${notification.title}');
    }
  }
  
  Future<void> sendSessionLockAlert(String reason) async {
    if (!_isInitialized) await initialize();
    
    final notification = FirebaseNotification(
      id: 'session_lock_${DateTime.now().millisecondsSinceEpoch}',
      title: '🔒 Session Locked',
      body: 'Your session has been locked due to: $reason',
      type: NotificationType.sessionLock,
      priority: NotificationPriority.high,
      data: {'reason': reason, 'timestamp': DateTime.now().toIso8601String()},
      timestamp: DateTime.now(),
    );
    
    _notificationController.add(notification);
    
    if (kDebugMode) {
      print('🔒 Session lock alert sent: $reason');
    }
  }
  
  Future<void> sendMirageActivationAlert(double trustScore, String intensity) async {
    if (!_isInitialized) await initialize();
    
    final notification = FirebaseNotification(
      id: 'mirage_${DateTime.now().millisecondsSinceEpoch}',
      title: '🎭 Security Mode Activated',
      body: 'Enhanced security measures are now active',
      type: NotificationType.mirageActivation,
      priority: NotificationPriority.high,
      data: {
        'trust_score': trustScore,
        'intensity': intensity,
        'timestamp': DateTime.now().toIso8601String()
      },
      timestamp: DateTime.now(),
    );
    
    _notificationController.add(notification);
    
    if (kDebugMode) {
      print('🎭 Mirage activation alert sent: Trust Score $trustScore');
    }
  }
  
  Future<void> sendTrustScoreAlert(double trustScore, String level) async {
    if (!_isInitialized) await initialize();
    
    if (trustScore < 40) {
      final notification = FirebaseNotification(
        id: 'trust_${DateTime.now().millisecondsSinceEpoch}',
        title: '⚠️ Low Trust Score',
        body: 'Your behavioral patterns seem unusual. Trust score: ${trustScore.toStringAsFixed(1)}',
        type: NotificationType.trustScore,
        priority: NotificationPriority.medium,
        data: {
          'trust_score': trustScore,
          'level': level,
          'timestamp': DateTime.now().toIso8601String()
        },
        timestamp: DateTime.now(),
      );
      
      _notificationController.add(notification);
      
      if (kDebugMode) {
        print('⚠️ Trust score alert sent: $trustScore');
      }
    }
  }
  
  Future<void> sendSecurityRestoreAlert() async {
    if (!_isInitialized) await initialize();
    
    final notification = FirebaseNotification(
      id: 'restore_${DateTime.now().millisecondsSinceEpoch}',
      title: '✅ Security Restored',
      body: 'Your account access has been restored to normal',
      type: NotificationType.securityRestore,
      priority: NotificationPriority.medium,
      data: {'timestamp': DateTime.now().toIso8601String()},
      timestamp: DateTime.now(),
    );
    
    _notificationController.add(notification);
    
    if (kDebugMode) {
      print('✅ Security restore alert sent');
    }
  }
  
  Future<void> sendPersonalizationUpdate(int sessionCount, double learningProgress) async {
    if (!_isInitialized) await initialize();
    
    if (sessionCount == 5 || sessionCount == 10 || sessionCount == 20) {
      final notification = FirebaseNotification(
        id: 'learning_${DateTime.now().millisecondsSinceEpoch}',
        title: '🧠 Learning Progress',
        body: 'NETHRA has completed $sessionCount learning sessions (${(learningProgress * 100).toInt()}% complete)',
        type: NotificationType.learningProgress,
        priority: NotificationPriority.low,
        data: {
          'session_count': sessionCount,
          'learning_progress': learningProgress,
          'timestamp': DateTime.now().toIso8601String()
        },
        timestamp: DateTime.now(),
      );
      
      _notificationController.add(notification);
      
      if (kDebugMode) {
        print('🧠 Learning progress alert sent: $sessionCount sessions');
      }
    }
  }
  
  void dispose() {
    if (!_notificationController.isClosed) {
      _notificationController.close();
    }


    _notificationController.close();
  }
}

class FirebaseNotification {
  final String id;
  final String title;
  final String body;
  final NotificationType type;
  final NotificationPriority priority;
  final Map<String, dynamic> data;
  final DateTime timestamp;
  
  FirebaseNotification({
    required this.id,
    required this.title,
    required this.body,
    required this.type,
    required this.priority,
    required this.data,
    required this.timestamp,
  });
}

enum NotificationType {
  tamperDetection,
  sessionLock,
  mirageActivation,
  trustScore,
  securityRestore,
  learningProgress,
}

enum NotificationPriority {
  low,
  medium,
  high,
  critical,
}