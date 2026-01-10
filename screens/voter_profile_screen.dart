import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class VoterProfileScreen extends StatefulWidget {
  final Map<String, dynamic> voter;
  const VoterProfileScreen({super.key, required this.voter});
  @override
  State<VoterProfileScreen> createState() => _VoterProfileScreenState();
}

class _VoterProfileScreenState extends State<VoterProfileScreen> {
  String? _selectedParty;

  Future<void> _save() async {
    final res = await http.put(Uri.parse(
      'http://10.0.2.2:8000/voters/update?voter_id=${widget.voter['voter_id']}&party=$_selectedParty'
    ));
    if (res.statusCode == 200) {
      Navigator.pop(context, "SAVED");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Voter Profile"), backgroundColor: Colors.blue[50]),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Voter info header
            Card(
              child: ListTile(
                leading: const CircleAvatar(child: Icon(Icons.person)),
                title: Text(widget.voter['name']),
                subtitle: Text("Age: ${widget.voter['age']} | Ward: ${widget.voter['ward']}"),
              ),
            ),
            const SizedBox(height: 20),
            const Text("Expecting to Vote For:", style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            // Party buttons matching your image
            Wrap(
              spacing: 10,
              children: ['TRS', 'INC', 'BJP', 'CPM', 'CPI', 'OTHER'].map((p) => ChoiceChip(
                label: Text(p),
                selected: _selectedParty == p,
                onSelected: (s) => setState(() => _selectedParty = s ? p : null),
                selectedColor: Colors.blue[100],
              )).toList(),
            ),
            const Spacer(),
            Row(
              children: [
                Expanded(child: OutlinedButton(onPressed: () => Navigator.pop(context), child: const Text("Next Voter"))),
                const SizedBox(width: 10),
                Expanded(child: ElevatedButton(onPressed: _save, style: ElevatedButton.styleFrom(backgroundColor: Colors.green), child: const Text("Save / Update"))),
              ],
            )
          ],
        ),
      ),
    );
  }
}