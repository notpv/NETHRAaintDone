class AppConstants {
  static const String appName = 'NETHRA Banking';
  static const String baseUrl = 'http://127.0.0.1:8000'; // Local development
  // For iOS simulator, use: 'http://127.0.0.1:8000'
  // For physical device, use your computer's IP: 'http://192.168.1.XXX:8000'
  // For Android emulator, use: 'http://10.0.2.2:8000'
  
  // Security Settings - Dynamic thresholds removed, now calculated by backend
  static const int maxFailedAttempts = 3;
  static const int sessionTimeoutMinutes = 10;
  static const int trustUpdateIntervalSeconds = 3;
  
  // Demo Data - Updated to Indian Rupees
  static const String demoUsername = 'demo_user';
  static const String demoPassword = 'demo123';
  static const double demoAccountBalance = 2075000.50; // ₹20,75,000.50
  
  // API Endpoints
  static const String authEndpoint = '/api/auth';
  static const String trustEndpoint = '/api/trust';
  static const String userEndpoint = '/api/user';
  static const String monitoringEndpoint = '/api/monitoring';
  static const String sessionEndpoint = '/api/session';
  static const String mirageEndpoint = '/api/mirage';
  
  // Personalization Settings
  static const int minLearningInteractions = 20;
  static const int fullLearningInteractions = 50;
  static const double personalizedThresholdMultiplier = 1.5;
  static const double adaptationRate = 0.1;
  
  // App Colors
  static const int primaryColorValue = 0xFF1E88E5;
  static const int successColorValue = 0xFF4CAF50;
  static const int warningColorValue = 0xFFFF9800;
  static const int errorColorValue = 0xFFE53935;
  
  // Currency Settings
  static const String currencySymbol = '₹';
  static const String currencyCode = 'INR';
  
  // Firebase Configuration
  static const String firebaseProjectId = 'nethra-banking-security';
  static const String firebaseSenderId = '123456789';
  static const String firebaseAppId = '1:123456789:android:abcdef';
}