import 'package:flutter/material.dart';
import 'voter_profile_screen.dart';
import '../services/api_service.dart';
import '../models/voter.dart';

class VoterSearchScreen extends StatefulWidget {
  const VoterSearchScreen({super.key});
  @override
  State<VoterSearchScreen> createState() => _VoterSearchScreenState();
}

class _VoterSearchScreenState extends State<VoterSearchScreen> {
  final TextEditingController _controller = TextEditingController();
  List<Voter> _voters = [];
  bool _isLoading = false;
  final ApiService _apiService = ApiService();

  Future<void> _search(String val) async {
    setState(() => _isLoading = true);
    try {
      final voters = await _apiService.searchVoters(val);
      setState(() => _voters = voters);
    } catch (e) {
      debugPrint("Connection Error: $e");
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Aregudem Voter Search")),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(10),
            child: TextField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: "Enter Name (e.g. Reddy)",
                border: OutlineInputBorder(),
              ),
              onSubmitted: _search,
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: _voters.length,
                    itemBuilder: (ctx, i) => ListTile(
                      title: Text(_voters[i].name),
                      subtitle: Text(
                        "Ward: ${_voters[i].ward} | House: ${_voters[i].houseNo}",
                      ),
                      trailing: _voters[i].expectedParty != null
                          ? const Icon(Icons.check_circle, color: Colors.green)
                          : const Icon(Icons.chevron_right),
                      onTap: () async {
                        final result = await Navigator.push(
                          ctx,
                          MaterialPageRoute(
                            builder: (_) =>
                                VoterProfileScreen(voter: _voters[i]),
                          ),
                        );
                        if (result == "RELOAD") _search(_controller.text);
                      },
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
