import 'package:flutter/material.dart';

class VoterDetailsScreen extends StatelessWidget {
  final Map<String, dynamic> voter;

  const VoterDetailsScreen({super.key, required this.voter});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(voter['name']),
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
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    _buildInfoRow(Icons.home, "House No", voter['house_no'] ?? 'N/A'),
                    const Divider(),
                    _buildInfoRow(Icons.calendar_today, "Age", voter['age']?.toString() ?? 'N/A'),
                    const Divider(),
                    _buildInfoRow(Icons.location_on, "Ward Number", voter['ward']?.toString() ?? 'N/A'),
                    const Divider(),
                    _buildInfoRow(Icons.wc, "Gender", voter['gender'] ?? 'Not Specified'),
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
          Text("$label: ", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          Text(value, style: const TextStyle(fontSize: 16)),
        ],
      ),
    );
  }
}