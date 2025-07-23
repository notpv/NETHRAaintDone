import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../core/themes/app_theme.dart';

class QuickActions extends StatelessWidget {
  final VoidCallback? onTransfer;
  final VoidCallback? onPayBills;
  final VoidCallback? onDeposit;
  final VoidCallback? onMoreActions;

  const QuickActions({
    super.key,
    this.onTransfer,
    this.onPayBills,
    this.onDeposit,
    this.onMoreActions,
  });

  @override
  Widget build(BuildContext context) {
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
            'Quick Actions',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              _buildQuickActionButton(
                context,
                icon: Icons.send,
                label: 'Transfer',
                color: AppTheme.primaryColor,
                onTap: onTransfer,
              ).animate(delay: 100.ms).scale(),
              _buildQuickActionButton(
                context,
                icon: Icons.receipt,
                label: 'Pay Bills',
                color: AppTheme.accentColor,
                onTap: onPayBills,
              ).animate(delay: 200.ms).scale(),
              _buildQuickActionButton(
                context,
                icon: Icons.account_balance,
                label: 'Deposit',
                color: AppTheme.successColor,
                onTap: onDeposit,
              ).animate(delay: 300.ms).scale(),
              _buildQuickActionButton(
                context,
                icon: Icons.more_horiz,
                label: 'More',
                color: AppTheme.warningColor,
                onTap: onMoreActions,
              ).animate(delay: 400.ms).scale(),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required Color color,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap ?? () => _showPlaceholderAction(context, label, color),
      child: Column(
        children: [
          Container(
            width: 64,
            height: 64,
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: color.withOpacity(0.2),
              ),
            ),
            child: Icon(
              icon,
              color: color,
              size: 28,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppTheme.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
  
  void _showPlaceholderAction(BuildContext context, String label, Color color) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.construction, color: color),
            const SizedBox(width: 12),
            Text('$label Feature'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('The $label feature is coming soon!'),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'This would normally take you to the $label screen with full functionality.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
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
  }
}