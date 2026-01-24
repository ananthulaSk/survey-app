import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/voter.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // Current Survey Context
  int? currentSurveyId;

  // Session Context (Simple In-Memory)
  static String? loggedInMobile;
  static int? loggedInSurveyorId;
  static String? loggedInWard;

  // Normalization Helper
  static String normalizeMobile(String mobile) {
    return mobile
        .replaceAll("+91", "")
        .replaceAll(" ", "")
        .replaceAll("-", "")
        .trim();
  }

  // Persist Session
  static Future<void> saveSession(
    String mobile,
    int? surveyorId,
    String? ward,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('mobile', normalizeMobile(mobile));
    if (surveyorId != null) {
      await prefs.setInt('surveyor_id', surveyorId);
    }
    if (ward != null) {
      await prefs.setString('ward', ward);
    }
    loggedInMobile = mobile;
    loggedInSurveyorId = surveyorId;
    loggedInWard = ward;
  }

  // Restore Session
  static Future<bool> restoreSession() async {
    final prefs = await SharedPreferences.getInstance();
    final mobile = prefs.getString('mobile');
    final surveyorId = prefs.getInt('surveyor_id');
    final ward = prefs.getString('ward');

    if (mobile != null && mobile.isNotEmpty) {
      loggedInMobile = mobile;
      loggedInSurveyorId = surveyorId;
      loggedInWard = ward;
      return true;
    }
    return false;
  }

  // Dynamic URL selection
  static String get baseUrl {
    // NUCLEAR OPTION: Unconditional Production URL
    // This removes ANY possibility of logic error.
    return "https://survey-app-171882639078.asia-south1.run.app";
  }

  // Check Backend Version
  Future<Map<String, dynamic>> checkBackendVersion() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/version'))
          .timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
    } catch (e) {
      print("Version check failed: $e");
    }
    return {"version": "UNKNOWN", "env": "UNKNOWN"};
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
      url += '?mobile_no=${normalizeMobile(loggedInMobile!)}';
    }

    print("Fetching surveys from: $url");
    try {
      final response = await http
          .get(Uri.parse(url))
          .timeout(const Duration(seconds: 10));
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

    String url =
        '$baseUrl/voters/search?query=$query&survey_id=$currentSurveyId';
    if (loggedInWard != null) {
      // Extract number from "Ward 4" -> 4
      final wardNum = int.tryParse(
        loggedInWard!.replaceAll(RegExp(r'[^0-9]'), ''),
      );
      if (wardNum != null) url += '&ward=$wardNum';
    }

    final response = await http.get(Uri.parse(url));

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

    String url =
        '$baseUrl/voters/next?current_id=$currentId&survey_id=$currentSurveyId&skip_completed=$skipCompleted';
    if (loggedInWard != null) {
      final wardNum = int.tryParse(
        loggedInWard!.replaceAll(RegExp(r'[^0-9]'), ''),
      );
      if (wardNum != null) url += '&ward=$wardNum';
    }

    final response = await http.get(Uri.parse(url));
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

    String url =
        '$baseUrl/voters/previous?current_id=$currentId&survey_id=$currentSurveyId&skip_completed=$skipCompleted';
    if (loggedInWard != null) {
      final wardNum = int.tryParse(
        loggedInWard!.replaceAll(RegExp(r'[^0-9]'), ''),
      );
      if (wardNum != null) url += '&ward=$wardNum';
    }

    final response = await http.get(Uri.parse(url));
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

    if (ward != null)
      params.add('ward=$ward');
    // Auto-inject ward if surveyor
    else if (loggedInWard != null) {
      final wardNum = int.tryParse(
        loggedInWard!.replaceAll(RegExp(r'[^0-9]'), ''),
      );
      if (wardNum != null) params.add('ward=$wardNum');
    }

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

  // --- Location APIs (Phase 1) ---
  Future<List<Map<String, dynamic>>> getDistricts() async {
    final response = await http.get(Uri.parse('$baseUrl/locations/districts'));
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    }
    return [];
  }

  Future<List<Map<String, dynamic>>> getMandals(int districtId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/locations/mandals/$districtId'),
    );
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    }
    return [];
  }

  Future<List<Map<String, dynamic>>> getVillages(int mandalId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/locations/villages/$mandalId'),
    );
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    }
    return [];
  }

  Future<List<Map<String, dynamic>>> getWards(int villageId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/locations/wards/$villageId'),
    );
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    }
    return [];
  }

  Future<Map<String, dynamic>> registerSurveyor(
    String name,
    String mobile, {
    required String district,
    required String mandal,
    required String village,
    required String ward,
  }) async {
    final url = Uri.parse('$baseUrl/register/surveyor');
    print("Attempting Registration to: $url");

    // Sanitize
    mobile = normalizeMobile(mobile);

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        "name": name,
        "mobile": mobile,
        "device_id": "device_${DateTime.now().millisecondsSinceEpoch}",
        "district_name": district,
        "mandal_name": mandal,
        "village_name": village,
        "ward_no": ward,
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
        Uri.parse(
          '$baseUrl/register/status/mobile?mobile_no=${normalizeMobile(mobile)}',
        ),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['surveyor_id'] != null) {
          loggedInSurveyorId = data['surveyor_id'];
        }
        loggedInWard = data['ward_no']; // Capture Ward
        return data['approval_status'] ?? 'PENDING';
      }
    } catch (e) {
      print("Check status failed: $e");
    }
    return 'PENDING'; // Default
  }
}
