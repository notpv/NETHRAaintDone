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

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeServices();
    });
  }
  
  Future<void> _initializeServices() async {
    final trustProvider = Provider.of<TrustProvider>(context, listen: false);
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    
    // Start trust monitoring
    await trustProvider.startMonitoring();
    
    // Initialize user session and profile
    await _initializeUserSession(authProvider);
  }
  
  Future<void> _initializeUserSession(AuthProvider authProvider) async {
    try {
      // Get user profile to ensure backend connection
      await authProvider.apiService.getUserProfile();
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.check_circle, color: Colors.white),
                const SizedBox(width: 8),
                Text('Connected to NETHRA backend'),
              ],
            ),
            backgroundColor: AppTheme.successColor,
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
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
            duration: const Duration(seconds: 3),
          ),
        );
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
                  _buildAppBar(context),
                  SliverPadding(
                    padding: const EdgeInsets.all(16),
                    sliver: SliverList(
                      delegate: SliverChildListDelegate([
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

  Widget _buildAppBar(BuildContext context) {
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
                  authProvider.username ?? 'User',
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
        IconButton(
          icon: const Icon(Icons.notifications_outlined),
          onPressed: () {
            _showNotificationCenter(context);
          },
        ),
        IconButton(
          icon: const Icon(Icons.psychology),
          onPressed: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const PersonalizationDemoScreen(),
              ),
            );
          },
        ),
        PopupMenuButton<String>(
          icon: const Icon(Icons.more_vert),
          onSelected: (value) {
            switch (value) {
              case 'profile':
                _showUserProfile(context);
                break;
              case 'delete_account':
                _showDeleteAccountDialog(context);
                break;
              case 'logout':
                _handleLogout(context);
                break;
            }
          },
          itemBuilder: (context) => [
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
              value: 'delete_account',
              child: Row(
                children: [
                  Icon(Icons.delete_forever, color: AppTheme.errorColor),
                  SizedBox(width: 8),
                  Text('Delete Account', style: TextStyle(color: AppTheme.errorColor)),
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
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('User Profile'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
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
  
  void _showDeleteAccountDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.warning, color: AppTheme.errorColor),
            const SizedBox(width: 8),
            const Text('Delete Account'),
          ],
        ),
        content: const Text(
          'Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently removed.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              final authProvider = Provider.of<AuthProvider>(context, listen: false);
              final success = await authProvider.deleteAccount();
              
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text(success ? 'Account deleted successfully' : 'Failed to delete account'),
                    backgroundColor: success ? AppTheme.successColor : AppTheme.errorColor,
                  ),
                );
              }
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.errorColor,
              foregroundColor: Colors.white,
            ),
            child: const Text('Delete'),
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
              leading: const Icon(Icons.psychology),
              title: const Text('Personalization Demo'),
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const PersonalizationDemoScreen(),
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
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Help feature coming soon!')),
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