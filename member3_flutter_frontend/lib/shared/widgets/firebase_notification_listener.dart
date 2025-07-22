import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/firebase_service.dart';
import '../../core/themes/app_theme.dart';

class FirebaseNotificationListener extends StatefulWidget {
  final Widget child;
  
  const FirebaseNotificationListener({
    super.key,
    required this.child,
  });

  @override
  State<FirebaseNotificationListener> createState() => _FirebaseNotificationListenerState();
}

class _FirebaseNotificationListenerState extends State<FirebaseNotificationListener> {
  late final FirebaseService _firebaseService;
  
  @override
  void initState() {
    super.initState();
    _firebaseService = Provider.of<FirebaseService>(context, listen: false);
    _listenToNotifications();
  }
  
  void _listenToNotifications() {
    _firebaseService.notificationStream.listen((notification) {
      if (mounted) {
        _showNotification(notification);
      }
    });
  }
  
  void _showNotification(FirebaseNotification notification) {
    final color = _getNotificationColor(notification.type);
    final icon = _getNotificationIcon(notification.type);
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              icon,
              color: Colors.white,
              size: 24,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    notification.title,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  Text(
                    notification.body,
                    style: const TextStyle(
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        backgroundColor: color,
        duration: Duration(
          seconds: notification.priority == NotificationPriority.critical ? 8 : 4,
        ),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        margin: const EdgeInsets.all(16),
        action: notification.priority == NotificationPriority.critical
            ? SnackBarAction(
                label: 'DISMISS',
                textColor: Colors.white,
                onPressed: () {
                  ScaffoldMessenger.of(context).hideCurrentSnackBar();
                },
              )
            : null,
      ),
    );
    
    // Show dialog for critical notifications
    if (notification.priority == NotificationPriority.critical) {
      Future.delayed(const Duration(milliseconds: 500), () {
        if (mounted) {
          _showCriticalNotificationDialog(notification);
        }
      });
    }
  }
  
  void _showCriticalNotificationDialog(FirebaseNotification notification) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(
              _getNotificationIcon(notification.type),
              color: _getNotificationColor(notification.type),
              size: 28,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                notification.title,
                style: TextStyle(
                  color: _getNotificationColor(notification.type),
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(notification.body),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _getNotificationColor(notification.type).withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Security Details:',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _getNotificationColor(notification.type),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Time: ${notification.timestamp.toString()}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (notification.data.isNotEmpty)
                    Text(
                      'Event ID: ${notification.id}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Acknowledge'),
          ),
          if (notification.type == NotificationType.tamperDetection)
            ElevatedButton(
              onPressed: () {
                Navigator.of(context).pop();
                // Handle security action
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.errorColor,
                foregroundColor: Colors.white,
              ),
              child: const Text('Secure Account'),
            ),
        ],
      ),
    );
  }
  
  Color _getNotificationColor(NotificationType type) {
    switch (type) {
      case NotificationType.tamperDetection:
        return AppTheme.errorColor;
      case NotificationType.sessionLock:
        return AppTheme.warningColor;
      case NotificationType.mirageActivation:
        return AppTheme.primaryColor;
      case NotificationType.trustScore:
        return AppTheme.warningColor;
      case NotificationType.securityRestore:
        return AppTheme.successColor;
      case NotificationType.learningProgress:
        return AppTheme.accentColor;
    }
  }
  
  IconData _getNotificationIcon(NotificationType type) {
    switch (type) {
      case NotificationType.tamperDetection:
        return Icons.warning;
      case NotificationType.sessionLock:
        return Icons.lock;
      case NotificationType.mirageActivation:
        return Icons.security;
      case NotificationType.trustScore:
        return Icons.trending_down;
      case NotificationType.securityRestore:
        return Icons.check_circle;
      case NotificationType.learningProgress:
        return Icons.psychology;
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
}