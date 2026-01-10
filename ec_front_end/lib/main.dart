import 'package:flutter/material.dart';
import 'screens/registration_screen.dart';

import 'services/api_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
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
