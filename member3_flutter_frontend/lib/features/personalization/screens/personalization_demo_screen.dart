import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'dart:async';
import '../../../core/themes/app_theme.dart';
import '../../../shared/widgets/behavioral_wrapper.dart';
import '../../../shared/widgets/custom_button.dart';

class PersonalizationDemoScreen extends StatefulWidget {
  const PersonalizationDemoScreen({super.key});

  @override
  State<PersonalizationDemoScreen> createState() => _PersonalizationDemoScreenState();
}

class _PersonalizationDemoScreenState extends State<PersonalizationDemoScreen> {
  int _currentUserProfile = 0;
  bool _showComparison = false;
  double _learningProgress = 0.0;
  double _standardTrustScore = 45.0;
  double _personalizedTrustScore = 75.0;
  
  final List<UserProfile> _userProfiles = [
    UserProfile(
      name: 'Sarah (Light Touch)',
      description: 'Naturally gentle touch patterns',
      tapPressure: 0.4,
      swipeVelocity: 400.0,
      deviceTilt: 0.1,
      color: AppTheme.successColor,
    ),
    UserProfile(
      name: 'Mike (Heavy Touch)',
      description: 'Naturally firm touch patterns',
      tapPressure: 1.2,
      swipeVelocity: 1200.0,
      deviceTilt: 0.6,
      color: AppTheme.primaryColor,
    ),
    UserProfile(
      name: 'Alex (Variable)',
      description: 'Inconsistent interaction patterns',
      tapPressure: 0.8,
      swipeVelocity: 800.0,
      deviceTilt: 0.4,
      color: AppTheme.warningColor,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return BehavioralWrapper(
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        appBar: AppBar(
          title: const Text('Personalization Demo'),
          backgroundColor: AppTheme.backgroundColor,
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: _resetDemo,
            ),
          ],
        ),
        body: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildDemoHeader().animate().fadeIn(delay: 100.ms),
              const SizedBox(height: 24),
              _buildUserProfileSelector().animate().slideX(delay: 300.ms),
              const SizedBox(height: 24),
              _buildPersonalizationStatus().animate().slideY(delay: 500.ms),
              const SizedBox(height: 24),
              _buildBehaviorComparison().animate().fadeIn(delay: 700.ms),
              const SizedBox(height: 24),
              _buildDemoActions().animate().slideY(delay: 900.ms),
              if (_showComparison) ...[
                const SizedBox(height: 24),
                _buildComparisonResults().animate().fadeIn(delay: 1100.ms),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDemoHeader() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.primaryColor,
            AppTheme.accentColor,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppTheme.primaryColor.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.psychology,
                color: Colors.white,
                size: 32,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Personalized Security',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Fair treatment for all interaction styles',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        color: Colors.white.withOpacity(0.9),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              'NETHRA learns each user\'s unique behavioral pattern and provides personalized security thresholds. This demo shows how the same behavior gets different treatment based on user baselines.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserProfileSelector() {
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
          Text(
            'Select User Profile',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          ...List.generate(_userProfiles.length, (index) {
            final profile = _userProfiles[index];
            final isSelected = _currentUserProfile == index;
            
            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              child: InkWell(
                onTap: () => _selectUserProfile(index),
                borderRadius: BorderRadius.circular(12),
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: isSelected 
                        ? profile.color.withOpacity(0.1)
                        : AppTheme.backgroundColor,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isSelected 
                          ? profile.color
                          : Colors.grey.withOpacity(0.3),
                      width: isSelected ? 2 : 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: profile.color.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Icon(
                          Icons.person,
                          color: profile.color,
                          size: 24,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              profile.name,
                              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                fontWeight: FontWeight.w600,
                                color: isSelected ? profile.color : AppTheme.textPrimary,
                              ),
                            ),
                            Text(
                              profile.description,
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
                          color: profile.color,
                        ),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildPersonalizationStatus() {
    final currentProfile = _userProfiles[_currentUserProfile];
    
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
              Icon(
                Icons.tune,
                color: currentProfile.color,
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                'Personalization Status',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          _buildStatusItem(
            'Learning Progress',
            '${(_learningProgress * 100).toInt()}%',
            _learningProgress,
            currentProfile.color,
          ),
          const SizedBox(height: 16),
          _buildStatusItem(
            'Baseline Confidence',
            '${(_learningProgress * 80).toInt()}%',
            _learningProgress * 0.8,
            currentProfile.color,
          ),
          const SizedBox(height: 16),
          _buildStatusItem(
            'Adaptation Count',
            '${(_learningProgress * 50).toInt()}',
            _learningProgress,
            currentProfile.color,
          ),
        ],
      ),
    );
  }

  Widget _buildStatusItem(String label, String value, double progress, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              value,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: progress.clamp(0.0, 1.0),
          backgroundColor: color.withOpacity(0.2),
          valueColor: AlwaysStoppedAnimation<Color>(color),
        ),
      ],
    );
  }

