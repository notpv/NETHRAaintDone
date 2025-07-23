import 'package:flutter/foundation.dart';
import 'dart:async';

class EmailAlertService {
  static final EmailAlertService _instance = EmailAlertService._internal();
  factory EmailAlertService() => _instance;
  EmailAlertService._internal();
  
  bool _isInitialized = false;
  final List<EmailAlert> _alertHistory = [];
  
  Future<void> initialize() async {
    if (_isInitialized) return;
    
    try {
      // Simulated email service initialization
      await Future.delayed(const Duration(milliseconds: 300));
      _isInitialized = true;
      
      if (kDebugMode) {
        print('📧 Email Alert Service initialized');
      }
    } catch (e) {
      if (kDebugMode) {
        print('❌ Email Alert Service initialization failed: $e');
      }
    }
  }
  
  Future<bool> sendMirageActivationAlert({
    required String userEmail,
    required int userId,
    required double trustScore,
    required String intensity,
  }) async {
    if (!_isInitialized) await initialize();
    
    try {
      final alert = EmailAlert(
        id: 'mirage_${DateTime.now().millisecondsSinceEpoch}',
        type: EmailAlertType.mirageActivation,
        recipient: userEmail,
        subject: '🚨 NETHRA Security Alert - Account Protection Activated',
        body: _generateMirageAlertBody(userId, trustScore, intensity),
        timestamp: DateTime.now(),
        userId: userId,
        metadata: {
          'trust_score': trustScore,
          'intensity': intensity,
          'alert_type': 'mirage_activation',
        },
      );
      
      // Simulate email sending
      await _simulateEmailSending(alert);
      
      _alertHistory.insert(0, alert);
      if (_alertHistory.length > 100) {
        _alertHistory.removeLast();
      }
      
      if (kDebugMode) {
        print('📧 Mirage activation alert sent to $userEmail');
      }
      
      return true;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to send mirage activation alert: $e');
      }
      return false;
    }
  }
  
  Future<bool> sendCriticalThreatAlert({
    required String userEmail,
    required int userId,
    required double trustScore,
    required String reason,
  }) async {
    if (!_isInitialized) await initialize();
    
    try {
      final alert = EmailAlert(
        id: 'critical_${DateTime.now().millisecondsSinceEpoch}',
        type: EmailAlertType.criticalThreat,
        recipient: userEmail,
        subject: '🚨 URGENT: NETHRA Security Alert - Account Access Terminated',
        body: _generateCriticalThreatAlertBody(userId, trustScore, reason),
        timestamp: DateTime.now(),
        userId: userId,
        metadata: {
          'trust_score': trustScore,
          'reason': reason,
          'alert_type': 'critical_threat',
        },
      );
      
      await _simulateEmailSending(alert);
      
      _alertHistory.insert(0, alert);
      if (_alertHistory.length > 100) {
        _alertHistory.removeLast();
      }
      
      if (kDebugMode) {
        print('📧 Critical threat alert sent to $userEmail');
      }
      
      return true;
    } catch (e) {
      if (kDebugMode) {
        print('❌ Failed to send critical threat alert: $e');
      }
      return false;
    }
  }
  
  Future<void> _simulateEmailSending(EmailAlert alert) async {
    // Simulate network delay for email sending
    await Future.delayed(const Duration(milliseconds: 500));
    
    // In a real implementation, this would integrate with:
    // - SendGrid, AWS SES, or similar email service
    // - SMTP server
    // - Email template engine
    
    if (kDebugMode) {
      print('📧 Email sent: ${alert.subject} to ${alert.recipient}');
    }
  }
  
  String _generateMirageAlertBody(int userId, double trustScore, String intensity) {
    return '''
Dear NETHRA Banking Customer,

We have detected unusual activity on your account and have activated enhanced security measures to protect your funds.

Security Details:
- Account ID: $userId
- Trust Score: ${trustScore.toStringAsFixed(1)}%
- Security Level: $intensity
- Time: ${DateTime.now().toString().substring(0, 19)}

What happened?
Our AI-powered behavioral authentication system detected patterns that don't match your usual interaction style. As a precaution, we've activated a protective interface to safeguard your account.

What should you do?
1. If this was you, complete the identity verification challenges in the app
2. If this wasn't you, contact our security team immediately
3. Review your recent account activity

Your account remains secure and protected.

Best regards,
NETHRA Security Team

This is an automated security alert. Please do not reply to this email.
''';
  }
  
  String _generateCriticalThreatAlertBody(int userId, double trustScore, String reason) {
    return '''
URGENT SECURITY ALERT

Dear NETHRA Banking Customer,

Your account access has been immediately terminated due to critical security concerns.

Security Details:
- Account ID: $userId
- Trust Score: ${trustScore.toStringAsFixed(1)}%
- Reason: $reason
- Time: ${DateTime.now().toString().substring(0, 19)}

Immediate Action Required:
1. Contact our security team at security@nethra-banking.com
2. Verify your identity through alternative channels
3. Review all recent account activity

Your account has been secured and no unauthorized transactions have been processed.

Emergency Contact: +1-800-NETHRA-SEC

Best regards,
NETHRA Security Team

This is an automated security alert. Please do not reply to this email.
''';
  }
  
  List<EmailAlert> getAlertHistory({int limit = 50}) {
    return _alertHistory.take(limit).toList();
  }
  
  void clearHistory() {
    _alertHistory.clear();
  }
}

class EmailAlert {
  final String id;
  final EmailAlertType type;
  final String recipient;
  final String subject;
  final String body;
  final DateTime timestamp;
  final int userId;
  final Map<String, dynamic> metadata;
  
  EmailAlert({
    required this.id,
    required this.type,
    required this.recipient,
    required this.subject,
    required this.body,
    required this.timestamp,
    required this.userId,
    required this.metadata,
  });
}

enum EmailAlertType {
  mirageActivation,
  criticalThreat,
  securityRestore,
  accountLocked,
}