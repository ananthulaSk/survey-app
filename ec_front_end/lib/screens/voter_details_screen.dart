import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'package:http/http.dart' as http;

class VoterDetailsScreen extends StatefulWidget {
  final Map<String, dynamic> voter;
  const VoterDetailsScreen({super.key, required this.voter});
  @override
  State<VoterDetailsScreen> createState() => _VoterDetailsScreenState();
}

class _VoterDetailsScreenState extends State<VoterDetailsScreen> {
  String? _party;
  // FIX: Use ApiService for dynamic URL
  // final String updateUrl = "http://127.0.0.1:8000/voters/update";
  String get updateUrl => "${ApiService.baseUrl}/voters/update";

  Future<void> _save() async {
    if (_party == null) return;
    final res = await http.put(
      Uri.parse(
        '$updateUrl?voter_id=${widget.voter['voter_id']}&party=$_party',
      ),
    );
    if (res.statusCode == 200) Navigator.pop(context, "REFRESH");
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.voter['name']),
        backgroundColor: Colors.blueAccent,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Voter Profile Header with Photo Placeholder
            Center(
              child: CircleAvatar(
                radius: 60,
                backgroundColor: Colors.grey[300],
                child: const Icon(Icons.person, size: 80, color: Colors.white),
              ),
            ),
            const SizedBox(height: 24),

            // Voter Details Card
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    _buildInfoRow(
                      Icons.account_circle,
                      "Full Name",
                      "${widget.voter['name']} ${widget.voter['surname']}",
                    ),
                    const Divider(),
                    _buildInfoRow(
                      Icons.home,
                      "House No",
                      widget.voter['house_no'] ?? 'N/A',
                    ),
                    const Divider(),
                    _buildInfoRow(
                      Icons.calendar_today,
                      "Age",
                      widget.voter['age']?.toString() ?? 'N/A',
                    ),
                    const Divider(),
                    _buildInfoRow(
                      Icons.location_on,
                      "Ward Number",
                      widget.voter['ward']?.toString() ?? 'N/A',
                    ),
                    const Divider(),
                    _buildInfoRow(
                      Icons.wc,
                      "Gender",
                      widget.voter['gender'] ?? 'Not Specified',
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Survey Section (Kept from original project file)
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Survey: Expected Vote",
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 10,
                      children: ['TRS', 'INC', 'BJP', 'OTHERS']
                          .map(
                            (p) => ChoiceChip(
                              label: Text(p),
                              selected: _party == p,
                              onSelected: (val) =>
                                  setState(() => _party = val ? p : null),
                            ),
                          )
                          .toList(),
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _save,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.green,
                          foregroundColor: Colors.white,
                        ),
                        child: const Text("Save Survey Details"),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        children: [
          Icon(icon, color: Colors.blueAccent),
          const SizedBox(width: 16),
          Text(
            "$label: ",
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
          Flexible(child: Text(value, style: const TextStyle(fontSize: 16))),
        ],
      ),
    );
  }
}
