import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'voter_profile_screen.dart';

class SurveySelectionScreen extends StatefulWidget {
  final ApiService apiService;

  const SurveySelectionScreen({required this.apiService, Key? key})
    : super(key: key);

  @override
  _SurveySelectionScreenState createState() => _SurveySelectionScreenState();
}

class _SurveySelectionScreenState extends State<SurveySelectionScreen> {
  List<dynamic> _surveys = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSurveys();
  }

  Future<void> _loadSurveys() async {
    setState(() => _isLoading = true);
    try {
      final surveys = await widget.apiService.getActiveSurveys();
      setState(() {
        _surveys = surveys;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Error loading surveys: $e')));
    }
  }

  Future<void> _createNewSurvey() async {
    final nameController = TextEditingController();
    final wardController = TextEditingController();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Create New Survey"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: InputDecoration(labelText: "Survey Name"),
            ),
            TextField(
              controller: wardController,
              decoration: InputDecoration(labelText: "Ward No (Scope)"),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: () async {
              if (nameController.text.isNotEmpty &&
                  wardController.text.isNotEmpty) {
                Navigator.pop(context);
                _submitCreateSurvey(nameController.text, wardController.text);
              }
            },
            child: Text("Create"),
          ),
        ],
      ),
    );
  }

  Future<void> _submitCreateSurvey(String name, String ward) async {
    setState(() => _isLoading = true);
    try {
      // Assuming Scope Type is always WARD for now
      final result = await widget.apiService.createSurvey(name, "WARD", ward);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result['message'] ?? "Survey Created")),
      );
      _loadSurveys();
    } catch (e) {
      setState(() => _isLoading = false);
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text("Error"),
          content: Text(e.toString()),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text("OK"),
            ),
          ],
        ),
      );
    }
  }

  void _selectSurvey(dynamic survey) {
    widget.apiService.currentSurveyId = survey['id'];
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => VoterProfileScreen(apiService: widget.apiService),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Select Survey")),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _surveys.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text("No Active Surveys"),
                  SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: _createNewSurvey,
                    child: Text("Create Your First Survey"),
                  ),
                ],
              ),
            )
          : ListView.builder(
              itemCount: _surveys.length,
              itemBuilder: (context, index) {
                final survey = _surveys[index];
                return Card(
                  margin: EdgeInsets.all(8),
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text(survey['scope_value'] ?? "?"),
                    ),
                    title: Text(survey['name'] ?? "Unnamed Survey"),
                    subtitle: Text(
                      "Created: ${survey['created_at']?.split('T')[0] ?? 'Unknown'}",
                    ),
                    trailing: Icon(Icons.arrow_forward_ios),
                    onTap: () => _selectSurvey(survey),
                  ),
                );
              },
            ),
      floatingActionButton: _surveys.isNotEmpty
          ? FloatingActionButton(
              onPressed: _createNewSurvey,
              child: Icon(Icons.add),
              tooltip: "Create New Survey",
            )
          : null,
    );
  }
}
