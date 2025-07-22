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
        // Core services
        Provider(create: (_) => ApiService()),
        Provider(create: (_) => FirebaseService()),
        Provider(create: (_) => PersonalizationService()),
        
        // Authentication provider
        ChangeNotifierProvider(
          create: (context) => AuthProvider(),
        ),
        
        // Trust provider with dependencies
        ChangeNotifierProxyProvider<AuthProvider, TrustProvider>(
          create: (context) => TrustProvider(),
          update: (context, authProvider, previous) => 
            TrustProvider(authProvider: authProvider),
        ),
        
        // Personalization provider
        ChangeNotifierProxyProvider<PersonalizationService, PersonalizationProvider>(
          create: (context) => PersonalizationProvider(
            Provider.of<PersonalizationService>(context, listen: false),
          ),
          update: (context, personalizationService, previous) => 
            PersonalizationProvider(personalizationService),
        ),
      ],
      child: Consumer<AuthProvider>(
        builder: (context, authProvider, child) {
          return MaterialApp(
            title: 'NETHRA Banking',
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            home: FirebaseNotificationListener(
             // Initialize in background without blocking UI
             WidgetsBinding.instance.addPostFrameCallback((_) {
               _initializeAppInBackground(authProvider);
             });
             
             // Show UI immediately based on current auth status
             return authProvider.isAuthenticated
                 ? const DashboardScreen()
                 : const LoginScreen();
            ),
          );
        },
      ),
    );
  }
  
  Future<void> _initializeApp(AuthProvider authProvider) async {
    try {
     // Initialize without blocking UI
     authProvider.checkAuthStatus();
    } catch (e) {
      // Log error but don't crash the app
      if (kDebugMode) {
        print('⚠️ App initialization error: $e');
      }
    }
  }
}

class NethraSplashScreen extends StatelessWidget {
  const NethraSplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.primaryColor,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 120,
              height: 120,
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.security,
                size: 60,
                color: AppTheme.primaryColor,
              ),
            ),
            const SizedBox(height: 32),
            Text(
              'NETHRA',
              style: Theme.of(context).textTheme.displayLarge?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'AI-Powered Banking Security',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Colors.white.withOpacity(0.9),
              ),
            ),
            const SizedBox(height: 48),
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ],
        ),
      ),
    );
  }
}
 void _initializeAppInBackground(AuthProvider authProvider) async {