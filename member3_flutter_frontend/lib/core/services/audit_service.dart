import 'package:flutter/foundation.dart';
import 'dart:async';

class AuditService {
  static final AuditService _instance = AuditService._internal();
  factory AuditService() => _instance;
  AuditService._internal();
  
  final List<AuditEvent> _events = [];
  final StreamController<AuditEvent> _eventController = StreamController<AuditEvent>.broadcast();
  
  Stream<AuditEvent> get eventStream => _eventController.stream;
  
  void logSecurityEvent({
    required String eventType,
    required int userId,
    required Map<String, dynamic> details,
    String? sessionId,
    SecurityLevel level = SecurityLevel.medium,
  }) {
    final event = AuditEvent(
      id: 'audit_${DateTime.now().millisecondsSinceEpoch}',
      eventType: eventType,
      userId: userId,
      sessionId: sessionId,
      timestamp: DateTime.now(),
      level: level,
      details: details,
      source: 'flutter_frontend',
    );
    
    _events.insert(0, event);
    if (_events.length > 1000) {
      _events.removeLast();
    }
    
    _eventController.add(event);
    
    if (kDebugMode) {
      print('📋 Audit: $eventType for user $userId (${level.name})');
    }
  }
  
  void logMirageActivation({
    required int userId,
    required double trustScore,
    required String intensity,
    String? sessionId,
  }) {
    logSecurityEvent(
      eventType: 'mirage_activation',
      userId: userId,
      sessionId: sessionId,
      level: SecurityLevel.high,
      details: {
        'trust_score': trustScore,
        'intensity': intensity,
        'activation_time': DateTime.now().toIso8601String(),
        'trigger_reason': 'low_trust_score',
      },
    );
  }
  
  void logCriticalThreatLogout({
    required int userId,
    required double trustScore,
    required String reason,
    String? sessionId,
  }) {
    logSecurityEvent(
      eventType: 'critical_threat_logout',
      userId: userId,
      sessionId: sessionId,
      level: SecurityLevel.critical,
      details: {
        'trust_score': trustScore,
        'logout_reason': reason,
        'logout_time': DateTime.now().toIso8601String(),
        'auto_logout': true,
      },
    );
  }
  
  void logTrustScoreUpdate({
    required int userId,
    required double oldScore,
    required double newScore,
    required Map<String, dynamic> behavioralData,
    String? sessionId,
  }) {
    logSecurityEvent(
      eventType: 'trust_score_update',
      userId: userId,
      sessionId: sessionId,
      level: newScore < 40 ? SecurityLevel.high : SecurityLevel.low,
      details: {
        'old_score': oldScore,
        'new_score': newScore,
        'score_change': newScore - oldScore,
        'behavioral_data': behavioralData,
        'update_time': DateTime.now().toIso8601String(),
      },
    );
  }
  
  void logUserAuthentication({
    required int userId,
    required String username,
    required bool success,
    String? failureReason,
  }) {
    logSecurityEvent(
      eventType: 'user_authentication',
      userId: userId,
      level: success ? SecurityLevel.low : SecurityLevel.medium,
      details: {
        'username': username,
        'success': success,
        'failure_reason': failureReason,
        'auth_time': DateTime.now().toIso8601String(),
        'auth_method': 'username_password',
      },
    );
  }
  
  List<AuditEvent> getEvents({
    int? userId,
    String? eventType,
    SecurityLevel? level,
    int limit = 100,
  }) {
    var filteredEvents = _events.where((event) {
      if (userId != null && event.userId != userId) return false;
      if (eventType != null && event.eventType != eventType) return false;
      if (level != null && event.level != level) return false;
      return true;
    }).take(limit).toList();
    
    return filteredEvents;
  }
  
  Map<String, dynamic> getSecuritySummary({int? userId}) {
    final events = userId != null 
        ? _events.where((e) => e.userId == userId).toList()
        : _events;
    
    final now = DateTime.now();
    final last24Hours = events.where((e) => 
        now.difference(e.timestamp).inHours < 24).toList();
    
    return {
      'total_events': events.length,
      'events_last_24h': last24Hours.length,
      'critical_events': events.where((e) => e.level == SecurityLevel.critical).length,
      'mirage_activations': events.where((e) => e.eventType == 'mirage_activation').length,
      'trust_updates': events.where((e) => e.eventType == 'trust_score_update').length,
      'last_event': events.isNotEmpty ? events.first.timestamp.toIso8601String() : null,
    };
  }
  
  void dispose() {
    _eventController.close();
  }
}

class AuditEvent {
  final String id;
  final String eventType;
  final int userId;
  final String? sessionId;
  final DateTime timestamp;
  final SecurityLevel level;
  final Map<String, dynamic> details;
  final String source;
  
  AuditEvent({
    required this.id,
    required this.eventType,
    required this.userId,
    this.sessionId,
    required this.timestamp,
    required this.level,
    required this.details,
    required this.source,
  });
  
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'event_type': eventType,
      'user_id': userId,
      'session_id': sessionId,
      'timestamp': timestamp.toIso8601String(),
      'level': level.name,
      'details': details,
      'source': source,
    };
  }
}

enum SecurityLevel {
  low,
  medium,
  high,
  critical,
}