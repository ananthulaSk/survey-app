import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/voter.dart';
import 'package:flutter/foundation.dart';

class ApiService {
  // Current Survey Context
  int? currentSurveyId;

  // Dynamic URL selection for Android Emulator vs Windows/Web
  String get baseUrl {
    if (kIsWeb) {
      return "http://127.0.0.1:8000";
    }
    // For mobile (Android/iOS)
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
    final response = await http.get(Uri.parse('$baseUrl/surveys/active'));
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
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

  Future<Voter?> getNextVoter(int currentId) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    final response = await http.get(
      Uri.parse(
        '$baseUrl/voters/next?current_id=$currentId&survey_id=$currentSurveyId',
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

  Future<Voter?> getPreviousVoter(int currentId) async {
    if (currentSurveyId == null) throw Exception("No survey selected");

    final response = await http.get(
      Uri.parse(
        '$baseUrl/voters/previous?current_id=$currentId&survey_id=$currentSurveyId',
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
}
