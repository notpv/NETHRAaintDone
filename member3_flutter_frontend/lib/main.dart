import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'core/themes/app_theme.dart';
import 'core/services/behavioral_service.dart';
import 'core/services/api_service.dart';
import 'core/services/firebase_service.dart';
import 'features/authentication/screens/login_screen.dart';
import 'features/dashboard/screens/dashboard_screen.dart';
import 'features/trust_monitor/providers/trust_provider.dart';
import 'features/authentication/providers/auth_provider.dart';
import 'features/personalization/providers/personalization_provider.dart';
import 'core/services/personalization_service.dart';
import 'features/demo/providers/demo_provider.dart';
import 'core/services/email_alert_service.dart';
import 'core/services/audit_service.dart';
import 'shared/widgets/firebase_notification_listener.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
      systemNavigationBarColor: Colors.white,
      systemNavigationBarIconBrightness: Brightness.dark,
    ),
  );

  runApp(const NethraBankingApp());
}

class NethraBankingApp extends StatefulWidget {
  const NethraBankingApp({super.key});

  @override
  State<NethraBankingApp> createState() => _NethraBankingAppState();
}

class _NethraBankingAppState extends State<NethraBankingApp> {
  late final ApiService _apiService;
  late final FirebaseService _firebaseService;
  late final PersonalizationService _personalizationService;
  late final EmailAlertService _emailAlertService;
  late final AuditService _auditService;
  late final AuthProvider _authProvider;
  late final TrustProvider _trustProvider;
  late final PersonalizationProvider _personalizationProvider;
  late final DemoProvider _demoProvider;

  @override
  void initState() {
    super.initState();
    
    // Initialize services
    _apiService = ApiService();
    _firebaseService = FirebaseService();
    _personalizationService = PersonalizationService();
    _emailAlertService = EmailAlertService();
    _auditService = AuditService();
    
    // Initialize providers
    _authProvider = AuthProvider();
    _trustProvider = TrustProvider(authProvider: _authProvider);
    _personalizationProvider = PersonalizationProvider(_personalizationService);
    _demoProvider = DemoProvider(_apiService, _firebaseService);
  }

  @override
  void dispose() {
    // Dispose in reverse order
    _demoProvider.dispose();
    _trustProvider.dispose();
    _authProvider.dispose();
    _auditService.dispose();
    _apiService.dispose();
    _firebaseService.dispose();
    
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Core services
        Provider<ApiService>.value(value: _apiService),
        Provider<FirebaseService>.value(value: _firebaseService),
        Provider<PersonalizationService>.value(value: _personalizationService),
        Provider<EmailAlertService>.value(value: _emailAlertService),
        Provider<AuditService>.value(value: _auditService),
        
        // Providers
        ChangeNotifierProvider<AuthProvider>.value(value: _authProvider),
        ChangeNotifierProvider<TrustProvider>.value(value: _trustProvider),
        ChangeNotifierProvider<PersonalizationProvider>.value(value: _personalizationProvider),
        ChangeNotifierProvider<DemoProvider>.value(value: _demoProvider),
      ],
      child: Consumer<AuthProvider>(
        builder: (context, authProvider, child) {
          return MaterialApp(
            title: 'NETHRA Banking',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            home: FirebaseNotificationListener(
              child: _buildHome(authProvider),
            ),
          );
        },
      ),
    );
  }
  
  Widget _buildHome(AuthProvider authProvider) {
    // Initialize app in background without blocking UI
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeAppInBackground(authProvider);
    });
    
    // Show UI immediately based on current auth status
    return authProvider.isAuthenticated
        ? const DashboardScreen()
        : const LoginScreen();
  }
  
  void _initializeAppInBackground(AuthProvider authProvider) async {
    try {
      // Initialize without blocking UI
      await authProvider.initialize();
      
      if (kDebugMode) {
        print('✅ App initialized successfully');
      }
    } catch (e) {
      // Log error but don't crash the app
      if (kDebugMode) {
        print('⚠️ App initialization error (non-critical): $e');
      }
    }
  }
}