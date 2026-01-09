import 'package:flutter/material.dart';
import '../models/voter.dart';
import '../services/api_service.dart';
import '../widgets/app_drawer.dart';

class VoterProfileScreen extends StatefulWidget {
  final Voter? voter;
  final ApiService? apiService; // Allow injection

  const VoterProfileScreen({super.key, this.voter, this.apiService});

  @override
  State<VoterProfileScreen> createState() => _VoterProfileScreenState();
}

class _VoterProfileScreenState extends State<VoterProfileScreen> {
  late final ApiService _apiService;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService ?? ApiService();
    _currentVoter = widget.voter;
    if (_currentVoter != null) {
      _populateFields(_currentVoter!);
    } else {
      _loadFirstVoter();
    }
  }

  Voter? _currentVoter;
  bool _isLoading = false;
  String _voterStatus = "AVAILABLE";

  // Controllers
  final _mobileController = TextEditingController();
  final _occupationController = TextEditingController();
  final _casteController = TextEditingController();
  final _subCasteController = TextEditingController();
  final _religionController = TextEditingController();
  String? _selectedParty;

  // Stats
  Map<String, int>? _stats;

  // Static options for dropdowns
  final List<String> _occupations = [
    "Farmer",
    "Employee",
    "Business",
    "Student",
    "Housewife",
    "Labor",
    "Other",
  ];
  final List<String> _religions = [
    "Hindu",
    "Muslim",
    "Christian",
    "Sikh",
    "Other",
  ];
  final List<String> _castes = [
    "OC",
    "BC-A",
    "BC-B",
    "BC-C",
    "BC-D",
    "SC",
    "ST",
    "Other",
  ];
  final List<String> _subCastes = [
    "Reddy",
    "Goud",
    "Munnuru Kapu",
    "Yadav",
    "Madiga",
    "Mala",
    "Other",
  ];

  Future<void> _refreshStats() async {
    if (_currentVoter == null) return;
    final s = await _apiService.getStats(
      ward: _currentVoter!.ward,
      currentVoterId: _currentVoter!.id,
    );
    if (mounted) setState(() => _stats = s);
  }

  void _populateFields(Voter v) {
    _selectedParty = v.expectedParty;
    _voterStatus = v.voterStatus ?? "AVAILABLE";
    _mobileController.text = v.mobileNo ?? '';
    _occupationController.text = v.occupation ?? '';
    _casteController.text = v.caste ?? '';
    _subCasteController.text = v.subCaste ?? '';
    _religionController.text = v.religion ?? '';

    // Auto-refresh stats for the current ward
    _refreshStats();
  }

  Future<void> _loadFirstVoter() async {
    setState(() => _isLoading = true);
    final v = await _apiService.getFirstVoter();
    if (mounted) {
      setState(() {
        _currentVoter = v;
        if (v != null) _populateFields(v);
        _isLoading = false;
      });
    }
  }

  Future<void> _navigate(bool isNext) async {
    if (_currentVoter == null) return;
    setState(() => _isLoading = true);

    Voter? newVoter;
    if (isNext) {
      newVoter = await _apiService.getNextVoter(_currentVoter!.id);
    } else {
      newVoter = await _apiService.getPreviousVoter(_currentVoter!.id);
    }

    if (newVoter != null && mounted) {
      setState(() {
        _currentVoter = newVoter;
        _populateFields(newVoter!);
        _isLoading = false;
      });
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              isNext ? "No more voters" : "This is the first voter",
            ),
          ),
        );
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _save() async {
    if (_currentVoter == null) return;

    final updates = {
      "party": _selectedParty,
      "mobile_no": _mobileController.text,
      "occupation": _occupationController.text,
      "religion": _religionController.text,
      "caste": _casteController.text,
      "sub_caste": _subCasteController.text,
      "voter_status": _voterStatus,
    };

    // If not available, clear survey data in the backend update (or handle in UI logic)
    // The requirement says: "If Deceased OR Out of Station / NRI is selected -> Completely hide ... Survey not required"
    // And "backend must block it" (simulated here by sending nulls or relying on backend to ignore if status != AVAILABLE)
    if (_voterStatus != "AVAILABLE") {
      updates["party"] = null;
      updates["occupation"] = null;
      updates["religion"] = null;
      updates["caste"] = null;
      updates["sub_caste"] = null;
      updates["mobile_no"] = null;
    }

    final success = await _apiService.updateVoter(_currentVoter!.id, updates);
    if (success && mounted) {
      await _refreshStats(); // Update counters immediately

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Survey Data Saved Successfully!"),
          backgroundColor: Colors.green,
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  @override
  void dispose() {
    _mobileController.dispose();
    _occupationController.dispose();
    _casteController.dispose();
    _subCasteController.dispose();
    _religionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text("Voter Profile")),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_currentVoter == null) {
      return Scaffold(
        appBar: AppBar(title: const Text("Voter Profile")),
        body: Center(
          child: ElevatedButton(
            onPressed: _loadFirstVoter,
            child: const Text("Retry"),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Voter Profile",
              style: TextStyle(color: Colors.black, fontSize: 18),
            ),
            if (_stats != null && _currentVoter != null)
              Text(
                "Ward ${_currentVoter!.ward} | Voter: ${_stats!['current_index']} / ${_stats!['total']}",
                style: const TextStyle(
                  color: Colors.green,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                ),
              ),
          ],
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        automaticallyImplyLeading: false, // Explicitly disable auto
        leading: Builder(
          builder: (context) => IconButton(
            icon: const Icon(
              Icons.menu,
              color: Colors.indigo,
            ), // Changed color to visible Indigo
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
        ),
      ),
      drawer: const AppDrawer(), // Add Left Side Menu using new widget
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 10),
              // 1. Purple Header Card
              Container(
                decoration: BoxDecoration(
                  color: const Color(0xFFF3E5F5), // Light purple
                  borderRadius: BorderRadius.circular(16),
                ),
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 30,
                      backgroundColor: Colors.purple[100],
                      child: const Icon(
                        Icons.person,
                        size: 35,
                        color: Colors.purple,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _currentVoter!.name,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 24, // Increased size further
                            ),
                          ),
                          const SizedBox(height: 8), // Increased spacing
                          Text(
                            "RELATION: ${_currentVoter!.relation ?? '-'}",
                            style: const TextStyle(
                              color: Colors.black87, // Darker for visibility
                              fontWeight: FontWeight.bold, // Bold
                              fontSize: 16, // Increased size
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            "Age: ${_currentVoter!.age} | Ward: ${_currentVoter!.ward}",
                            style: const TextStyle(
                              fontWeight: FontWeight.bold, // Bold
                              fontSize: 16, // Increased size
                              color: Colors.black87,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              const Icon(
                                Icons.location_on,
                                color: Colors.red,
                                size: 20,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                "House #${_currentVoter!.houseNo}",
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold, // Bold
                                  fontSize: 16, // Increased size
                                  color: Colors.black54,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 8),
              // Voter Status Buttons
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildStatusButton("AVAILABLE", "Available", Colors.green),
                    const SizedBox(width: 8),
                    _buildStatusButton("DEATH", "Death", Colors.red),
                    const SizedBox(width: 8),
                    _buildStatusButton(
                      "OUT_OF_STATION",
                      "Out of Station",
                      Colors.grey,
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 25),

              // CONDITIONAL RENDERING BASED ON STATUS
              if (_voterStatus == "AVAILABLE") ...[
                const Text(
                  "Expecting to Vote For",
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                const SizedBox(height: 15),

                // 2. Party Grid WITH DYNAMIC COLORS
                GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: 3,
                  childAspectRatio: 1.4,
                  mainAxisSpacing: 10,
                  crossAxisSpacing: 10,
                  children: [
                    _buildPartyButton(
                      "TRS",
                      Icons.directions_car,
                      const Color(0xFFF50057),
                    ), // Pink
                    _buildPartyButton("INC", Icons.pan_tool, Colors.blue),
                    _buildPartyButton(
                      "BJP",
                      Icons.local_florist,
                      Colors.orange,
                    ),
                    _buildPartyButton("CPM", Icons.handyman, Colors.red),
                    _buildPartyButton("CPI", Icons.agriculture, Colors.red),
                    _buildPartyButton("OTHER", Icons.more_horiz, Colors.black),
                  ],
                ),

                const SizedBox(height: 25),
                const Text(
                  "Demographic Details",
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
                const SizedBox(height: 15),

                // 3. Demographic Details Card
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey[300]!),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _buildDropdown(
                        "Occupation",
                        _occupationController,
                        _occupations,
                        Icons.work,
                      ),
                      const SizedBox(height: 15),
                      Row(
                        children: [
                          Expanded(
                            child: _buildDropdown(
                              "Religion",
                              _religionController,
                              _religions,
                              Icons.temple_buddhist,
                            ),
                          ),
                          const SizedBox(width: 15),
                          Expanded(
                            child: _buildDropdown(
                              "Caste",
                              _casteController,
                              _castes,
                              Icons.people,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 15),
                      _buildDropdown(
                        "Sub-Caste (Goud, Reddy, etc.)",
                        _subCasteController,
                        _subCastes,
                        Icons.subdirectory_arrow_right,
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),

                // 4. Mobile Number
                Container(
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey[300]!),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: TextField(
                    controller: _mobileController,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.phone),
                      hintText: "Mobile Number (Optional)",
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 14,
                      ),
                    ),
                  ),
                ),
                const Padding(
                  padding: EdgeInsets.only(left: 8.0, top: 8),
                  child: Text(
                    "Used only for follow-up communication",
                    style: TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ),
              ] else ...[
                // MESSAGE FOR NON-AVAILABLE VOTERS
                Container(
                  margin: const EdgeInsets.only(top: 40, bottom: 20),
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  child: Column(
                    children: [
                      Icon(
                        Icons.info_outline,
                        size: 48,
                        color: Colors.grey[600],
                      ),
                      const SizedBox(height: 16),
                      Text(
                        "Survey not required for this voter.",
                        style: TextStyle(
                          fontSize: 18,
                          color: Colors.grey[800],
                          fontWeight: FontWeight.w500,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        "Status: $_voterStatus",
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 30),

              // 5. Navigation Buttons
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton.icon(
                    onPressed: () => _navigate(false),
                    icon: const Icon(Icons.arrow_back),
                    label: const Text("Previous"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.purple[50],
                      foregroundColor: Colors.purple,
                    ),
                  ),
                  ElevatedButton(
                    onPressed: _save,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 40,
                        vertical: 12,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(25),
                      ),
                    ),
                    child: const Text(
                      "Save",
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  ElevatedButton.icon(
                    onPressed: () => _navigate(true),
                    icon: const Icon(Icons.arrow_forward),
                    label: const Text("Next"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.purple[50],
                      foregroundColor: Colors.purple,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 50),
            ],
          ),
        ),
      ),
    );
  }

  // --- CHANGED: Now takes activeColor ---
  Widget _buildPartyButton(String label, IconData icon, Color activeColor) {
    bool isSelected = _selectedParty == label;
    return GestureDetector(
      onTap: () => setState(() => _selectedParty = label),
      child: Container(
        decoration: BoxDecoration(
          // Active: Show activeColor. Inactive: White.
          color: isSelected ? activeColor : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            // Active: border same color (or transparent). Inactive: grey border.
            color: isSelected ? activeColor : Colors.grey[300]!,
          ),
          boxShadow: [
            if (!isSelected)
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              // Active: White icon. Inactive: Colored icon matching the brand.
              color: isSelected ? Colors.white : activeColor,
              size: 28,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                // Active: White text. Inactive: Black text.
                color: isSelected ? Colors.white : Colors.black,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDropdown(
    String label,
    TextEditingController controller,
    List<String> items,
    IconData icon,
  ) {
    String? currentVal = items.contains(controller.text)
        ? controller.text
        : null;

    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, size: 20, color: Colors.grey),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: BorderSide(color: Colors.grey[300]!),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: currentVal,
          isExpanded: true,
          hint: Text(
            "Select $label",
            style: const TextStyle(color: Colors.grey, fontSize: 13),
          ),
          items: items
              .map(
                (e) => DropdownMenuItem(
                  value: e,
                  child: Text(e, style: const TextStyle(fontSize: 14)),
                ),
              )
              .toList(),
          onChanged: (val) {
            if (val != null) {
              setState(() => controller.text = val);
            }
          },
        ),
      ),
    );
  }

  Widget _buildStatusButton(String value, String label, Color color) {
    print("Voter Status: $_voterStatus");
    bool isSelected = _voterStatus == value;
    return InkWell(
      onTap: () {
        if (value == "DEATH" && _voterStatus != "DEATH") {
          showDialog(
            context: context,
            builder: (ctx) => AlertDialog(
              title: const Text("Confirm Deceased"),
              content: const Text(
                "Please confirm this voter is deceased. This action ensures accuracy and cannot be easily undone.",
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(ctx).pop(),
                  child: const Text("Cancel"),
                ),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                  onPressed: () {
                    setState(() => _voterStatus = value);
                    Navigator.of(ctx).pop();
                  },
                  child: const Text(
                    "Confirm",
                    style: TextStyle(color: Colors.white),
                  ),
                ),
              ],
            ),
          );
        } else {
          setState(() {
            _voterStatus = value;
            print("Updated Voter Status to: $_voterStatus");
          });
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? color : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color),
        ),
        child: Row(
          children: [
            if (isSelected)
              const Icon(Icons.check, color: Colors.white, size: 16),
            if (isSelected) const SizedBox(width: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? Colors.white : color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
