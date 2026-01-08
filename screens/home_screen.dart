import 'package:flutter/material.dart';
import '../models/voter.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  List<Voter> _voters = [];
  bool _isLoading = false;
  final TextEditingController _searchController = TextEditingController();

  void _performSearch(String query) async {
    if (query.isEmpty) return;
    setState(() => _isLoading = true);
    try {
      final results = await _apiService.searchVoters(query);
      setState(() => _voters = results);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error: $e")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Aregudem Voter Search"),
        backgroundColor: Colors.blueAccent,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: "Search by Voter Name...",
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: () => _performSearch(_searchController.text),
                ),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onSubmitted: _performSearch,
            ),
          ),
          _isLoading 
            ? const Center(child: CircularProgressIndicator()) 
            : Expanded(
                child: ListView.builder(
                  itemCount: _voters.length,
                  itemBuilder: (context, index) {
                    final voter = _voters[index];
                    return Card(
                      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                      child: ListTile(
                        leading: const Icon(Icons.person, color: Colors.blue),
                        title: Text("${voter.voterName} ${voter.surname ?? ''}"),
                        subtitle: Text("House: ${voter.houseNo} | Age: ${voter.age}"),
                        trailing: Text("Ward: ${voter.wardNo}"),
                      ),
                    );
                  },
                ),
              ),
        ],
      ),
    );
  }
}