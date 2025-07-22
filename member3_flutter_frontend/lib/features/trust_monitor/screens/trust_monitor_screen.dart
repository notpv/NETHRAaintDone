import 'dart:math';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../core/themes/app_theme.dart';
import '../../../shared/widgets/behavioral_wrapper.dart';
import '../providers/trust_provider.dart';
import '../../../shared/models/trust_data.dart';
import '../../mirage_interface/screens/mirage_screen.dart';

class TrustMonitorScreen extends StatefulWidget {
  const TrustMonitorScreen({super.key});

  @override
  State<TrustMonitorScreen> createState() => _TrustMonitorScreenState();
}

class _TrustMonitorScreenState extends State<TrustMonitorScreen> {
  List<FlSpot> _trustHistorySpots = [];
  
  @override
  void initState() {
    super.initState();
    // Initialize with current trust score
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final trustProvider = Provider.of<TrustProvider>(context, listen: false);
      _updateTrustHistory(trustProvider.trustScore);
    });
  }

  void _updateTrustHistory(double newScore) {
    setState(() {
      _trustHistorySpots.add(FlSpot(_trustHistorySpots.length.toDouble(), newScore));
      
      // Keep only last 20 points
      if (_trustHistorySpots.length > 20) {
        _trustHistorySpots.removeAt(0);
        // Adjust x values to maintain continuity
        for (int i = 0; i < _trustHistorySpots.length; i++) {
          _trustHistorySpots[i] = FlSpot(i.toDouble(), _trustHistorySpots[i].y);
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return BehavioralWrapper(
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        appBar: AppBar(
          title: const Text('Trust Monitor'),
          backgroundColor: AppTheme.backgroundColor,
          actions: [
            Consumer<TrustProvider>(
              builder: (context, trustProvider, child) {
                return PopupMenuButton<String>(
                  onSelected: (value) {
                    switch (value) {
                      case 'simulate_threat':
                        trustProvider.simulateThreat();
                        break;
                      case 'reset_trust':
                        trustProvider.resetTrust();
                        break;
                    }
                  },
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'simulate_threat',
                      child: Row(
                        children: [
                          Icon(Icons.warning, color: AppTheme.warningColor),
                          SizedBox(width: 8),
                          Text('Simulate Threat'),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'reset_trust',
                      child: Row(
                        children: [
                          Icon(Icons.refresh, color: AppTheme.successColor),
                          SizedBox(width: 8),
                          Text('Reset Trust'),
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),
          ],
        ),
        body: Consumer<TrustProvider>(
          builder: (context, trustProvider, child) {
            // Update history when trust score changes
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (_trustHistorySpots.isEmpty || 
                  _trustHistorySpots.last.y != trustProvider.trustScore) {
                _updateTrustHistory(trustProvider.trustScore);
              }
            });
            
            // Show mirage interface if trust score is low
            if (trustProvider.shouldShowMirage) {
              return const MirageScreen();
            }
            
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildTrustScoreCard(trustProvider).animate().slideY(delay: 100.ms),
                  const SizedBox(height: 24),
                  _buildTrustChart(trustProvider).animate().slideX(delay: 300.ms),
                  const SizedBox(height: 24),
                  _buildRiskFactors(trustProvider).animate().fadeIn(delay: 500.ms),
                  const SizedBox(height: 24),
                  _buildLiveBehavioralMetrics(trustProvider).animate().slideY(delay: 700.ms),
                  const SizedBox(height: 24),
                  _buildSecurityActions(trustProvider).animate().fadeIn(delay: 900.ms),
                  const SizedBox(height: 24),
                  _buildPersonalizationInsights(trustProvider).animate().slideY(delay: 1100.ms),
                  const SizedBox(height: 24),
                  _buildBackendStatus(trustProvider).animate().fadeIn(delay: 1300.ms),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildTrustScoreCard(TrustProvider trustProvider) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _getTrustColor(trustProvider.trustScore),
            _getTrustColor(trustProvider.trustScore).withOpacity(0.8),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: _getTrustColor(trustProvider.trustScore).withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Trust Score',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _getTrustLevelText(trustProvider.trustLevel),
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                  if (trustProvider.isMonitoring)
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: Colors.greenAccent,
                            shape: BoxShape.circle,
                          ),
                        ).animate(onPlay: (controller) => controller.repeat())
                            .fadeIn(duration: 1.seconds)
                            .then(delay: 500.ms)
                            .fadeOut(duration: 1.seconds),
                        const SizedBox(width: 8),
                        Text(
                          'Live Monitoring',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.white.withOpacity(0.8),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
              Text(
                trustProvider.trustScore.toStringAsFixed(1),
                style: Theme.of(context).textTheme.displayLarge?.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          LinearProgressIndicator(
            value: trustProvider.trustScore / 100,
            backgroundColor: Colors.white.withOpacity(0.3),
            valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
            minHeight: 8,
          ),
        ],
      ),
    );
  }

  Widget _buildTrustChart(TrustProvider trustProvider) {
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
              Text(
                'Trust Score History',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              if (trustProvider.isMonitoring)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.successColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    'LIVE',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.successColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            height: 200,
            child: _trustHistorySpots.isNotEmpty
                ? LineChart(
                    LineChartData(
                      gridData: FlGridData(
                        show: true,
                        drawVerticalLine: false,
                        horizontalInterval: 20,
                        getDrawingHorizontalLine: (value) {
                          return FlLine(
                            color: Colors.grey.withOpacity(0.2),
                            strokeWidth: 1,
                          );
                        },
                      ),
                      titlesData: FlTitlesData(
                        show: true,
                        leftTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 40,
                            getTitlesWidget: (value, meta) {
                              return Text(
                                value.toInt().toString(),
                                style: Theme.of(context).textTheme.bodySmall,
                              );
                            },
                          ),
                        ),
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 30,
                            getTitlesWidget: (value, meta) {
                              return Text(
                                '${value.toInt()}',
                                style: Theme.of(context).textTheme.bodySmall,
                              );
                            },
                          ),
                        ),
                        rightTitles: AxisTitles(
                          sideTitles: SideTitles(showTitles: false),
                        ),
                        topTitles: AxisTitles(
                          sideTitles: SideTitles(showTitles: false),
                        ),
                      ),
                      borderData: FlBorderData(show: false),
                      lineBarsData: [
                        LineChartBarData(
                          spots: _trustHistorySpots,
                          isCurved: true,
                          color: _getTrustColor(trustProvider.trustScore),
                          barWidth: 3,
                          dotData: FlDotData(show: false),
                          belowBarData: BarAreaData(
                            show: true,
                            color: _getTrustColor(trustProvider.trustScore).withOpacity(0.1),
                          ),
                        ),
                      ],
                      minY: 0,
                      maxY: 100,
                    ),
                  )
                : Center(
                    child: Text(
                      'Building trust history...',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildRiskFactors(TrustProvider trustProvider) {
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
                Icons.warning_amber_rounded,
                color: trustProvider.riskFactors.isEmpty 
                    ? AppTheme.successColor 
                    : AppTheme.warningColor,
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                'Risk Factors',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (trustProvider.riskFactors.isEmpty)
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.successColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.check_circle,
                    color: AppTheme.successColor,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'No risk factors detected',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppTheme.successColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            )
          else
            ...trustProvider.riskFactors.map((factor) => Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.warningColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: AppTheme.warningColor.withOpacity(0.3),
                ),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.error_outline,
                    color: AppTheme.warningColor,
                    size: 20,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      factor,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ),
                ],
              ),
            )),
        ],
      ),
    );
  }

  Widget _buildLiveBehavioralMetrics(TrustProvider trustProvider) {
    // Get live behavioral data from the provider
    final behavioralData = trustProvider.getBehavioralData();
    
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
              Text(
                'Live Behavioral Metrics',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
              const Spacer(),
              if (trustProvider.isMonitoring)
                Icon(
                  Icons.sensors,
                  color: AppTheme.successColor,
                  size: 20,
                ).animate(onPlay: (controller) => controller.repeat())
                    .scale(begin: Offset(1.0, 1.0), end: Offset(1.2, 1.2), duration: 1.seconds)
                    .then()
                    .scale(begin: Offset(1.2, 1.2), end: Offset(1.0, 1.0), duration: 1.seconds),
            ],
          ),
          const SizedBox(height: 20),
          if (behavioralData != null) ...[
            Row(
              children: [
                Expanded(
                  child: _buildLiveMetricCard(
                    title: 'Tap Pressure',
                    value: '${(behavioralData.averageTapPressure * 100).toInt()}%',
                    normalizedValue: behavioralData.averageTapPressure,
                    icon: Icons.touch_app,
                    color: _getMetricColor(behavioralData.averageTapPressure, 0.3, 1.2),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildLiveMetricCard(
                    title: 'Swipe Velocity',
                    value: '${behavioralData.averageSwipeVelocity.toInt()}px/s',
                    normalizedValue: (behavioralData.averageSwipeVelocity / 1500).clamp(0.0, 1.0),
                    icon: Icons.swipe,
                    color: _getMetricColor(behavioralData.averageSwipeVelocity / 1500, 0.2, 1.0),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildLiveMetricCard(
                    title: 'Device Tilt',
                    value: '${(behavioralData.deviceTiltVariation * 100).toInt()}%',
                    normalizedValue: behavioralData.deviceTiltVariation,
                    icon: Icons.screen_rotation,
                    color: _getMetricColor(behavioralData.deviceTiltVariation, 0.1, 0.8),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: _buildLiveMetricCard(
                    title: 'Touch Frequency',
                    value: '${(behavioralData.tapCount / (behavioralData.sessionDuration / 60)).toStringAsFixed(1)}/min',
                    normalizedValue: (behavioralData.tapCount / (behavioralData.sessionDuration / 60) / 20).clamp(0.0, 1.0),
                    icon: Icons.fingerprint,
                    color: _getMetricColor(behavioralData.tapCount / (behavioralData.sessionDuration / 60) / 20, 0.2, 1.0),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.timer,
                    color: AppTheme.primaryColor,
                    size: 16,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Session Duration: ${(behavioralData.sessionDuration / 60).toStringAsFixed(1)} minutes',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.primaryColor,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
          ] else ...[
            Container(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Icon(
                    Icons.sensors_off,
                    color: AppTheme.textSecondary,
                    size: 48,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'No behavioral data available',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  Text(
                    'Start interacting with the app to see live metrics',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildLiveMetricCard({
    required String title,
    required String value,
    required double normalizedValue,
    required IconData icon,
    required Color color,
  }) {
    return Container(
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
              Icon(
                icon,
                color: color,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                value,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            title,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppTheme.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: normalizedValue.clamp(0.0, 1.0),
            backgroundColor: color.withOpacity(0.2),
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 4,
          ),
        ],
      ),
    );
  }

  Color _getMetricColor(double normalizedValue, double minNormal, double maxNormal) {
    if (normalizedValue >= minNormal && normalizedValue <= maxNormal) {
      return AppTheme.successColor;
    } else if (normalizedValue > maxNormal * 1.5 || normalizedValue < minNormal * 0.5) {
      return AppTheme.errorColor;
    } else {
      return AppTheme.warningColor;
    }
  }

  Widget _buildSecurityActions(TrustProvider trustProvider) {
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
            'Security Actions',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () {
                    trustProvider.forceUpdateTrust();
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Update Trust'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryColor,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: () {
                    _showSecurityReport(context, trustProvider);
                  },
                  icon: const Icon(Icons.report),
                  label: const Text('Security Report'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.accentColor,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
  
  Widget _buildPersonalizationInsights(TrustProvider trustProvider) {
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
                Icons.psychology,
                color: AppTheme.primaryColor,
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                'Personalization Insights',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          if (trustProvider.isPersonalized) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.successColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.check_circle,
                        color: AppTheme.successColor,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Personalized Security Active',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: AppTheme.successColor,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'NETHRA has learned your unique behavioral patterns and adapted security thresholds accordingly.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _buildComparisonMetric(
                          'Standard Score',
                          trustProvider.standardTrustScore,
                          AppTheme.warningColor,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: _buildComparisonMetric(
                          'Personalized Score',
                          trustProvider.personalizedTrustScore,
                          AppTheme.successColor,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ] else ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.school,
                        color: AppTheme.primaryColor,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Learning Your Patterns',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w600,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'NETHRA is currently learning your unique behavioral patterns to provide personalized security.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
  
  Widget _buildComparisonMetric(String label, double value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Text(
            value.toStringAsFixed(1),
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppTheme.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildBackendStatus(TrustProvider trustProvider) {
    final lastResponse = trustProvider.lastBackendResponse;
    final isConnected = lastResponse != null;
    
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
                isConnected ? Icons.cloud_done : Icons.cloud_off,
                color: isConnected ? AppTheme.successColor : AppTheme.errorColor,
                size: 24,
              ),
              const SizedBox(width: 12),
              Text(
                'Backend Connection',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: (isConnected ? AppTheme.successColor : AppTheme.errorColor).withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      isConnected ? Icons.check_circle : Icons.error,
                      color: isConnected ? AppTheme.successColor : AppTheme.errorColor,
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      isConnected ? 'Connected to NETHRA Backend' : 'Backend Disconnected',
                      style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: isConnected ? AppTheme.successColor : AppTheme.errorColor,
                      ),
                    ),
                  ],
                ),
                if (isConnected && lastResponse != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    'Last Update: ${DateTime.now().toString().substring(11, 19)}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.textSecondary,
                    ),
                  ),
                  if (lastResponse['session_count'] != null)
                    Text(
                      'Session Count: ${lastResponse['session_count']}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textSecondary,
                      ),
                    ),
                  if (lastResponse['security_action'] != null)
                    Text(
                      'Security Action: ${lastResponse['security_action']}',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppTheme.textSecondary,
                      ),
                    ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Color _getTrustColor(double trustScore) {
    if (trustScore >= 80) return AppTheme.successColor;
    if (trustScore >= 60) return AppTheme.accentColor;
    if (trustScore >= 40) return AppTheme.warningColor;
    return AppTheme.errorColor;
  }

  String _getTrustLevelText(TrustLevel trustLevel) {
    switch (trustLevel) {
      case TrustLevel.high:
        return 'High Trust';
      case TrustLevel.medium:
        return 'Medium Trust';
      case TrustLevel.low:
        return 'Low Trust';
      case TrustLevel.critical:
        return 'Critical Risk';
    }
  }

  void _showSecurityReport(BuildContext context, TrustProvider trustProvider) {
    final behavioralData = trustProvider.getBehavioralData();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Security Report'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Trust Score: ${trustProvider.trustScore.toStringAsFixed(1)}'),
              Text('Trust Level: ${_getTrustLevelText(trustProvider.trustLevel)}'),
              Text('Monitoring: ${trustProvider.isMonitoring ? "Active" : "Inactive"}'),
              const SizedBox(height: 16),
              if (behavioralData != null) ...[
                const Text('Current Behavioral Patterns:', style: TextStyle(fontWeight: FontWeight.bold)),
                Text('• Tap pressure: ${behavioralData.averageTapPressure.toStringAsFixed(2)}'),
                Text('• Swipe velocity: ${behavioralData.averageSwipeVelocity.toStringAsFixed(0)} px/s'),
                Text('• Device tilt: ${behavioralData.deviceTiltVariation.toStringAsFixed(2)}'),
                Text('• Session duration: ${(behavioralData.sessionDuration / 60).toStringAsFixed(1)} min'),
              ] else ...[
                const Text('No behavioral data available'),
              ],
              const SizedBox(height: 16),
              Text('Risk Factors: ${trustProvider.riskFactors.length}'),
              ...trustProvider.riskFactors.map((factor) => Text('• $factor')),
            ],
          ),
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
}