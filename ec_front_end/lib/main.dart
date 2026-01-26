import 'package:ec_front_end/services/offline_service.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:flutter/material.dart';
import 'screens/registration_screen.dart';

import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await OfflineService.init(); // Initialize Hive
  await ApiService.restoreSession();
  runApp(const VoterApp());
}

class VoterApp extends StatelessWidget {
  const VoterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Aregudem Survey',
      theme: ThemeData(primarySwatch: Colors.blue, useMaterial3: true),
      home: const RegistrationScreen(),
    );
  }
}
