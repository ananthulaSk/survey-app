import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import 'approval_screen.dart'; // For logout logic if needed

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with SingleTickerProviderStateMixin {
  final ApiService _api = ApiService();
  late TabController _tabController;

  bool _isLoading = true;
  String? _errorMessage;

  // Analytics Data
  Map<String, dynamic>? _analyticsData;
  int _totalPolled = 0;

  // Team Data
  List<dynamic> _teamRequests = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // 1. Ensure we have a Survey ID (Context)
      if (_api.currentSurveyId == null) {
        final activeSurveys = await _api.getActiveSurveys();
        if (activeSurveys.isNotEmpty) {
          _api.currentSurveyId = activeSurveys.first['id'];
          print("Auto-Selected Survey ID: ${_api.currentSurveyId}");
        } else {
          throw Exception("No Active Survey Found. Please create one.");
        }
      }

      // 2. Fetch Data in Parallel
      final analytics = await _api.getDashboardAnalytics();
      final approvals = await _api.getPendingApprovals();

      if (mounted) {
        setState(() {
          _analyticsData = analytics;
          _totalPolled = analytics['total_polled'] ?? 0;
          _teamRequests = approvals;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  // --- ACTIONS ---

  Future<void> _handleApproval(int id, String action) async {
    // Optimistic Update
    final index = _teamRequests.indexWhere((r) => r['id'] == id);
    if (index == -1) return;

    final originalStatus = _teamRequests[index]['status'];
    setState(() {
      _teamRequests[index]['status'] = action;
    });

    final success = await _api.approveSurveyor(id, action);
    if (!success) {
      // Revert if failed
      if (mounted) {
        setState(() {
          _teamRequests[index]['status'] = originalStatus;
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text("Action Failed")));
      }
    }
  }

  Future<void> _deleteSurveyor(int id) async {
    final success = await _api.deleteSurveyor(id);
    if (success) {
      setState(() {
        _teamRequests.removeWhere((r) => r['id'] == id);
      });
    }
  }

  // --- CREATE SURVEY FLOW ---

  Future<void> _showCreateSurveyDialog() async {
    final nameController = TextEditingController();
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Create New Survey"),
        content: TextField(
          controller: nameController,
          decoration: const InputDecoration(
            labelText: "Survey Name (e.g. Election 2026)",
            hintText: "Enter unique name",
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (nameController.text.isNotEmpty) {
                Navigator.pop(context);
                await _performCreateSurvey(nameController.text);
              }
            },
            child: const Text("Create"),
          ),
        ],
      ),
    );
  }

  Future<void> _performCreateSurvey(String name) async {
    setState(() => _isLoading = true);
    try {
      // Create Default Survey (Global Scope for now)
      final res = await _api.createSurvey(name, "DISTRICT", "ALL");
      // Refresh to load it
      await _loadDashboardData();
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Survey '$name' Created!")));
    } catch (e) {
      setState(() {
        _isLoading = false;
        _errorMessage = "Failed to create: $e";
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Admin Dashboard (v19.73)"),
        backgroundColor: Colors.purpleAccent,
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.pie_chart), text: "Analytics"),
            Tab(icon: Icon(Icons.people), text: "Team"),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDashboardData,
          ),
          IconButton(
            icon: const Icon(Icons.add_chart), // Icon for creating a survey
            onPressed: _showCreateSurveyDialog,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.error_outline,
                    size: 48,
                    color: Colors.orange,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _errorMessage!,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.red),
                  ),
                  const SizedBox(height: 24),
                  // Show "Create Survey" button if the error is "No Active Survey"
                  if (_errorMessage!.contains("No Active Survey"))
                    ElevatedButton.icon(
                      onPressed: _showCreateSurveyDialog,
                      icon: const Icon(Icons.add),
                      label: const Text("Create First Survey"),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 12,
                        ),
                        textStyle: const TextStyle(fontSize: 16),
                      ),
                    )
                  else
                    ElevatedButton(
                      onPressed: _loadDashboardData,
                      child: const Text("Retry"),
                    ),
                ],
              ),
            )
          : TabBarView(
              controller: _tabController,
              children: [_buildAnalyticsTab(), _buildTeamTab()],
            ),
    );
  }

  Widget _buildAnalyticsTab() {
    if (_analyticsData == null || _totalPolled == 0) {
      return const Center(child: Text("No Data Yet"));
    }

    final List<dynamic> parties = _analyticsData!['data'] ?? [];

    // Convert to PieChart Sections
    List<PieChartSectionData> sections = [];
    final List<Color> colors = [
      Colors.blue,
      Colors.orange,
      Colors.green,
      Colors.red,
      Colors.purple,
    ];

    for (int i = 0; i < parties.length; i++) {
      final p = parties[i];
      final double val = (p['count'] as int).toDouble();
      final double percent = (p['percentage'] as num).toDouble();

      sections.add(
        PieChartSectionData(
          color: colors[i % colors.length],
          value: val,
          title: '${percent}%',
          radius: 100,
          titleStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  const Text(
                    "Expected Party Vote Share",
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    height: 300,
                    child: PieChart(
                      PieChartData(
                        sections: sections,
                        centerSpaceRadius: 40,
                        sectionsSpace: 2,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text("Total Polled: $_totalPolled voters"),
                ],
              ),
            ),
          ),
          // Legend
          ...parties.asMap().entries.map((entry) {
            final i = entry.key;
            final p = entry.value;
            return ListTile(
              leading: CircleAvatar(
                backgroundColor: colors[i % colors.length],
                radius: 10,
              ),
              title: Text(p['party'] ?? "Unknown"),
              trailing: Text("${p['count']} votes"),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildTeamTab() {
    if (_teamRequests.isEmpty) {
      return const Center(child: Text("No Team Members or Requests"));
    }

    return ListView.builder(
      itemCount: _teamRequests.length,
      itemBuilder: (context, index) {
        final req = _teamRequests[index];
        final id = req['id'];
        final status = req['status'];
        final isPending = status == 'PENDING';

        return Card(
          margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: isPending
                  ? Colors.orange
                  : (status == "APPROVED" ? Colors.green : Colors.red),
              child: Icon(
                isPending
                    ? Icons.question_mark
                    : (status == "APPROVED" ? Icons.check : Icons.close),
                color: Colors.white,
              ),
            ),
            title: Text("${req['name']} (${req['role']})"),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Mobile: ${req['mobile']}"),
                Text("Loc: ${req['village']} / Ward ${req['ward']}"),
                Text(
                  "Status: $status",
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ],
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (isPending) ...[
                  IconButton(
                    icon: const Icon(Icons.check, color: Colors.green),
                    onPressed: () => _handleApproval(id, "APPROVED"),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.red),
                    onPressed: () => _handleApproval(id, "REJECTED"),
                  ),
                ],
                IconButton(
                  icon: const Icon(Icons.delete, color: Colors.grey),
                  onPressed: () => _deleteSurveyor(id),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
