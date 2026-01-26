import 'dart:convert';
import 'package:ec_front_end/services/api_service.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:internet_connection_checker/internet_connection_checker.dart';

class OfflineService {
  static const String BOX_NAME = "offline_votes";
  static final OfflineService _instance = OfflineService._internal();

  factory OfflineService() {
    return _instance;
  }

  OfflineService._internal();

  /// Initialize Hive and Open Box
  static Future<void> init() async {
    await Hive.initFlutter();
    await Hive.openBox(BOX_NAME);
  }

  /// Check if device is online
  Future<bool> isOnline() async {
    var connectivityResult = await (Connectivity().checkConnectivity());
    if (connectivityResult == ConnectivityResult.none) {
      return false;
    }
    // Deep check (ping google)
    return await InternetConnectionChecker().hasConnection;
  }

  /// Save Vote Locally (when offline)
  Future<void> saveVoteOffline(Map<String, dynamic> voteData) async {
    final box = Hive.box(BOX_NAME);
    // Add timestamp for sorting/debug
    voteData['_saved_at'] = DateTime.now().toIso8601String();
    await box.add(jsonEncode(voteData));
    print("OFFLINE: Vote Saved. Total Pending: ${box.length}");
  }

  /// Get count of pending votes
  int getPendingCount() {
    final box = Hive.box(BOX_NAME);
    return box.length;
  }

  /// Sync Pending Votes to Server
  /// Returns number of votes successfully synced
  Future<int> syncPendingVotes() async {
    if (!await isOnline()) return 0;

    final box = Hive.box(BOX_NAME);
    if (box.isEmpty) return 0;

    print("SYNC: Found ${box.length} pending votes. Syncing...");

    final ApiService api = ApiService();
    int syncedCount = 0;

    // Convert box values to Map (keys are indices)
    final Map<dynamic, dynamic> rawMap = box.toMap();

    for (var key in rawMap.keys) {
      try {
        final String jsonStr = rawMap[key];
        final Map<String, dynamic> data = jsonDecode(jsonStr);

        // Remove internal metadata
        data.remove('_saved_at');

        // Send to API
        final bool success = await api.updateVoter(
          data['voter_id'],
          data, // survey_data (filtered)
        );

        if (success) {
          await box.delete(key);
          syncedCount++;
        }
      } catch (e) {
        print("SYNC ERROR for key $key: $e");
      }
    }

    print("SYNC: Completed. Synced $syncedCount votes.");
    return syncedCount;
  }
}
