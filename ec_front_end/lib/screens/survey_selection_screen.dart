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
      appBar: AppBar(
        title: const Text("Select Survey"),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadSurveys),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _surveys.isEmpty
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.pending_actions, size: 64, color: Colors.grey),
                    const SizedBox(height: 16),
                    const Text(
                      "No active surveys available",
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      "Surveys will appear here once created and approved by the central dashboard.",
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 16, color: Colors.grey[600]),
                    ),
                  ],
                ),
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
                      backgroundColor: survey['survey_type'] == 'FINAL'
                          ? Colors.red[100]
                          : Colors.blue[100],
                      child: Text(survey['scope_value'] ?? "?"),
                    ),
                    title: Text(survey['name'] ?? "Unnamed Survey"),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text("Code: ${survey['survey_code'] ?? 'N/A'}"),
                        Text("Type: ${survey['survey_type'] ?? 'TEST'}"),
                        Text(
                          "Created: ${survey['created_at']?.split('T')[0] ?? 'Unknown'}",
                        ),
                      ],
                    ),
                    trailing: Icon(Icons.arrow_forward_ios),
                    onTap: () => _selectSurvey(survey),
                  ),
                );
              },
            ),
    );
  }
}
