import 'package:flutter/material.dart';

import 'approval_screen.dart';

class RegistrationScreen extends StatelessWidget {
  const RegistrationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFE3F2FD), Colors.white], // Soft blue to white
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 20),
                // --- Header Section ---
                const Center(
                  child: Icon(
                    Icons.how_to_vote,
                    size: 48,
                    color: Color(0xFF1565C0),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  "Election Survey Program",
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1565C0),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  "Join the official village survey team",
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colors.grey[700]),
                ),
                const SizedBox(height: 40),

                // --- Form Card ---
                Card(
                  elevation: 8,
                  shadowColor: Colors.black26,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      children: [
                        _buildTextField(
                          label: "Mobile Number",
                          icon: Icons.phone,
                          isNumber: true,
                        ),
                        const SizedBox(height: 16),
                        _buildTextField(
                          label: "Surveyor Name",
                          icon: Icons.person,
                        ),
                        const SizedBox(height: 16),
                        _buildDropdown(
                          label: "District",
                          items: ["District A", "District B"],
                        ),
                        const SizedBox(height: 16),
                        _buildDropdown(
                          label: "Mandal",
                          items: ["Mandal X", "Mandal Y"],
                        ),
                        const SizedBox(height: 16),
                        _buildDropdown(
                          label: "Village",
                          items: ["Village 1", "Village 2"],
                        ),
                        const SizedBox(height: 16),
                        _buildDropdown(
                          label: "Ward",
                          items: ["Ward 1", "Ward 2"],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 40),

                // --- Action Area ---
                ElevatedButton(
                  onPressed: () {
                    // Simulate API request/Approval
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text("Request Sent! Redirecting..."),
                      ),
                    );
                    // Navigate to Survey Screen (Profile) after delay
                    Future.delayed(const Duration(seconds: 1), () {
                      if (context.mounted) {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (context) =>
                                const ApprovalScreen(), // Go to Approval Wait Screen
                          ),
                        );
                      }
                    });
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2E7D32), // Green
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    elevation: 4,
                  ),
                  child: const Text(
                    "Request Survey Access",
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  "Access will be approved by village coordinator",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),

                const SizedBox(height: 40),
                // --- Footer Trust Line ---
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.lock_outline, size: 16, color: Colors.grey[600]),
                    const SizedBox(width: 8),
                    Text(
                      "Secure • Local Approval • No OTP Required",
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required String label,
    required IconData icon,
    bool isNumber = false,
  }) {
    return TextField(
      keyboardType: isNumber ? TextInputType.phone : TextInputType.text,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Colors.blueGrey),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.grey[50],
      ),
    );
  }

  Widget _buildDropdown({required String label, required List<String> items}) {
    return DropdownButtonFormField<String>(
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.grey[50],
      ),
      items: items
          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
          .toList(),
      onChanged: (v) {},
    );
  }
}
