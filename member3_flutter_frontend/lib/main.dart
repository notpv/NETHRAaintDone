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

class NethraBankingApp extends StatelessWidget {
  const NethraBankingApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        // Core services as singletons
        Provider<ApiService>(
          create: (_) => ApiService(),
          dispose: (_, service) => service.dispose(),
        ),
        Provider<FirebaseService>(
          create: (_) => FirebaseService(),
          dispose: (_, service) => service.dispose(),
        ),
        Provider<PersonalizationService>(
          create: (_) => PersonalizationService(),
        ),
        
        // Authentication provider
        ChangeNotifierProvider<AuthProvider>(
          create: (context) => AuthProvider(),
          dispose: (_, provider) => provider.dispose(),
        ),
        
        // Trust provider - single instance
        ChangeNotifierProvider<TrustProvider>(
          create: (context) => TrustProvider(
            authProvider: Provider.of<AuthProvider>(context, listen: false),
          ),
          dispose: (_, provider) => provider.dispose(),
        ),
        
        // Personalization provider
        ChangeNotifierProvider<PersonalizationProvider>(
          create: (context) => PersonalizationProvider(
            Provider.of<PersonalizationService>(context, listen: false),
          ),
          dispose: (_, provider) => provider.dispose(),
        ),
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
    } catch (e) {
      // Log error but don't crash the app
      if (kDebugMode) {
        print('⚠️ App initialization error: $e');
      }
    }
  }
}