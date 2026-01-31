import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/api_service.dart';

class BulkUploadScreen extends StatefulWidget {
  const BulkUploadScreen({super.key});

  @override
  State<BulkUploadScreen> createState() => _BulkUploadScreenState();
}

class _BulkUploadScreenState extends State<BulkUploadScreen> {
  final ApiService _api = ApiService();

  // Location State
  int? _selectedDistrictId;
  int? _selectedMandalId;
  int? _selectedVillageId;
  int? _selectedWardNo; // Optional, can be derived

  // Dropdown Data
  List<dynamic> _districts = [];
  List<dynamic> _mandals = [];
  List<dynamic> _villages = [];
  List<dynamic> _wards = [];

  bool _isLoading = false;
  String? _statusMessage;
  bool _isSuccess = false;

  @override
  void initState() {
    super.initState();
    _loadDistricts();
  }

  Future<void> _loadDistricts() async {
    try {
      final districts = await _api.getDistricts();
      setState(() => _districts = districts);
    } catch (e) {
      print("Error loading districts: $e");
    }
  }

  Future<void> _loadMandals(int districtId) async {
    try {
      final mandals = await _api.getMandals(districtId);
      setState(() {
        _mandals = mandals;
        _villages = [];
        _selectedMandalId = null;
        _selectedVillageId = null;
      });
    } catch (e) {
      print("Error loading mandals: $e");
    }
  }

  Future<void> _loadVillages(int mandalId) async {
    try {
      final villages = await _api.getVillages(mandalId);
      setState(() {
        _villages = villages;
        _selectedVillageId = null;
      });
    } catch (e) {
      print("Error loading villages: $e");
    }
  }

  Future<void> _pickAndUpload() async {
    if (_selectedVillageId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select a Village first")),
      );
      return;
    }

    try {
      // Pick File
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['csv'],
        withData: true, // Important for Web
      );

      if (result != null) {
        setState(() {
          _isLoading = true;
          _statusMessage = "Uploading...";
          _isSuccess = false;
        });

        // Prepare Multipart Request
        final bytes = result.files.first.bytes;
        final filename = result.files.first.name;

        var uri = Uri.parse('${ApiService.baseUrl}/voters/upload_bulk');
        var request = http.MultipartRequest('POST', uri);

        // Add Admin Token Header
        request.headers['x-admin-token'] = 'admin-secret-123';

        request.files.add(
          http.MultipartFile.fromBytes('file', bytes!, filename: filename),
        );

        // Add Location Context (Critical for Smart Parse)
        request.fields['district_id'] = _selectedDistrictId.toString();
        request.fields['mandal_id'] = _selectedMandalId.toString();
        request.fields['village_id'] = _selectedVillageId.toString();
        // Optional Ward Context if selected (implied)

        var streamedResponse = await request.send();
        var response = await http.Response.fromStream(streamedResponse);

        if (response.statusCode == 200) {
          final json = jsonDecode(response.body);
          String msg =
              "Success!\nProcessed: ${json['total_processed']}\nAdded: ${json['added']}\nUpdated: ${json['updated']}";

          if (json['errors'] != null && (json['errors'] as List).isNotEmpty) {
            msg +=
                "\n\nErrors:\n" + (json['errors'] as List).take(3).join("\n");
          }

          setState(() {
            _statusMessage = msg;
            _isSuccess = true;
          });
        } else {
          throw Exception("Server Error: ${response.body}");
        }
      }
    } catch (e) {
      setState(() {
        _statusMessage = "Upload Failed: $e";
        _isSuccess = false;
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Bulk Upload Voters")),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              "Select Target Location",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),

            // District Dropdown
            DropdownButtonFormField<int>(
              value: _selectedDistrictId,
              decoration: const InputDecoration(
                labelText: "District",
                border: OutlineInputBorder(),
              ),
              items: _districts
                  .map(
                    (d) => DropdownMenuItem<int>(
                      value: d['id'],
                      child: Text(d['name']),
                    ),
                  )
                  .toList(),
              onChanged: (val) {
                if (val != null) {
                  setState(() => _selectedDistrictId = val);
                  _loadMandals(val);
                }
              },
            ),
            const SizedBox(height: 12),

            // Mandal Dropdown
            DropdownButtonFormField<int>(
              value: _selectedMandalId,
              decoration: const InputDecoration(
                labelText: "Mandal",
                border: OutlineInputBorder(),
              ),
              items: _mandals
                  .map(
                    (m) => DropdownMenuItem<int>(
                      value: m['id'],
                      child: Text(m['name']),
                    ),
                  )
                  .toList(),
              onChanged: (val) {
                if (val != null) {
                  setState(() => _selectedMandalId = val);
                  _loadVillages(val);
                }
              },
            ),
            const SizedBox(height: 12),

            // Village Dropdown
            DropdownButtonFormField<int>(
              value: _selectedVillageId,
              decoration: const InputDecoration(
                labelText: "Village",
                border: OutlineInputBorder(),
              ),
              items: _villages
                  .map(
                    (v) => DropdownMenuItem<int>(
                      value: v['id'],
                      child: Text(v['name']),
                    ),
                  )
                  .toList(),
              onChanged: (val) {
                setState(() => _selectedVillageId = val);
              },
            ),

            const SizedBox(height: 32),

            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else
              ElevatedButton.icon(
                onPressed: _selectedVillageId == null ? null : _pickAndUpload,
                icon: const Icon(Icons.upload_file),
                label: const Text("Select CSV & Upload"),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                  textStyle: const TextStyle(fontSize: 18),
                ),
              ),

            if (_statusMessage != null) ...[
              const SizedBox(height: 24),
              Card(
                color: _isSuccess ? Colors.green[50] : Colors.red[50],
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(
                    _statusMessage!,
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: _isSuccess ? Colors.green[800] : Colors.red[800],
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