  Widget _buildBehaviorComparison() {
    final currentProfile = _userProfiles[_currentUserProfile];
    
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
          Text(
            '${currentProfile.name} - Behavioral Profile',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 20),
          _buildBehaviorMetric(
            'Tap Pressure',
            currentProfile.tapPressure,
            'Normal range: 0.3 - 1.5',
            currentProfile.color,
          ),
          const SizedBox(height: 16),
          _buildBehaviorMetric(
            'Swipe Velocity',
            currentProfile.swipeVelocity / 1000,
            'Normal range: 200 - 1500 px/s',
            currentProfile.color,
          ),
          const SizedBox(height: 16),
          _buildBehaviorMetric(
            'Device Tilt',
            currentProfile.deviceTilt,
            'Normal range: 0.1 - 0.8',
            currentProfile.color,
          ),
        ],
      ),
    );
  }

  Widget _buildBehaviorMetric(String label, double value, String range, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              value.toStringAsFixed(2),
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          range,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: AppTheme.textSecondary,
          ),
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: _normalizeValue(value, label),
          backgroundColor: color.withOpacity(0.2),
          valueColor: AlwaysStoppedAnimation<Color>(color),
        ),
      ],
    );
  }

  double _normalizeValue(double value, String label) {
    switch (label) {
      case 'Tap Pressure':
        return (value / 1.5).clamp(0.0, 1.0);
      case 'Swipe Velocity':
        return (value / 1.5).clamp(0.0, 1.0);
      case 'Device Tilt':
        return (value / 0.8).clamp(0.0, 1.0);
      default:
        return 0.5;
    }
  }

  Widget _buildDemoActions() {
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
          Text(
            'Demo Actions',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: CustomButton(
                  text: 'Run Comparison',
                  onPressed: _runComparison,
                  backgroundColor: AppTheme.primaryColor,
                  icon: Icons.compare_arrows,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: CustomButton(
                  text: 'Simulate Learning',
                  onPressed: _simulateLearning,
                  backgroundColor: AppTheme.accentColor,
                  icon: Icons.school,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildComparisonResults() {
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
          Text(
            'Comparison Results',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 20),
          _buildComparisonCard(
            'Standard Security',
            _standardTrustScore,
            'One-size-fits-all approach',
            AppTheme.errorColor,
          ),
          const SizedBox(height: 16),
          _buildComparisonCard(
            'Personalized Security',
            _personalizedTrustScore,
            'Adapted to user\'s unique patterns',
            AppTheme.successColor,
          ),
          const SizedBox(height: 20),
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
                  'Key Insight',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'The same behavioral pattern receives different trust scores based on the user\'s established baseline. This ensures fair treatment for users with naturally different interaction styles.',
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildComparisonCard(String title, double score, String description, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: color.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Center(
              child: Text(
                score.toStringAsFixed(0),
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ),
          ),
          const SizedBox(width: 16),
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
                  description,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _selectUserProfile(int index) {
    setState(() {
      _currentUserProfile = index;
      _showComparison = false;
      _learningProgress = 0.0;
    });
  }

  void _runComparison() {
    final currentProfile = _userProfiles[_currentUserProfile];
    
    // Simulate comparison based on user profile
    setState(() {
      // Standard security gives same score regardless of user
      _standardTrustScore = 45.0;
      
      // Personalized security adapts to user's natural patterns
      switch (currentProfile.name) {
        case 'Sarah (Light Touch)':
          _personalizedTrustScore = 85.0; // High score for gentle user
          break;
        case 'Mike (Heavy Touch)':
          _personalizedTrustScore = 78.0; // Good score for firm user
          break;
        case 'Alex (Variable)':
          _personalizedTrustScore = 65.0; // Moderate score for inconsistent user
          break;
      }
      
      _showComparison = true;
    });
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Comparison completed for ${currentProfile.name}'),
        backgroundColor: AppTheme.successColor,
      ),
    );
  }

  void _simulateLearning() {
    setState(() {
      _learningProgress = 0.0;
    });
    
    // Animate learning progress
    Timer.periodic(const Duration(milliseconds: 200), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      
      setState(() {
        _learningProgress += 0.1;
      });
      
      if (_learningProgress >= 1.0) {
        timer.cancel();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Learning simulation completed!'),
            backgroundColor: AppTheme.successColor,
          ),
        );
      }
    });
  }

  void _resetDemo() {
    setState(() {
      _showComparison = false;
      _learningProgress = 0.0;
      _standardTrustScore = 45.0;
      _personalizedTrustScore = 75.0;
    });
  }
}

class UserProfile {
  final String name;
  final String description;
  final double tapPressure;
  final double swipeVelocity;
  final double deviceTilt;
  final Color color;
  
  UserProfile({
    required this.name,
    required this.description,
    required this.tapPressure,
    required this.swipeVelocity,
    required this.deviceTilt,
    required this.color,
  });
}