import 'package:flutter/material.dart';

import 'approval_screen.dart';

import '../services/api_service.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final TextEditingController _mobileController = TextEditingController();
  final TextEditingController _nameController = TextEditingController();
  bool _isSubmitting = false;

  // --- Location State ---
  List<Map<String, dynamic>> _districts = [];
  List<Map<String, dynamic>> _mandals = [];
  List<Map<String, dynamic>> _villages = [];
  List<Map<String, dynamic>> _wards = [];

  String? _selectedDistrict;
  String? _selectedMandal;
  String? _selectedVillage;
  String? _selectedWard;

  final _api = ApiService();

  @override
  void initState() {
    super.initState();
    _loadDistricts();
  }

  Future<void> _loadDistricts() async {
    try {
      final list = await _api.getDistricts();
      setState(() => _districts = list);
    } catch (e) {
      print("Error loading districts: $e");
    }
  }

  Future<void> _onDistrictChanged(String? name) async {
    if (name == null) return;
    final id = _districts.firstWhere((e) => e['name'] == name)['id'];

    setState(() {
      _selectedDistrict = name;
      _selectedDistrict = name;
      _mandals = [];
      _selectedMandal = null;
      _villages = [];
      _selectedVillage = null;
      _wards = [];
      _selectedWard = null;
    });

    try {
      final list = await _api.getMandals(id);
      setState(() => _mandals = list);
    } catch (e) {
      print("Error: $e");
    }
  }

  Future<void> _onMandalChanged(String? name) async {
    if (name == null) return;
    final id = _mandals.firstWhere((e) => e['name'] == name)['id'];

    setState(() {
      _selectedMandal = name;
      _selectedMandal = name;
      _villages = [];
      _selectedVillage = null;
      _wards = [];
      _selectedWard = null;
    });

    try {
      final list = await _api.getVillages(id);
      setState(() => _villages = list);
    } catch (e) {
      print("Error: $e");
    }
  }

  Future<void> _onVillageChanged(String? name) async {
    if (name == null) return;
    final id = _villages.firstWhere((e) => e['name'] == name)['id'];

    setState(() {
      _selectedVillage = name;
      _selectedVillage = name;
      _wards = [];
      _selectedWard = null;
    });

    try {
      final list = await _api.getWards(id);
      setState(() => _wards = list);
    } catch (e) {
      print("Error: $e");
    }
  }

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
                          controller: _mobileController,
                          label: "Mobile Number",
                          icon: Icons.phone,
                          isNumber: true,
                        ),
                        const SizedBox(height: 16),
                        _buildTextField(
                          controller: _nameController,
                          label: "Surveyor Name",
                          icon: Icons.person,
                        ),
                        const SizedBox(height: 16),

                        // --- DYNAMIC LOCATION DROPDOWNS ---
                        _buildDynamicDropdown(
                          label: "District",
                          value: _selectedDistrict,
                          items: _districts
                              .map((e) => e['name'] as String)
                              .toList(),
                          onChanged: _onDistrictChanged,
                        ),
                        const SizedBox(height: 16),
                        _buildDynamicDropdown(
                          label: "Mandal",
                          value: _selectedMandal,
                          items: _mandals
                              .map((e) => e['name'] as String)
                              .toList(),
                          onChanged: _onMandalChanged,
                        ),
                        const SizedBox(height: 16),
                        _buildDynamicDropdown(
                          label: "Village",
                          value: _selectedVillage,
                          items: _villages
                              .map((e) => e['name'] as String)
                              .toList(),
                          onChanged: _onVillageChanged,
                        ),
                        const SizedBox(height: 16),
                        _buildDynamicDropdown(
                          label: "Ward",
                          value: _selectedWard,
                          items: _wards
                              .map((e) => e['name'] as String)
                              .toList(),
                          onChanged: (v) => setState(() => _selectedWard = v),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 40),

                // --- Action Area ---
                _isSubmitting
                    ? const Center(child: CircularProgressIndicator())
                    : ElevatedButton(
                        onPressed: () async {
                          if (_mobileController.text.trim().isEmpty ||
                              _nameController.text.trim().isEmpty) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  "Please enter Name and Mobile Number",
                                ),
                              ),
                            );
                            return;
                          }

                          if (_selectedWard == null) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                  "Please select complete location details",
                                ),
                              ),
                            );
                            return;
                          }

                          setState(() => _isSubmitting = true);

                          try {
                            // 1. Send Request to Backend (With Locations)
                            await ApiService().registerSurveyor(
                              _nameController.text.trim(),
                              _mobileController.text.trim(),
                              district: _selectedDistrict!,
                              mandal: _selectedMandal!,
                              village: _selectedVillage!,
                              ward: _selectedWard!,
                            );

                            // 2. Save Session locally
                            await ApiService.saveSession(
                              _mobileController.text.trim(),
                              null,
                            );

                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text("Request Sent! Redirecting..."),
                              ),
                            );

                            if (context.mounted) {
                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => const ApprovalScreen(),
                                ),
                              );
                            }
                          } catch (e) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text("Error: $e")),
                            );
                          } finally {
                            if (mounted) setState(() => _isSubmitting = false);
                          }
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
                // Legacy Footer
                const SizedBox(height: 40),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.lock_outline, size: 16, color: Colors.grey[600]),
                    const SizedBox(width: 8),
                    const Text(
                      "v16.2 (DATA RESET)",
                      style: TextStyle(
                        color: Colors.red,
                        fontWeight: FontWeight.bold,
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
    TextEditingController? controller,
  }) {
    return TextField(
      controller: controller,
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

  Widget _buildDynamicDropdown({
    required String label,
    required String? value,
    required List<String> items,
    required Function(String?) onChanged,
  }) {
    return DropdownButtonFormField<String>(
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.grey[50],
      ),
      value: value,
      items: items
          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
          .toList(),
      onChanged: onChanged,
    );
  }
}
