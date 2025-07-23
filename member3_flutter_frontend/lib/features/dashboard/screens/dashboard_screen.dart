// lib/features/dashboard/screens/dashboard_screen.dart (Updated)
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/themes/app_theme.dart';
import '../../../shared/widgets/behavioral_wrapper.dart';
import '../../../shared/widgets/trust_indicator.dart';
import '../../../shared/widgets/account_card.dart';
import '../../../shared/widgets/quick_actions.dart';
import '../../../shared/widgets/recent_transactions.dart';
import '../../trust_monitor/providers/trust_provider.dart';
import '../../trust_monitor/screens/trust_monitor_screen.dart';
import '../../transactions/screens/transactions_screen.dart';
import '../../mirage_interface/screens/mirage_screen.dart';
import '../../authentication/providers/auth_provider.dart';
import '../../personalization/screens/personalization_demo_screen.dart';
import '../../demo/screens/demo_user_selector_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Timer? _criticalThreatTimer;
  
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeServices();
    });
  }
  
  @override
  void dispose() {
    _criticalThreatTimer?.cancel();
    super.dispose();
  }
  
  Future<void> _initializeServices() async {
    final trustProvider = Provider.of<TrustProvider>(context, listen: false);
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    
    // Start trust monitoring
    await trustProvider.startMonitoring();
    
    // Handle critical threat auto-logout
    _setupCriticalThreatHandling(trustProvider, authProvider);
    
    // Initialize user session and profile
    await _initializeUserSession(authProvider);
  }
  
  void _setupCriticalThreatHandling(TrustProvider trustProvider, AuthProvider authProvider) {
    // Listen for critical threat user type
    trustProvider.addListener(() {
      if (trustProvider.currentUserType == 'user4_critical_threat' && 
          trustProvider.isMonitoring &&
          _criticalThreatTimer == null) {
        
        // Start 10-second countdown for auto-logout
        _criticalThreatTimer = Timer(const Duration(seconds: 10), () {
          if (mounted) {
            _handleCriticalThreatLogout(authProvider);
          }
        });
        
        // Show countdown warning
        _showCriticalThreatWarning();
      }
    });
  }
  
  void _showCriticalThreatWarning() {
    if (!mounted) return;
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.dangerous, color: AppTheme.errorColor),
            const SizedBox(width: 12),
            const Text('Critical Security Threat'),
          ],
        ),
        content: const Text(
          'Automated behavior detected. Your session will be terminated for security reasons.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _handleCriticalThreatLogout(
                Provider.of<AuthProvider>(context, listen: false)
              );
            },
            child: const Text('Acknowledge'),
          ),
        ],
      ),
    );
  }
  
  void _handleCriticalThreatLogout(AuthProvider authProvider) {
    _criticalThreatTimer?.cancel();
    _criticalThreatTimer = null;
    
    // Log audit event
    final auditService = Provider.of<AuditService>(context, listen: false);
    final userId = int.tryParse(authProvider.userId ?? '0') ?? 0;
    auditService.logCriticalThreatLogout(
      userId: userId,
      trustScore: 5.0,
      reason: 'Automated behavior detected',
      sessionId: 'demo_session',
    );
    
    // Send email alert
    final emailService = Provider.of<EmailAlertService>(context, listen: false);
    emailService.sendCriticalThreatAlert(
      userEmail: authProvider.email ?? 'demo@nethra.com',
      userId: userId,
      trustScore: 5.0,
      reason: 'Automated behavior detected',
    );
    
    // Stop monitoring
    final trustProvider = Provider.of<TrustProvider>(context, listen: false);
    trustProvider.stopMonitoring();
    
    // Logout
    authProvider.logout();
    
    // Show security alert
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(Icons.security, color: Colors.white),
            const SizedBox(width: 12),
            const Expanded(
              child: Text('Session terminated due to critical security threat'),
            ),
          ],
        ),
        backgroundColor: AppTheme.errorColor,
        duration: const Duration(seconds: 5),
      ),
    );
  }
  
  Future<void> _initializeUserSession(AuthProvider authProvider) async {
    try {
      // Get user profile to ensure backend connection
      await authProvider.apiService.getUserProfile();
      
      if (mounted) {
        // Don't show success message for demo users to avoid UI interference
        final trustProvider = Provider.of<TrustProvider>(context, listen: false);
        if (trustProvider.currentUserType == 'normal') {
          // Suppress connection success message to reduce UI noise
          if (kDebugMode) {
            print('✅ Connected to NETHRA backend');
          }
        }
      }
    } catch (e) {
      if (mounted) {
        // Only show connection issues for non-demo users
        final trustProvider = Provider.of<TrustProvider>(context, listen: false);
        if (trustProvider.currentUserType == 'normal') {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Row(
                children: [
                  const Icon(Icons.warning, color: Colors.white),
                  const SizedBox(width: 8),
                  Expanded(child: Text('Backend connection issue: Using demo mode')),
                ],
              ),
              backgroundColor: AppTheme.warningColor,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BehavioralWrapper(
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        body: SafeArea(
          child: Consumer<TrustProvider>(
            builder: (context, trustProvider, child) {
              // Show mirage interface if trust score is low
              if (trustProvider.shouldShowMirage) {
                return const MirageScreen();
              }
              
              return CustomScrollView(
                slivers: [
                  _buildAppBar(context, trustProvider),
                  SliverPadding(
                    padding: const EdgeInsets.all(16),
                    sliver: SliverList(
                      delegate: SliverChildListDelegate([
                        if (trustProvider.currentUserType != 'normal')
                          _buildDemoIndicator(trustProvider).animate().slideY(delay: 50.ms),
                        if (trustProvider.currentUserType != 'normal')
                          const SizedBox(height: 16),
                        _buildTrustIndicator(trustProvider),
                        const SizedBox(height: 24),
                        _buildAccountCard().animate().slideX(delay: 300.ms),
                        const SizedBox(height: 24),
                        _buildQuickActions().animate().slideY(delay: 500.ms),
                        const SizedBox(height: 24),
                        _buildRecentTransactions().animate().fadeIn(delay: 700.ms),
                        const SizedBox(height: 24),
                        _buildSecurityInsights(trustProvider).animate().fadeIn(delay: 900.ms),
                      ]),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildDemoIndicator(TrustProvider trustProvider) {
    final userTypeInfo = _getUserTypeInfo(trustProvider.currentUserType);
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            userTypeInfo['color'].withOpacity(0.8),
            userTypeInfo['color'],
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: userTypeInfo['color'].withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Icon(
            Icons.science,
            color: Colors.white,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'DEMO MODE: ${userTypeInfo['name']}',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  userTypeInfo['description'],
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.white.withOpacity(0.9),
                  ),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pushReplacement(
                context,
                MaterialPageRoute(
                  builder: (context) => const DemoUserSelectorScreen(),
                ),
              );
            },
            child: Text(
              'CHANGE',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Map<String, dynamic> _getUserTypeInfo(String userType) {
    switch (userType) {
      case 'user1_low_threat':
        return {
          'name': 'User 1 - Sarah Thompson',
          'description': 'Low Threat - Smooth Usage',
          'color': AppTheme.successColor,
        };
      case 'user2_medium_threat':
        return {
          'name': 'User 2 - Alex Rodriguez',
          'description': 'Medium Threat - Slight Anomaly',
          'color': AppTheme.accentColor,
        };
      case 'user3_high_threat':
        return {
          'name': 'User 3 - Suspicious Actor',
          'description': 'High Threat - Mirage Triggered',
          'color': AppTheme.warningColor,
        };
      case 'user4_critical_threat':
        return {
          'name': 'User 4 - Critical Bot',
          'description': 'Critical Threat - Auto-Logout',
          'color': AppTheme.errorColor,
        };
      default:
        return {
          'name': 'Normal User',
          'description': 'Standard Operation',
          'color': AppTheme.primaryColor,
        };
    }
  }

  Widget _buildAppBar(BuildContext context, TrustProvider trustProvider) {
    return SliverAppBar(
      expandedHeight: 100,
      floating: false,
      pinned: true,
      backgroundColor: AppTheme.backgroundColor,
      flexibleSpace: FlexibleSpaceBar(
        titlePadding: const EdgeInsets.only(left: 16, bottom: 16),
        title: Consumer<AuthProvider>(
          builder: (context, authProvider, child) {
            return Column(
              mainAxisAlignment: MainAxisAlignment.end,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Welcome back,',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
                Text(
                  trustProvider.currentUserType != 'normal' 
                      ? _getUserTypeInfo(trustProvider.currentUserType)['name']
                      : authProvider.username ?? 'User',
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            );
          },
        ),
      ),
      actions: [
        if (trustProvider.currentUserType != 'normal')
          IconButton(
            icon: const Icon(Icons.science),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => const DemoUserSelectorScreen(),
                ),
              );
            },
            tooltip: 'Demo Controls',
          ),
        IconButton(
          icon: const Icon(Icons.notifications_outlined),
          onPressed: () {
            _showNotificationCenter(context);
          },
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert),
          onSelected: (value) {
            switch (value) {
              case 'demo_selector':
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const DemoUserSelectorScreen(),
                  ),
                );
                break;
              case 'profile':
                _showUserProfile(context);
                break;
              case 'logout':
                _handleLogout(context);
                break;
            }
          },
          itemBuilder: (context) => [
            if (trustProvider.currentUserType != 'normal')
              const PopupMenuItem(
                value: 'demo_selector',
                child: Row(
                  children: [
                    Icon(Icons.science),
                    SizedBox(width: 8),
                    Text('Demo Controls'),
                  ],
                ),
              ),
            const PopupMenuItem(
              value: 'profile',
              child: Row(
                children: [
                  Icon(Icons.person),
                  SizedBox(width: 8),
                  Text('Profile'),
                ],
              ),
            ),
            const PopupMenuItem(
              value: 'logout',
              child: Row(
                children: [
                  Icon(Icons.logout),
                  SizedBox(width: 8),
                  Text('Logout'),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildTrustIndicator(TrustProvider trustProvider) {
    return TrustIndicator(
      trustScore: trustProvider.trustScore,
      trustLevel: trustProvider.trustLevel,
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const TrustMonitorScreen(),
          ),
        );
      },
    ).animate().slideY(delay: 100.ms);
  }

  Widget _buildAccountCard() {
    return const AccountCard();
  }

  Widget _buildQuickActions() {
    return QuickActions(
      onTransfer: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => const TransactionsScreen(),
          ),
        );
      },
      onPayBills: () {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Bill payment feature coming soon!')),
        );
      },
      onDeposit: () {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Deposit feature coming soon!')),
        );
      },
      onMoreActions: () {
        _showMoreActionsDialog(context);
      },
    );
  }

  Widget _buildRecentTransactions() {
    return const RecentTransactions();
  }

  Widget _buildSecurityInsights(TrustProvider trustProvider) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.insights,
                color: AppTheme.primaryColor,
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                'Security Insights',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _buildInsightItem(
            icon: Icons.check_circle,
            title: 'Behavioral Authentication',
            subtitle: trustProvider.isMonitoring ? 'Active and monitoring' : 'Initializing...',
            color: trustProvider.isMonitoring ? AppTheme.successColor : AppTheme.warningColor,
          ),
          const SizedBox(height: 12),
          _buildInsightItem(
            icon: Icons.security,
            title: 'Session Security',
            subtitle: 'Trust score: ${trustProvider.trustScore.toStringAsFixed(1)}',
            color: _getTrustColor(trustProvider.trustScore),
          ),
          const SizedBox(height: 12),
          _buildInsightItem(
            icon: Icons.psychology,
            title: 'Personalization',
            subtitle: trustProvider.isPersonalized ? 'Fully adapted' : 'Learning your patterns',
            color: trustProvider.isPersonalized ? AppTheme.successColor : AppTheme.accentColor,
          ),
          if (trustProvider.currentUserType != 'normal') ...[
            const SizedBox(height: 12),
            _buildInsightItem(
              icon: Icons.science,
              title: 'Demo Mode',
              subtitle: '${_getUserTypeInfo(trustProvider.currentUserType)['name']} simulation',
              color: _getUserTypeInfo(trustProvider.currentUserType)['color'],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildInsightItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
  }) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            icon,
            color: color,
            size: 20,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Color _getTrustColor(double trustScore) {
    if (trustScore >= 80) return AppTheme.successColor;
    if (trustScore >= 60) return AppTheme.accentColor;
    if (trustScore >= 40) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }
  
  void _showNotificationCenter(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Security Notifications',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Firebase notifications will appear here in real-time when security events occur.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppTheme.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
  
  void _showUserProfile(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final trustProvider = Provider.of<TrustProvider>(context, listen: false);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('User Profile'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (trustProvider.currentUserType != 'normal') ...[
              Text('Demo User: ${_getUserTypeInfo(trustProvider.currentUserType)['name']}'),
              Text('User Type: ${trustProvider.currentUserType}'),
              const SizedBox(height: 8),
            ],
            Text('Username: ${authProvider.username ?? 'N/A'}'),
            Text('Email: ${authProvider.email ?? 'N/A'}'),
            Text('User ID: ${authProvider.userId ?? 'N/A'}'),
            const SizedBox(height: 16),
            Text(
              'Account created and managed through NETHRA backend',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textSecondary,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
  
  void _showMoreActionsDialog(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'More Actions',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.science),
              title: const Text('Demo Controls'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const DemoUserSelectorScreen(),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.security),
              title: const Text('Trust Monitor'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const TrustMonitorScreen(),
                  ),
                );
              },
            ),
            ListTile(
              leading: const Icon(Icons.help),
              title: const Text('Help & Support'),
              onTap: () {
                Navigator.pop(context);
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Row(
                      children: [
                        Icon(Icons.help, color: AppTheme.primaryColor),
                        SizedBox(width: 12),
                        Text('Help & Support'),
                      ],
                    ),
                    content: const Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('Need help with NETHRA Banking?'),
                        SizedBox(height: 16),
                        Text(
                          'Contact our support team:\n• Email: support@nethra.com\n• Phone: 1-800-NETHRA\n• Live Chat: Available 24/7',
                          style: TextStyle(fontSize: 14),
                        ),
                      ],
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Got it'),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  void _handleLogout(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _criticalThreatTimer?.cancel();
              Provider.of<AuthProvider>(context, listen: false).logout();
              Provider.of<TrustProvider>(context, listen: false).stopMonitoring();
            },
            child: const Text('Logout'),
          ),
        ],
      ),
    );
  }
}