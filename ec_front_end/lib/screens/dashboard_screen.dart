import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';
import 'bulk_upload_screen.dart';
import 'package:http/http.dart' as http;

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

  // Assignment Data
  List<dynamic> _activeSurveys = [];
  int? _selectedAssignmentSurveyId;
  List<dynamic> _unassignedSurveyors = [];
  List<dynamic> _currentAssignments = [];
  bool _isAssignmentLoading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: 4,
      vsync: this,
    ); // Updated for 4 tabs
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      // 1. Fetch Surveys
      final activeSurveys = await _api.getActiveSurveys();
      _activeSurveys = activeSurveys;

      // 2. Ensure we have a Survey ID (Context)
      if (_api.currentSurveyId == null && activeSurveys.isNotEmpty) {
        _api.currentSurveyId = activeSurveys.first['id'];
        _selectedAssignmentSurveyId = _api.currentSurveyId;
      }

      // 3. Fetch Data in Parallel
      final analytics = await _api.getDashboardAnalytics();
      final approvals = await _api.getPendingApprovals();

      if (mounted) {
        setState(() {
          _analyticsData = analytics;
          _totalPolled = analytics['total_polled'] ?? 0;
          _teamRequests = approvals;
          _isLoading = false;
        });

        // Post-load: if we have a survey, fetch its assignments
        if (_api.currentSurveyId != null) {
          _loadAssignmentDetails(_api.currentSurveyId!);
        }
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

  Future<void> _deleteSurvey(int id) async {
    final bool confirm =
        await showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: const Text("Confirm Delete"),
            content: const Text(
              "Are you sure you want to delete this survey? This will erase all captured voter opinions for this survey.",
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text("Cancel"),
              ),
              TextButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text(
                  "Delete",
                  style: TextStyle(color: Colors.red),
                ),
              ),
            ],
          ),
        ) ??
        false;

    if (confirm) {
      setState(() => _isLoading = true);
      try {
        // We'll need to implement the actual delete API call if not exists
        // ApiService already has the base url for it.
        final response = await http.delete(
          Uri.parse('${ApiService.baseUrl}/surveys/$id'),
          headers: {'x-admin-token': 'admin-secret-123'},
        );
        if (response.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text("Survey deleted successfully")),
          );
          _loadDashboardData();
        } else {
          throw Exception("Failed to delete: ${response.body}");
        }
      } catch (e) {
        setState(() {
          _isLoading = false;
          _errorMessage = e.toString();
        });
      }
    }
  }

  Future<void> _loadAssignmentDetails(int surveyId) async {
    setState(() => _isAssignmentLoading = true);
    try {
      final approved = await _api.getApprovedSurveyors();
      final assigned = await _api.getAssignmentsForSurvey(surveyId);

      // Filter unassigned: Approved surveyors not in the assigned list
      final assignedMobiles = assigned.map((a) => a['surveyor_mobile']).toSet();
      final unassigned = approved
          .where((s) => !assignedMobiles.contains(s['mobile']))
          .toList();

      if (mounted) {
        setState(() {
          _currentAssignments = assigned;
          _unassignedSurveyors = unassigned;
          _isAssignmentLoading = false;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _isAssignmentLoading = false);
    }
  }

  Future<void> _handleAssign(int surveyorId) async {
    if (_selectedAssignmentSurveyId == null) return;
    final success = await _api.assignSurveyor(
      _selectedAssignmentSurveyId!,
      surveyorId,
    );
    if (success) {
      _loadAssignmentDetails(_selectedAssignmentSurveyId!);
    }
  }

  Future<void> _handleUnassign(int surveyorId) async {
    if (_selectedAssignmentSurveyId == null) return;
    final success = await _api.unassignSurveyor(
      _selectedAssignmentSurveyId!,
      surveyorId,
    );
    if (success) {
      _loadAssignmentDetails(_selectedAssignmentSurveyId!);
    }
  }

  // --- CREATE SURVEY FLOW ---

  Future<void> _showCreateSurveyDialog() async {
    final nameController = TextEditingController();

    // State for Dialog
    int? selectedDistrictId;
    int? selectedMandalId;
    int? selectedVillageId;

    List<dynamic> districts = [];
    List<dynamic> mandals = [];
    List<dynamic> villages = [];

    // Initial Load
    try {
      districts = await _api.getDistricts();
    } catch (e) {
      // debugPrint("Error loading districts: $e");
    }

    if (!mounted) return;

    await showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) {
          return AlertDialog(
            title: const Text("Create New Survey"),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: nameController,
                    decoration: const InputDecoration(
                      labelText: "Survey Name",
                      hintText: "Enter unique name",
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    "Select Scope",
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),

                  // District Dropdown
                  DropdownButtonFormField<int>(
                    value: selectedDistrictId,
                    decoration: const InputDecoration(
                      labelText: "District",
                      border: OutlineInputBorder(),
                    ),
                    hint: const Text("Select District"),
                    items: districts
                        .map(
                          (d) => DropdownMenuItem<int>(
                            value: d['id'],
                            child: Text(d['name']),
                          ),
                        )
                        .toList(),
                    onChanged: (val) async {
                      if (val != null) {
                        setDialogState(() {
                          selectedDistrictId = val;
                          selectedMandalId = null;
                          selectedVillageId = null;
                          mandals = [];
                          villages = [];
                        });
                        try {
                          final newMandals = await _api.getMandals(val);
                          setDialogState(() => mandals = newMandals);
                        } catch (e) {
                          print(e);
                        }
                      }
                    },
                  ),
                  const SizedBox(height: 12),

                  // Mandal Dropdown
                  DropdownButtonFormField<int>(
                    value: selectedMandalId,
                    decoration: const InputDecoration(
                      labelText: "Mandal",
                      border: OutlineInputBorder(),
                    ),
                    hint: const Text("Select Mandal (Optional)"),
                    items: mandals
                        .map(
                          (m) => DropdownMenuItem<int>(
                            value: m['id'],
                            child: Text(m['name']),
                          ),
                        )
                        .toList(),
                    onChanged: (val) async {
                      if (val != null) {
                        setDialogState(() {
                          selectedMandalId = val;
                          selectedVillageId = null;
                          villages = [];
                        });
                        try {
                          final newVillages = await _api.getVillages(val);
                          setDialogState(() => villages = newVillages);
                        } catch (e) {
                          print(e);
                        }
                      } else {
                        setDialogState(() => selectedMandalId = null);
                      }
                    },
                  ),
                  const SizedBox(height: 12),

                  // Village Dropdown
                  DropdownButtonFormField<int>(
                    value: selectedVillageId,
                    decoration: const InputDecoration(
                      labelText: "Village",
                      border: OutlineInputBorder(),
                    ),
                    hint: const Text("Select Village (Optional)"),
                    items: villages
                        .map(
                          (v) => DropdownMenuItem<int>(
                            value: v['id'],
                            child: Text(v['name']),
                          ),
                        )
                        .toList(),
                    onChanged: (val) {
                      setDialogState(() => selectedVillageId = val);
                    },
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text("Cancel"),
              ),
              ElevatedButton(
                onPressed: () async {
                  if (nameController.text.isNotEmpty &&
                      selectedDistrictId != null) {
                    Navigator.pop(context);
                    await _performCreateSurvey(
                      nameController.text,
                      selectedDistrictId!,
                      selectedMandalId,
                      selectedVillageId,
                    );
                  } else {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Please enter Name and select District"),
                      ),
                    );
                  }
                },
                child: const Text("Create"),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _performCreateSurvey(
    String name,
    int districtId,
    int? mandalId,
    int? villageId,
  ) async {
    setState(() => _isLoading = true);
    try {
      // Determine Scope
      String scopeType = "DISTRICT";
      String scopeIds = "ALL";

      // If Village Selected -> Scope is VILLAGE
      // If Mandal Selected -> Scope is MANDAL
      // Else -> DISTRICT

      // Backend expects specific format.
      // For now, we pass the IDs explicitly.
      List<int> mIds = mandalId != null ? [mandalId] : [];
      List<int> vIds = villageId != null ? [villageId] : [];

      final res = await _api.createSurvey(
        name,
        scopeType,
        scopeIds,
        districtId: districtId,
        mandalIds: mIds.isNotEmpty ? mIds : "ALL",
        villageIds: vIds.isNotEmpty ? vIds : "ALL",
      );

      // CRITICAL FIX: Force set the current survey ID so the dashboard picks it up immediately
      if (res['survey_id'] != null) {
        _api.currentSurveyId = res['survey_id'];
        print("Explicitly set Current Survey ID: ${_api.currentSurveyId}");
      }

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
        title: const Text("Admin Dashboard (v20.02 - FORCE UPDATE)"),
        backgroundColor:
            Colors.teal[800], // Changed to Teal to signify feature addition
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.pie_chart), text: "Analytics"),
            Tab(icon: Icon(Icons.people), text: "Team"),
            Tab(icon: Icon(Icons.assignment), text: "Surveys"),
            Tab(icon: Icon(Icons.task), text: "Assignments"),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadDashboardData,
          ),
          IconButton(
            icon: const Icon(Icons.upload_file),
            tooltip: "Bulk Upload Voters",
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const BulkUploadScreen()),
              );
            },
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
              children: [
                _buildAnalyticsTab(),
                _buildTeamTab(),
                _buildSurveysTab(),
                _buildAssignmentsTab(),
              ],
            ),
    );
  }

  Widget _buildAnalyticsTab() {
    if (_analyticsData == null || _totalPolled == 0) {
      return const Center(child: Text("No Data Yet"));
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "Vote Share Analytics",
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              ElevatedButton.icon(
                onPressed: () => _api.exportSurveyData(_api.currentSurveyId!),
                icon: Icon(Icons.download),
                label: Text("Export CSV"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue[700],
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ),
        ),
        Expanded(child: _buildChartContainer()),
      ],
    );
  }

  Widget _buildChartContainer() {
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

  Widget _buildSurveysTab() {
    if (_activeSurveys.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assignment_late, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            const Text(
              "No Surveys Created Yet",
              style: TextStyle(fontSize: 18, color: Colors.grey),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _showCreateSurveyDialog,
              icon: const Icon(Icons.add),
              label: const Text("Create First Survey"),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "Active Surveys (${_activeSurveys.length})",
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              ElevatedButton.icon(
                onPressed: _showCreateSurveyDialog,
                icon: const Icon(Icons.add),
                label: const Text("New Survey"),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _activeSurveys.length,
            itemBuilder: (context, index) {
              final s = _activeSurveys[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: ListTile(
                  leading: const CircleAvatar(child: Icon(Icons.poll)),
                  title: Text(s['name'] ?? "Unnamed Survey"),
                  subtitle: Text(
                    "Code: ${s['survey_code'] ?? 'N/A'} | Scope: ${s['scope_type']}",
                  ),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete, color: Colors.red),
                    onPressed: () => _deleteSurvey(s['id']),
                  ),
                  onTap: () {
                    setState(() {
                      _api.currentSurveyId = s['id'];
                      _selectedAssignmentSurveyId = s['id'];
                    });
                    _loadDashboardData();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text("Switched context to: ${s['name']}"),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildAssignmentsTab() {
    return Column(
      children: [
        // 1. Survey Selection
        Container(
          padding: const EdgeInsets.all(16),
          color: Colors.white,
          child: Row(
            children: [
              const Icon(Icons.poll, color: Colors.blue),
              const SizedBox(width: 12),
              Expanded(
                child: DropdownButtonFormField<int>(
                  value: _selectedAssignmentSurveyId,
                  decoration: const InputDecoration(
                    labelText: "Select Survey to Manage Assignments",
                    border: OutlineInputBorder(),
                  ),
                  items: _activeSurveys.map((s) {
                    return DropdownMenuItem<int>(
                      value: s['id'],
                      child: Text(s['name']),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      setState(() => _selectedAssignmentSurveyId = val);
                      _loadAssignmentDetails(val);
                    }
                  },
                ),
              ),
            ],
          ),
        ),

        const Divider(height: 1),

        // 2. Content
        Expanded(
          child: _isAssignmentLoading
              ? const Center(child: CircularProgressIndicator())
              : Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // LEFT: Available Surveyors
                    Expanded(
                      flex: 1,
                      child: Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            color: Colors.grey[100],
                            width: double.infinity,
                            child: const Text(
                              "UNASSIGNED SURVEYORS",
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                          Expanded(
                            child: ListView.builder(
                              itemCount: _unassignedSurveyors.length,
                              itemBuilder: (ctx, i) {
                                final s = _unassignedSurveyors[i];
                                return ListTile(
                                  title: Text(s['name']),
                                  subtitle: Text(s['mobile']),
                                  trailing: IconButton(
                                    icon: const Icon(
                                      Icons.add_circle,
                                      color: Colors.green,
                                    ),
                                    onPressed: () => _handleAssign(s['id']),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                    const VerticalDivider(width: 1),
                    // RIGHT: Current Assignments
                    Expanded(
                      flex: 1,
                      child: Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            color: Colors.blue[50],
                            width: double.infinity,
                            child: const Text(
                              "CURRENTLY ASSIGNED",
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.blue,
                              ),
                            ),
                          ),
                          Expanded(
                            child: ListView.builder(
                              itemCount: _currentAssignments.length,
                              itemBuilder: (ctx, i) {
                                final a = _currentAssignments[i];
                                return ListTile(
                                  title: Text(a['surveyor_name'] ?? "Unknown"),
                                  subtitle: Text(a['surveyor_mobile'] ?? ""),
                                  trailing: IconButton(
                                    icon: const Icon(
                                      Icons.remove_circle,
                                      color: Colors.red,
                                    ),
                                    onPressed: () =>
                                        _handleUnassign(a['surveyor_id']),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
        ),
      ],
    );
  }
}
