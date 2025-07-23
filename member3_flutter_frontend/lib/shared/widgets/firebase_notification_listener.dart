// lib/shared/widgets/firebase_notification_listener.dart (Updated)
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/services/firebase_service.dart';
import '../../core/themes/app_theme.dart';
import '../../features/trust_monitor/providers/trust_provider.dart';

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
  final List<FirebaseNotification> _notifications = [];
  
  @override
  void initState() {
    super.initState();
    _firebaseService = Provider.of<FirebaseService>(context, listen: false);
    _listenToNotifications();
  }
  
  void _listenToNotifications() {
    _firebaseService.notificationStream.listen((notification) {
      if (mounted) {
        // Store notification for later access
        setState(() {
          _notifications.insert(0, notification);
          // Keep only last 50 notifications
          if (_notifications.length > 50) {
            _notifications.removeLast();
          }
        });
        
        // Check if we should suppress notifications during demo mode
        final trustProvider = Provider.of<TrustProvider>(context, listen: false);
        
        // Suppress all popup notifications - only store them
        // Users can access via notifications icon
      }
    });
  }
  
  void _showNotification(FirebaseNotification notification) {
    final color = _getNotificationColor(notification.type);
    final icon = _getNotificationIcon(notification.type);
    
    // For critical notifications, show dialog immediately without snackbar
    if (notification.priority == NotificationPriority.critical) {
      _showCriticalNotificationDialog(notification);
      return;
    }
    
    // Show snackbar for non-critical notifications
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
        duration: const Duration(seconds: 3), // Reduced duration
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        margin: const EdgeInsets.all(16),
        action: SnackBarAction(
          label: 'DISMISS',
          textColor: Colors.white,
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
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
                    'Time: ${notification.timestamp.toString().substring(0, 19)}',
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
                // Handle security action - could logout user
                final trustProvider = Provider.of<TrustProvider>(context, listen: false);
                trustProvider.resetTrust();
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
    return Consumer<TrustProvider>(
      builder: (context, trustProvider, child) {
        return Stack(
          children: [
            widget.child,
            // Notification access overlay
            Positioned(
              top: 50,
              right: 16,
              child: _buildNotificationAccess(),
            ),
          ],
        );
      },
    );
  }
  
  Widget _buildNotificationAccess() {
    if (_notifications.isEmpty) return const SizedBox.shrink();
    
    return GestureDetector(
      onTap: _showNotificationCenter,
      child: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: AppTheme.primaryColor,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.notifications,
              color: Colors.white,
              size: 16,
            ),
            const SizedBox(width: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppTheme.errorColor,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${_notifications.length}',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  void _showNotificationCenter() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.7,
        decoration: const BoxDecoration(
          color: AppTheme.surfaceColor,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  Icon(
                    Icons.notifications,
                    color: AppTheme.primaryColor,
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Security Notifications',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: () {
                      setState(() {
                        _notifications.clear();
                      });
                      Navigator.pop(context);
                    },
                    icon: const Icon(Icons.clear_all),
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                itemCount: _notifications.length,
                itemBuilder: (context, index) {
                  final notification = _notifications[index];
                  return _buildNotificationItem(notification);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildNotificationItem(FirebaseNotification notification) {
    final color = _getNotificationColor(notification.type);
    final icon = _getNotificationIcon(notification.type);
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withOpacity(0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  notification.title,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ),
              Text(
                _formatTime(notification.timestamp),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            notification.body,
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
  
  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);
    
    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
    }
  }
}