import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/voter.dart';
import 'package:flutter/foundation.dart';

class ApiService {
  // Current Survey Context
  int? currentSurveyId;

  // Session Context (Simple In-Memory)
  static String? loggedInMobile;
  static int? loggedInSurveyorId;

  // Dynamic URL selection
  String get baseUrl {
    if (kIsWeb) {
      // 1. Hardcoded Production URL for reliability
      if (Uri.base.toString().contains("run.app")) {
        print("Using Hardcoded Prod URL");
        return "https://survey-app-75558224521.asia-south1.run.app";
      }

      // 2. Dynamic Localhost/Self-Hosted fallback
      if (Uri.base.host != 'localhost' && Uri.base.host != '127.0.0.1') {
        return Uri.base.origin;
      }

      // 3. Localhost Dev
      if (Uri.base.port == 8000) return Uri.base.origin;
      return "http://127.0.0.1:8000";
    }

    // Android Emulator
    return "http://10.0.2.2:8000";
  }

  // --- Survey Management ---

  Future<Map<String, dynamic>> createSurvey(
    String name,
    String scopeType,
    String scopeValue,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/surveys/create'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "name": name,
        "scope_type": scopeType,
        "scope_value": scopeValue,
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to create survey: ${response.body}');
  }

  Future<List<dynamic>> getActiveSurveys() async {
    String url = '$baseUrl/surveys/active';
    if (loggedInMobile != null) {
      url += '?mobile_no=$loggedInMobile';
    }

    print("Fetching surveys from: $url");
    try {
      final response = await http.get(Uri.parse(url));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("Error fetching active surveys: $e");
    }
    return [];
  }

  // --- Voter Operations (Snapshot Aware) ---

  Future<List<Voter>> searchVoters(String query) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    final response = await http.get(
      Uri.parse(
        '$baseUrl/voters/search?query=$query&survey_id=$currentSurveyId',
      ),
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((json) => Voter.fromJson(json)).toList();
    } else {
      throw Exception("Could not fetch voter data");
    }
  }

  Future<bool> updateVoter(int voterId, Map<String, dynamic> updates) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    // Add voter_id and survey_id to the body
    final body = {
      "voter_id": voterId,
      "survey_id": currentSurveyId,
      ...updates,
    };

    final response = await http.put(
      Uri.parse('$baseUrl/voters/update'),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(body),
    );
    return response.statusCode == 200;
  }

  Future<Voter?> getNextVoter(
    int currentId, {
    bool skipCompleted = true,
  }) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    final response = await http.get(
      Uri.parse(
        '$baseUrl/voters/next?current_id=$currentId&survey_id=$currentSurveyId&skip_completed=$skipCompleted',
      ),
    );
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      if (json['status'] == 'success' && json['data'] != null) {
        return Voter.fromJson(json['data']);
      }
    }
    return null;
  }

  Future<Voter?> getPreviousVoter(
    int currentId, {
    bool skipCompleted = true,
  }) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    final response = await http.get(
      Uri.parse(
        '$baseUrl/voters/previous?current_id=$currentId&survey_id=$currentSurveyId&skip_completed=$skipCompleted',
      ),
    );
    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      if (json['status'] == 'success' && json['data'] != null) {
        return Voter.fromJson(json['data']);
      }
    }
    return null;
  }

  Future<Voter?> getVoterById(int voterId) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    final response = await http.get(
      Uri.parse('$baseUrl/voters/$voterId?survey_id=$currentSurveyId'),
    );

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body);
      if (json['status'] == 'success' && json['data'] != null) {
        return Voter.fromJson(json['data']);
      }
    }
    return null;
  }

  Future<Voter?> getFirstVoter() async {
    // Pass 0 to get the very first one relative to 0
    return getNextVoter(0);
  }

  Future<Map<String, int>> getStats({int? ward, int? currentVoterId}) async {
    // If no survey, return empty stats
    if (currentSurveyId == null)
      return {"total": 0, "completed": 0, "current_index": 0};

    String url = '$baseUrl/voters/stats';
    List<String> params = [];
    params.add('survey_id=$currentSurveyId');

    if (ward != null) params.add('ward=$ward');
    if (currentVoterId != null) params.add('current_voter_id=$currentVoterId');

    if (params.isNotEmpty) url += '?${params.join('&')}';

    print("Fetching stats from: $url");
    try {
      final response = await http.get(Uri.parse(url));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          "total": data['total'],
          "completed": data['completed'],
          "current_index": data['current_index'] ?? 0,
        };
      } else {
        print("Stats fetch failed with status: ${response.statusCode}");
      }
    } catch (e) {
      print("Error fetching stats: $e");
    }
    return {"total": 0, "completed": 0, "current_index": 0};
  }

  // --- Dashboard Methods ---

  Future<Map<String, dynamic>> getDashboardSummary() async {
    if (currentSurveyId == null) throw Exception("No survey selected");
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/summary?survey_id=$currentSurveyId'),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['data'];
    }
    throw Exception("Failed to load summary");
  }

  Future<List<dynamic>> getDashboardProgress() async {
    if (currentSurveyId == null) throw Exception("No survey selected");
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/progress?survey_id=$currentSurveyId'),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['data'];
    }
    throw Exception("Failed to load progress");
  }

  Future<Map<String, dynamic>> getDashboardAnalytics() async {
    if (currentSurveyId == null) throw Exception("No survey selected");
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/analytics?survey_id=$currentSurveyId'),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body); // Returns {status, total_polled, data}
    }
    throw Exception("Failed to load analytics");
  }

  Future<List<dynamic>> getPendingApprovals() async {
    final response = await http.get(Uri.parse('$baseUrl/dashboard/approvals'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  Future<bool> approveSurveyor(int requestId, String action) async {
    final response = await http.post(
      Uri.parse('$baseUrl/dashboard/approve'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({"request_id": requestId, "action": action}),
    );
    return response.statusCode == 200;
  }

  Future<Map<String, dynamic>> registerSurveyor(
    String name,
    String mobile,
  ) async {
    final url = Uri.parse('$baseUrl/register/surveyor');
    print("Attempting Registration to: $url");

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "name": name,
        "mobile": mobile,
        "device_id": "device_${DateTime.now().millisecondsSinceEpoch}",
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception("Registration failed: ${response.statusCode}");
  }

  // --- NEW: Polling Status ---
  Future<String> checkStatusByMobile(String mobile) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/register/status/mobile?mobile_no=$mobile'),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['surveyor_id'] != null) {
          loggedInSurveyorId = data['surveyor_id'];
        }
        return data['approval_status'] ?? 'PENDING';
      }
    } catch (e) {
      print("Check status failed: $e");
    }
    return 'PENDING'; // Default
  }
}
