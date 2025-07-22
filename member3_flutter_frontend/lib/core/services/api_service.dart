import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants/app_constants.dart';
import '../../shared/models/trust_data.dart';
import '../../shared/models/behavioral_data.dart';

class ApiService {
  static const String baseUrl = AppConstants.baseUrl;
  String? _authToken;
  
  void setAuthToken(String token) {
    _authToken = token;
  }
  
  Map<String, String> get _headers {
    final headers = {
      'Content-Type': 'application/json',
    };
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  // Authentication APIs
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl${AppConstants.authEndpoint}/login'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: {
          'username': username,
          'password': password,
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['access_token'] != null) {
          setAuthToken(data['access_token']);
        }
        return data;
      } else {
        throw Exception('Login failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during login: $e');
    }
  }

  Future<Map<String, dynamic>> register(String username, String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl${AppConstants.authEndpoint}/register'),
        headers: _headers,
        body: jsonEncode({
          'username': username,
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['access_token'] != null) {
          setAuthToken(data['access_token']);
        }
        return data;
      } else {
        throw Exception('Registration failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during registration: $e');
    }
  }

  Future<bool> validateToken() async {
    if (_authToken == null) return false;
    
    try {
      final response = await http.post(
        Uri.parse('$baseUrl${AppConstants.authEndpoint}/validate-token'),
        headers: _headers,
      );

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<void> logout() async {
    try {
      await http.post(
        Uri.parse('$baseUrl${AppConstants.authEndpoint}/logout'),
        headers: _headers,
      );
    } catch (e) {
      // Ignore logout errors
    } finally {
      _authToken = null;
    }
  }

  // Trust Score APIs
  Future<Map<String, dynamic>> predictTrustScore(Map<String, dynamic> behavioralData) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl${AppConstants.trustEndpoint}/predict-trust'),
        headers: _headers,
        body: jsonEncode(behavioralData),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Trust prediction failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during trust prediction: $e');
    }
  }

  Future<Map<String, dynamic>> getThresholdAnalysis(int userId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.trustEndpoint}/threshold-analysis/$userId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Threshold analysis failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during threshold analysis: $e');
    }
  }

  Future<Map<String, dynamic>> getTrustHistory(int userId, {int limit = 20}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.trustEndpoint}/user-trust-history/$userId?limit=$limit'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Trust history failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during trust history: $e');
    }
  }

  // Session Management APIs
  Future<Map<String, dynamic>> createSession({Map<String, dynamic>? deviceInfo}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl${AppConstants.sessionEndpoint}/create'),
        headers: _headers,
        body: jsonEncode({
          'device_info': deviceInfo ?? {},
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Session creation failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during session creation: $e');
    }
  }

  Future<Map<String, dynamic>> getSessionStatus(String sessionToken) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.sessionEndpoint}/status/$sessionToken'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Session status failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during session status: $e');
    }
  }

  Future<Map<String, dynamic>> sendHeartbeat(String sessionToken) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl${AppConstants.sessionEndpoint}/heartbeat/$sessionToken'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Heartbeat failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during heartbeat: $e');
    }
  }

  // Mirage Interface APIs
  Future<Map<String, dynamic>> getMirageStatus(int userId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.mirageEndpoint}/status/$userId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Mirage status failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during mirage status: $e');
    }
  }

  Future<Map<String, dynamic>> getFakeAccountData(int userId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.mirageEndpoint}/fake-data/$userId'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Fake data failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during fake data: $e');
    }
  }

  // User Profile APIs
  Future<Map<String, dynamic>> getUserProfile() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.userEndpoint}/profile'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Profile fetch failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during profile fetch: $e');
    }
  }

  Future<Map<String, dynamic>> getTrustStats() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.userEndpoint}/trust-stats'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Trust stats failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during trust stats: $e');
    }
  }

  // Monitoring APIs
  Future<Map<String, dynamic>> getHealthStatus() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.monitoringEndpoint}/health'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during health check: $e');
    }
  }

  Future<Map<String, dynamic>> getSystemMetrics() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl${AppConstants.monitoringEndpoint}/metrics'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Metrics failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error during metrics: $e');
    }
  }

  // Legacy methods for backward compatibility
  Future<TrustData> calculateTrustScore(BehavioralData behavioralData) async {
    try {
      final behavioralMap = {
        'user_id': 1, // This should come from auth state
        'avg_pressure': behavioralData.averageTapPressure,
        'avg_swipe_velocity': behavioralData.averageSwipeVelocity,
        'avg_swipe_duration': behavioralData.averageTapDuration / 1000, // Convert to seconds
        'accel_stability': behavioralData.deviceTiltVariation,
        'gyro_stability': behavioralData.deviceTiltVariation * 0.8, // Simulate gyro
        'touch_frequency': behavioralData.tapCount / (behavioralData.sessionDuration / 60), // Per minute
        'timestamp': behavioralData.timestamp.toIso8601String(),
      };

      final response = await predictTrustScore(behavioralMap);
      
      return TrustData(
        trustScore: response['trust_score']?.toDouble() ?? 50.0,
        trustLevel: _getTrustLevelFromScore(response['trust_score']?.toDouble() ?? 50.0),
        riskFactors: List<String>.from(response['risk_factors'] ?? []),
        timestamp: DateTime.now(),
      );
    } catch (e) {
      throw Exception('Trust score calculation failed: $e');
    }
  }

  TrustLevel _getTrustLevelFromScore(double score) {
    if (score >= 80) return TrustLevel.high;
    if (score >= 60) return TrustLevel.medium;
    if (score >= 40) return TrustLevel.low;
    return TrustLevel.critical;
  }

  Future<Map<String, dynamic>> validateTransaction(Map<String, dynamic> transactionData) async {
    // This would integrate with actual transaction validation
    return {'status': 'validated', 'transaction_id': 'demo_${DateTime.now().millisecondsSinceEpoch}'};
  }

  Future<Map<String, dynamic>> reportTamperAttempt(Map<String, dynamic> tamperData) async {
    // This would report tamper attempts to security monitoring
    return {'status': 'reported', 'incident_id': 'tamper_${DateTime.now().millisecondsSinceEpoch}'};
  }

  Future<bool> authenticateUser(String username, String password) async {
    try {
      final result = await login(username, password);
      return result['access_token'] != null;
    } catch (e) {
      return false;
    }
  }
}