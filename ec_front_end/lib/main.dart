import 'package:ec_front_end/services/offline_service.dart';
import 'package:flutter/material.dart';
import 'screens/registration_screen.dart';
import 'screens/admin_login_screen.dart'; // Admin Auth

import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await OfflineService.init(); // Initialize Hive

  // Start Background Sync Service
  OfflineService().startAutoSync();

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
      // DYNAMIC HOME SCREEN based on URL
      // If we are on the Admin Dashboard Link (/static/), show AdminAuth.
      // If we are on the Mobile App Link (/app/), show Registration.
      home: Uri.base.toString().contains("/static/")
          ? const AdminLoginScreen()
          : const RegistrationScreen(),
    );
  }
}
