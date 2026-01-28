import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'approval_screen.dart'; // For logout/redirect if needed

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _api = ApiService();
  Map<String, dynamic>? _summary;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    // For now, checking version or just basic stats.
    // Real dashboard needs a Survey ID context, which might not be selected yet for Admin?
    // Or Admin sees global stats?
    // For this Hotfix, we just show the "Admin Portal" placeholder.
    setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Admin Dashboard"),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              // Logout Logic here
              Navigator.of(context).pop();
            },
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.admin_panel_settings,
              size: 80,
              color: Colors.indigo,
            ),
            const SizedBox(height: 20),
            const Text(
              "Welcome, Coordinator",
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            _isLoading
                ? const CircularProgressIndicator()
                : const Text("Dashboard metrics coming soon..."),
          ],
        ),
      ),
    );
  }
}
