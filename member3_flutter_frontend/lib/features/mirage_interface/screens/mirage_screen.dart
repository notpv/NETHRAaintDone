import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:provider/provider.dart';
import '../../../core/themes/app_theme.dart';
import '../../../shared/widgets/behavioral_wrapper.dart';
import '../../trust_monitor/providers/trust_provider.dart';
import '../../authentication/providers/auth_provider.dart';

class MirageScreen extends StatefulWidget {
  const MirageScreen({super.key});

  @override
  State<MirageScreen> createState() => _MirageScreenState();
}

class _MirageScreenState extends State<MirageScreen>
    with TickerProviderStateMixin {
  late AnimationController _glitchController;
  late AnimationController _fadeController;
  bool _showChallenge = false;
  int _challengeStep = 0;
  final List<bool> _challengeResponses = [false, false, false];
  Map<String, dynamic>? _fakeAccountData;
  bool _loadingFakeData = true;

  @override
  void initState() {
    super.initState();
    _glitchController = AnimationController(
      duration: const Duration(milliseconds: 200),
      vsync: this,
    );
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    // Start the mirage sequence
    _startMirageSequence();
    _loadFakeAccountData();
  }

  @override
  void dispose() {
    _glitchController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  void _startMirageSequence() async {
    // Initial glitch effect
    await Future.delayed(const Duration(milliseconds: 500));
    _glitchController.forward();

    // Show challenge after a delay
    await Future.delayed(const Duration(seconds: 2));
    setState(() {
      _showChallenge = true;
    });
    _fadeController.forward();
  }
  
  void _loadFakeAccountData() async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      if (authProvider.userId != null) {
        final userId = int.tryParse(authProvider.userId!) ?? 1;
        final fakeData = await authProvider.apiService.getFakeAccountData(userId);
        
        setState(() {
          _fakeAccountData = fakeData;
          _loadingFakeData = false;
        });
      }
    } catch (e) {
      // Use fallback fake data
      setState(() {
        _fakeAccountData = _generateFallbackFakeData();
        _loadingFakeData = false;
      });
    }
  }
  
  Map<String, dynamic> _generateFallbackFakeData() {
    return {
      'account_balance': 5500000.00, // ₹55 Lakhs - inflated for mirage
      'available_balance': 5200000.00,
      'recent_transactions': [
        {
          'id': 'TXN_FAKE_001',
          'type': 'Business Revenue',
          'amount': 500000, // ₹5 Lakhs
          'direction': 'credit',
          'timestamp': DateTime.now().subtract(const Duration(hours: 2)).toIso8601String(),
          'description': 'Large Business Payment - Mirage Generated',
        },
        {
          'id': 'TXN_FAKE_002',
          'type': 'Investment Return',
          'amount': 250000, // ₹2.5 Lakhs
          'direction': 'credit',
          'timestamp': DateTime.now().subtract(const Duration(days: 1)).toIso8601String(),
          'description': 'Stock Portfolio Gains - Mirage Generated',
        }
      ],
      'account_number': '****8847',
      'account_type': 'Premium Business Checking',
      'mirage_active': true,
    };
  }

  @override
  Widget build(BuildContext context) {
    return BehavioralWrapper(
      child: Scaffold(
        backgroundColor: AppTheme.backgroundColor,
        body: Stack(
          children: [
            // Main mirage interface
            _buildMirageInterface(),
            
            // Glitch overlay
            AnimatedBuilder(
              animation: _glitchController,
              builder: (context, child) {
                return _glitchController.isAnimating
                    ? Container(
                        color: Colors.red.withOpacity(0.1),
                        child: Center(
                          child: Text(
                            'SYSTEM ERROR',
                            style: Theme.of(context).textTheme.displayMedium?.copyWith(
                              color: Colors.red,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      )
                    : const SizedBox.shrink();
              },
            ),
            
            // Cognitive challenge overlay
            if (_showChallenge)
              AnimatedBuilder(
                animation: _fadeController,
                builder: (context, child) {
                  return Opacity(
                    opacity: _fadeController.value,
                    child: _buildCognitiveChallenge(),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildMirageInterface() {
    return SafeArea(
      child: Column(
        children: [
          // Normal app bar - identical to regular dashboard
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.surfaceColor,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              children: [
                const Icon(Icons.account_balance, color: AppTheme.primaryColor),
                const SizedBox(width: 12),
                Text(
                  'NETHRA Banking',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppTheme.primaryColor,
                  ),
                ),
                const Spacer(),
                Icon(
                  Icons.notifications_outlined,
                  color: AppTheme.textSecondary,
                ),
              ],
            ),
          ),
          
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  // Fake account balance with loading shimmer
                  _buildFakeAccountCard(),
                  const SizedBox(height: 24),
                  
                  // Fake transaction list
                  _buildFakeTransactionList(),
                  const SizedBox(height: 24),
                  
                  // Fake error message
                  _buildFakeErrorMessage(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFakeAccountCard() {
    final balance = _fakeAccountData?['account_balance'] ?? 0.0;
    final accountType = _fakeAccountData?['account_type'] ?? 'Premium Account';
    
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
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
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Account Balance',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: Colors.white.withOpacity(0.9),
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '₹${_formatIndianCurrency(balance)}',
                    style: Theme.of(context).textTheme.displayMedium?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.account_balance_wallet,
                  color: Colors.white,
                  size: 32,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.savings,
                            color: Colors.white,
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Account Type',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Savings',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.credit_card,
                            color: Colors.white,
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'Account Number',
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '****2847',
                        style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.15),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: Colors.white.withOpacity(0.2),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.security,
                  color: Colors.white,
                  size: 20,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Protected by NETHRA',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        'Continuous behavioral authentication',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.white.withOpacity(0.8),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.successColor,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    'ACTIVE',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 10,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              const Spacer(),
              Icon(
                Icons.refresh,
                color: Colors.white,
              ).animate(onPlay: (controller) => controller.repeat())
                  .rotate(duration: 2.seconds),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFakeTransactionList() {
    final transactions = _fakeAccountData?['recent_transactions'] as List<dynamic>? ?? [];
    
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
            'Recent Transactions',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 16),
          if (transactions.isEmpty)
            ...List.generate(3, (index) => _buildFakeTransactionItem(index))
          else
            ...transactions.map((transaction) => _buildFakeTransactionItemFromData(transaction)).toList(),
        ],
      ),
    );
  }

  Widget _buildFakeTransactionItem(int index) {
    final fakeTransactions = [
      {'title': 'Payment Processing...', 'amount': '- \$---.--', 'loading': true},
      {'title': 'Transfer Failed', 'amount': '- \$500.00', 'loading': false},
      {'title': 'Deposit Pending', 'amount': '+ \$---.--', 'loading': true},
    ];
    
    final transaction = fakeTransactions[index];
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: transaction['loading'] as bool
              ? AppTheme.warningColor.withOpacity(0.3)
              : AppTheme.errorColor.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: transaction['loading'] as bool
                  ? AppTheme.warningColor.withOpacity(0.2)
                  : AppTheme.errorColor.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              transaction['loading'] as bool
                  ? Icons.hourglass_empty
                  : Icons.error_outline,
              color: transaction['loading'] as bool
                  ? AppTheme.warningColor
                  : AppTheme.errorColor,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  transaction['title'] as String,
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  'Processing...',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          if (transaction['loading'] as bool)
            SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: AppTheme.warningColor,
              ),
            )
          else
            Text(
              '₹${_formatIndianCurrency(balance)}',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppTheme.errorColor,
              ),
            ),
        ],
      ),
    );
  }
  
  Widget _buildFakeTransactionItemFromData(Map<String, dynamic> transaction) {
    final amount = transaction['amount'] ?? 0;
    final isCredit = transaction['direction'] == 'credit';
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.backgroundColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: AppTheme.successColor.withOpacity(0.3),
        ),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppTheme.successColor.withOpacity(0.2),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              isCredit ? Icons.arrow_downward : Icons.arrow_upward,
              color: AppTheme.successColor,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  transaction['type'] ?? 'Unknown Transaction',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                Text(
                  transaction['description'] ?? 'Mirage Generated',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          Text(
            '${isCredit ? '+' : '-'} ₹${_formatIndianCurrency(amount.toDouble())}',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              fontWeight: FontWeight.bold,
              color: isCredit ? AppTheme.successColor : AppTheme.errorColor,
            ),
          ),
        ],
      ),
    );
  }
  
  String _formatIndianCurrency(double amount) {
    // Format number in Indian style (lakhs, crores)
    if (amount >= 10000000) {
      return '${(amount / 10000000).toStringAsFixed(2)} Cr';
    } else if (amount >= 100000) {
      return '${(amount / 100000).toStringAsFixed(2)} L';
    } else if (amount >= 1000) {
      return '${(amount / 1000).toStringAsFixed(2)} K';
    } else {
      return amount.toStringAsFixed(2);
    }
  }

  Widget _buildFakeErrorMessage() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.errorColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppTheme.errorColor.withOpacity(0.3),
        ),
      ),
      child: Column(
        children: [
          Icon(
            Icons.error_outline,
            color: AppTheme.errorColor,
            size: 48,
          ),
          const SizedBox(height: 16),
          Text(
            'System Maintenance',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: AppTheme.errorColor,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Some features may be temporarily unavailable. Please try again later.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppTheme.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildCognitiveChallenge() {
    return Container(
      color: Colors.black.withOpacity(0.8),
      child: Center(
        child: Container(
          margin: const EdgeInsets.all(32),
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: AppTheme.surfaceColor,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.security,
                    color: AppTheme.primaryColor,
                    size: 32,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Security Verification',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: AppTheme.primaryColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Text(
                'Please complete the following challenge to verify your identity:',
                style: Theme.of(context).textTheme.bodyLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              _buildChallengeStep(),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () {
                      // Simulate failed challenge
                      _handleChallengeResponse(false);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.errorColor,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Cancel'),
                  ),
                  ElevatedButton(
                    onPressed: () {
                      // Simulate successful challenge
                      _handleChallengeResponse(true);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.successColor,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Verify'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChallengeStep() {
    final challenges = [
      {
        'question': 'Tap the blue circle',
        'widget': Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            _buildChallengeButton(Colors.red, false),
            _buildChallengeButton(Colors.blue, true),
            _buildChallengeButton(Colors.green, false),
          ],
        ),
      },
      {
        'question': 'Enter your favorite color',
        'widget': TextField(
          decoration: const InputDecoration(
            hintText: 'Enter color name',
            border: OutlineInputBorder(),
          ),
        ),
      },
      {
        'question': 'Swipe right to continue',
        'widget': GestureDetector(
          onPanUpdate: (details) {
            if (details.delta.dx > 10) {
              _handleChallengeResponse(true);
            }
          },
          child: Container(
            width: double.infinity,
            height: 60,
            decoration: BoxDecoration(
              color: AppTheme.primaryColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.primaryColor),
            ),
            child: Center(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.arrow_forward,
                    color: AppTheme.primaryColor,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Swipe Right',
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                      color: AppTheme.primaryColor,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      },
    ];

    final currentChallenge = challenges[_challengeStep % challenges.length];

    return Column(
      children: [
        Text(
          currentChallenge['question'] as String,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.w600,
          ),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        currentChallenge['widget'] as Widget,
      ],
    );
  }

  Widget _buildChallengeButton(Color color, bool isCorrect) {
    return GestureDetector(
      onTap: () => _handleChallengeResponse(isCorrect),
      child: Container(
        width: 60,
        height: 60,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
      ),
    );
  }

  void _handleChallengeResponse(bool isCorrect) {
    _challengeResponses[_challengeStep] = isCorrect;
    
    if (_challengeStep < 2) {
      setState(() {
        _challengeStep++;
      });
    } else {
      // Challenge completed, exit mirage
      final trustProvider = Provider.of<TrustProvider>(context, listen: false);
      trustProvider.resetTrust();
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Identity verified. Access restored.'),
          backgroundColor: AppTheme.successColor,
        ),
      );
    }
  }
}