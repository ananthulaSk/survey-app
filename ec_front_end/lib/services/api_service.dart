import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/voter.dart';

import 'dart:io';
import 'package:flutter/foundation.dart';

class ApiService {
  // Dynamic URL selection for Android Emulator vs Windows/Web
  String get baseUrl {
    if (!kIsWeb && Platform.isAndroid) {
      return "http://10.0.2.2:8000";
    }
    return "http://127.0.0.1:8000";
  }

  Future<List<Voter>> searchVoters(String query) async {
    final response = await http.get(
      Uri.parse('$baseUrl/voters/search?query=$query'),
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((json) => Voter.fromJson(json)).toList();
    } else {
      throw Exception("Could not fetch voter data");
    }
  }

  Future<bool> updateVoter(int voterId, Map<String, dynamic> updates) async {
    // Add voter_id to the body
    final body = {"voter_id": voterId, ...updates};

    final response = await http.put(
      Uri.parse(
        '$baseUrl/voters/update',
      ), // Query params not needed for body-based PUT
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(body),
    );
    return response.statusCode == 200;
  }

  Future<Voter?> getNextVoter(int currentId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/voters/next?current_id=$currentId'),
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
    final response = await http.get(
      Uri.parse('$baseUrl/voters/previous?current_id=$currentId'),
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
    String url = '$baseUrl/voters/stats';
    List<String> params = [];
    if (ward != null) params.add('ward=$ward');
    if (currentVoterId != null) params.add('current_voter_id=$currentVoterId');

    if (params.isNotEmpty) url += '?${params.join('&')}';

    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return {
        "total": data['total'],
        "completed": data['completed'],
        "current_index": data['current_index'] ?? 0,
      };
    }
    return {"total": 0, "completed": 0, "current_index": 0};
  }
}
