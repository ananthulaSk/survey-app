import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class VoterOpinionScreen extends StatefulWidget {
  const VoterOpinionScreen({super.key});

  @override
  State<VoterOpinionScreen> createState() => _VoterOpinionScreenState();
}

class _VoterOpinionScreenState extends State<VoterOpinionScreen> {
  String? _selectedParty;

  bool _isLoading = true;
  Map<String, dynamic>? _voterData;

  @override
  void initState() {
    super.initState();
    _fetchNextVoter();
  }

  Future<void> _fetchNextVoter() async {
    setState(() => _isLoading = true);
    try {
      int currentId = 0;
      if (_voterData != null) {
        currentId = _voterData!['voter_id'] ?? 0;
      }

      final response = await http.get(
        Uri.parse('http://127.0.0.1:8000/voters/next?current_id=$currentId'),
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json['status'] == 'success') {
          setState(() {
            _voterData = json['data'];
            _isLoading = false;
            _selectedParty = _voterData?['expected_party'];
          });
        } else {
          // Handle finished or error
          setState(() => _isLoading = false);
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(const SnackBar(content: Text("No more voters!")));
        }
      } else {
        throw Exception("Failed to load");
      }
    } catch (e) {
      setState(() => _isLoading = false);
      print("Error fetching voter: $e");
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text("Error: $e")));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    if (_voterData == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Survey Entry")),
        body: const Center(child: Text("No Voter Data Available")),
      );
    }

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          "Survey Entry",
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // --- Section 1: Voter Information Card ---
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      "Voter Details (DB ID: ${_voterData!['voter_id']})",
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Divider(),
                    const SizedBox(height: 8),
                    _buildInfoRow("Name", _voterData!['name'] ?? "N/A"),
                    _buildInfoRow("Surname", _voterData!['surname'] ?? "N/A"),
                    _buildInfoRow("Relation", _voterData!['relation'] ?? "N/A"),
                    _buildInfoRow("Age", "${_voterData!['age'] ?? 'N/A'}"),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(
                          Icons.location_on,
                          color: Colors.indigo,
                          size: 20,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          "Ward ${_voterData!['ward']}, House ${_voterData!['house_no']}",
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // --- Section 2: Expected Vote Selection ---
            const Text(
              "Expecting to Vote For",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              alignment: WrapAlignment.center,
              children: [
                _buildPartyButton("TRS", Colors.pink),
                _buildPartyButton("INC", Colors.blue),
                _buildPartyButton("BJP", Colors.orange),
                _buildPartyButton("CPM", Colors.red),
                _buildPartyButton("CPI", Colors.redAccent),
                _buildPartyButton("OTHER", Colors.grey),
              ],
            ),
            const SizedBox(height: 24),

            // --- Section 3: Demographic Information ---
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  children: [
                    _buildDropdown("Occupation", [
                      "Farmer",
                      "Employee",
                      "Business",
                    ], _voterData!['occupation']),
                    const SizedBox(height: 16),
                    _buildDropdown("Religion", [
                      "Hindu",
                      "Muslim",
                      "Christian",
                    ], _voterData!['religion']),
                    const SizedBox(height: 16),
                    _buildDropdown("Caste", [
                      "OC",
                      "BC",
                      "SC",
                      "ST",
                    ], _voterData!['caste']),
                    const SizedBox(height: 16),
                    _buildDropdown("Sub-Caste", [
                      "Yadav",
                      "Mala",
                      "Madiga",
                      "Reddy",
                    ], _voterData!['sub_caste']),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // --- Section 4: Optional Mobile Number ---
            TextFormField(
              initialValue: _voterData!['mobile_no'],
              keyboardType: TextInputType.phone,
              decoration: InputDecoration(
                labelText: "Mobile Number (Optional)",
                helperText: "Used only for follow-up communication",
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                filled: true,
                fillColor: Colors.white,
              ),
              onChanged: (v) => _voterData!['mobile_no'] = v,
            ),
            const SizedBox(height: 100), // Space for bottom buttons
          ],
        ),
      ),
      // --- Action Buttons (Bottom Fixed) ---
      bottomNavigationBar: Container(
        padding: const EdgeInsets.all(16),
        color: Colors.white,
        child: Row(
          children: [
            Expanded(
              child: ElevatedButton(
                onPressed: () async {
                  // Update Logic
                  try {
                    final updateData = {
                      "voter_id": _voterData!['voter_id'],
                      "party": _selectedParty,
                      "occupation":
                          _voterData!['occupation'], // In real app, bind these to state
                      "mobile_no": _voterData!['mobile_no'],
                    };

                    await http.put(
                      Uri.parse('http://127.0.0.1:8000/voters/update'),
                      headers: {"Content-Type": "application/json"},
                      body: jsonEncode(updateData),
                    );

                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Voter Data Saved Successfully!"),
                      ),
                    );
                    // Fetch next
                    _fetchNextVoter();
                  } catch (e) {
                    ScaffoldMessenger.of(
                      context,
                    ).showSnackBar(SnackBar(content: Text("Save Error: $e")));
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: const Text(
                  "Save / Update Voter",
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            OutlinedButton(
              onPressed: () {
                // Skip / Next
                _fetchNextVoter();
              },
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(
                  vertical: 16,
                  horizontal: 20,
                ),
                side: const BorderSide(color: Colors.indigo, width: 2),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              child: const Text(
                "Next Voter →",
                style: TextStyle(
                  color: Colors.indigo,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
          ),
        ],
      ),
    );
  }

  Widget _buildPartyButton(String party, Color color) {
    final isSelected = _selectedParty == party;
    return GestureDetector(
      onTap: () => setState(() => _selectedParty = party),
      child: Container(
        width: 100,
        height: 60,
        decoration: BoxDecoration(
          color: isSelected ? color : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color, width: 2),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: color.withOpacity(0.4),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ]
              : [],
        ),
        alignment: Alignment.center,
        child: Text(
          party,
          style: TextStyle(
            color: isSelected ? Colors.white : color,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
      ),
    );
  }

  Widget _buildDropdown(
    String label,
    List<String> items,
    String? currentValue,
  ) {
    return DropdownButtonFormField<String>(
      value: (items.contains(currentValue)) ? currentValue : null,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 0),
      ),
      items: items
          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
          .toList(),
      onChanged: (v) {
        setState(() {
          // Simplistic binding for demo
          if (label == 'Occupation') _voterData!['occupation'] = v;
          if (label == 'Religion') _voterData!['religion'] = v;
          if (label == 'Caste') _voterData!['caste'] = v;
          if (label == 'Sub-Caste') _voterData!['sub_caste'] = v;
        });
      },
    );
  }
}
