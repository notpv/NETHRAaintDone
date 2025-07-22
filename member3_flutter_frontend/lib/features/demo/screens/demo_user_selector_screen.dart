// lib/features/demo/screens/demo_user_selector_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/themes/app_theme.dart';
import '../../../shared/widgets/custom_button.dart';
import '../../trust_monitor/providers/trust_provider.dart';
import '../../authentication/providers/auth_provider.dart';
import '../../dashboard/screens/dashboard_screen.dart';

class DemoUserSelectorScreen extends StatefulWidget {
  const DemoUserSelectorScreen({super.key});

  @override
  State<DemoUserSelectorScreen> createState() => _DemoUserSelectorScreenState();
}

class _DemoUserSelectorScreenState extends State<DemoUserSelectorScreen> {
  String? _selectedUserType;
  bool _isLoading = false;

  final List<DemoUser> _demoUsers = [
    DemoUser(
      type: 'low_threat',
      name: 'Sarah Thompson',
      description: 'Normal User - Consistent Behavior',
      subtitle: 'Trust Score: 85-95% • No Security Alerts',
      icon: Icons.verified_user,
      color: AppTheme.successColor,
      behaviorProfile: 'Gentle touch patterns, consistent swipe velocity, stable device handling',
    ),
    DemoUser(
      type: 'medium_threat',
      name: 'Alex Rodriguez',
      description: 'Moderate Risk User - Variable Behavior',
      subtitle: 'Trust Score: 55-75% • Occasional Monitoring',
      icon: Icons.security,
      color: AppTheme.accentColor,
      behaviorProfile: 'Fluctuating interaction patterns, sometimes inconsistent timing',
    ),
    DemoUser(
      type: 'high_threat',
      name: 'Unknown User',
      description: 'High Risk User - Suspicious Activity',
      subtitle: 'Trust Score: 15-35% • Mirage Interface Activated',
      icon: Icons.warning,
      color: AppTheme.warningColor,
      behaviorProfile: 'Unusual behavioral patterns, potential bot-like interactions',
    ),
    DemoUser(
      type: 'critical_threat',
      name: 'Automated Bot',
      description: 'Critical Threat - Immediate Action Required',
      subtitle: 'Trust Score: 1-10% • Auto-Logout in 10 seconds',
      icon: Icons.dangerous,
      color: AppTheme.errorColor,
      behaviorProfile: 'Automated behavior detected, immediate security threat',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader().animate().fadeIn(delay: 100.ms),
              const SizedBox(height: 32),
              Expanded(
                child: ListView.builder(
                  itemCount: _demoUsers.length,
                  itemBuilder: (context, index) {
                    final user = _demoUsers[index];
                    return _buildUserCard(user, index).animate()
                        .slideX(delay: (200 + index * 100).ms, begin: 0.3);
                  },
                ),
              ),
              if (_selectedUserType != null) ...[
                const SizedBox(height: 24),
                _buildActionButton().animate().slideY(delay: 600.ms),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 60,
              height: 60,
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppTheme.primaryColor, AppTheme.accentColor],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.science,
                size: 30,
                color: Colors.white,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'NETHRA Demo',
                    style: Theme.of(context).textTheme.headlineLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                  Text(
                    'Choose a demo user profile',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppTheme.primaryColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Demo Experience',
                style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Each user profile demonstrates different behavioral patterns and security responses. Select a profile to experience how NETHRA adapts to various threat levels.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppTheme.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildUserCard(DemoUser user, int index) {
    final isSelected = _selectedUserType == user.type;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: () {
          setState(() {
            _selectedUserType = user.type;
          });
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: isSelected ? user.color.withOpacity(0.1) : AppTheme.surfaceColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isSelected ? user.color : Colors.grey.withOpacity(0.2),
              width: isSelected ? 2 : 1,
            ),
            boxShadow: isSelected ? [
              BoxShadow(
                color: user.color.withOpacity(0.2),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ] : [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 5,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 60,
                    height: 60,
                    decoration: BoxDecoration(
                      color: user.color.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Icon(
                      user.icon,
                      color: user.color,
                      size: 30,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user.name,
                          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: isSelected ? user.color : AppTheme.textPrimary,
                          ),
                        ),
                        Text(
                          user.description,
                          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                        Text(
                          user.subtitle,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppTheme.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (isSelected)
                    Icon(
                      Icons.check_circle,
                      color: user.color,
                      size: 32,
                    ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: user.color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Behavioral Profile:',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: user.color,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      user.behaviorProfile,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionButton() {
    final selectedUser = _demoUsers.firstWhere((user) => user.type == _selectedUserType);
    
    return Column(
      children: [
        CustomButton(
          text: _isLoading ? 'Starting Demo...' : 'Start Demo as ${selectedUser.name}',
          isLoading: _isLoading,
          onPressed: _startDemo,
          backgroundColor: selectedUser.color,
          icon: Icons.play_arrow,
        ),
        const SizedBox(height: 12),
        Text(
          'This will simulate the selected user\'s behavioral patterns and security responses',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: AppTheme.textSecondary,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Future<void> _startDemo() async {
    if (_selectedUserType == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // Set up the demo user in TrustProvider
      final trustProvider = Provider.of<TrustProvider>(context, listen: false);
      trustProvider.setUserType(_selectedUserType!);

      // Navigate to dashboard
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => const DashboardScreen(),
          ),
        );
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to start demo: $e'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }
}

class DemoUser {
  final String type;
  final String name;
  final String description;
  final String subtitle;
  final IconData icon;
  final Color color;
  final String behaviorProfile;

  DemoUser({
    required this.type,
    required this.name,
    required this.description,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.behaviorProfile,
  });
}