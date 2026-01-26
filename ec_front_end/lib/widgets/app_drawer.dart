import 'package:flutter/material.dart';
import '../screens/voter_profile_screen.dart';
import '../screens/registration_screen.dart';
import '../screens/approval_screen.dart';
import '../services/offline_service.dart';

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      elevation: 16,
      child: Container(
        color: const Color(0xFFF8F9FA), // Light background
        child: Column(
          children: [
            // Header
            DrawerHeader(
              decoration: const BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black12,
                    blurRadius: 10,
                    offset: Offset(0, 5),
                  ),
                ],
              ),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.how_to_vote,
                      size: 50,
                      color: Color(0xFF1565C0),
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      "Election Survey Apps",
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1565C0),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "Official Surveyor Interface",
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 10),

            // Menu Items
            _buildMenuItem(
              context,
              icon: Icons.home_outlined,
              label: "Home",
              onTap: () {
                Navigator.pop(context);
                // Navigate to Home Dashboard if it existed
              },
            ),

            // MANUAL SYNC BUTTON
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 4,
              ),
              leading: const Icon(Icons.sync, color: Colors.orange),
              title: const Text(
                "Sync Offline Data",
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: Colors.orange,
                ),
              ),
              onTap: () async {
                Navigator.pop(context); // Close Drawer
                _showSyncDialog(context);
              },
            ),

            // Highlighted Start Survey Item
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFE3F2FD), // Light blue Highlight
                borderRadius: BorderRadius.circular(12),
              ),
              child: ListTile(
                leading: const Icon(Icons.poll, color: Color(0xFF1565C0)),
                title: const Text(
                  "Start Survey",
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1565C0),
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  // Ensure we are on the profile/search flow
                  if (context.widget is! VoterProfileScreen) {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const VoterProfileScreen(),
                      ),
                    );
                  }
                },
              ),
            ),

            _buildMenuItem(
              context,
              icon: Icons.support_agent_outlined, // Contact Us
              label: "Contact Us",
              onTap: () {
                Navigator.pop(context);
                _showInfo(
                  context,
                  "Contact Support",
                  "Helpline: 1800-123-4567\nWhatsApp: +91 98765 43210",
                );
              },
            ),

            _buildMenuItem(
              context,
              icon: Icons.info_outline, // Help
              label: "Help / Guidelines",
              onTap: () {
                Navigator.pop(context);
                _showInfo(
                  context,
                  "Guidelines",
                  "1. Verify voter identity.\n2. Do NOT influence votes.\n3. Mark 'Other' for unlisted parties.",
                );
              },
            ),

            // Added Approval Status Option
            _buildMenuItem(
              context,
              icon: Icons.verified_user_outlined,
              label: "Approval Status",
              onTap: () {
                Navigator.pop(context);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const ApprovalScreen(),
                  ),
                );
              },
            ),

            const Spacer(),
            const Divider(),

            // Logout
            ListTile(
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 8,
              ),
              leading: const Icon(
                Icons.logout,
                color: Color(0xFFD32F2F),
              ), // Red accent
              title: const Text(
                "Logout",
                style: TextStyle(
                  color: Color(0xFFD32F2F),
                  fontWeight: FontWeight.w600,
                ),
              ),
              onTap: () {
                // Clear session and go to Registration
                Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute(
                    builder: (context) => const RegistrationScreen(),
                  ),
                  (Route<dynamic> route) => false,
                );
              },
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
      leading: Icon(icon, color: Colors.grey[800]),
      title: Text(
        label,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w500,
          color: Colors.grey[900],
        ),
      ),
      onTap: onTap,
    );
  }

  Future<void> _showSyncDialog(BuildContext context) async {
    // Show Loading
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => const Center(child: CircularProgressIndicator()),
    );

    // Perform Sync
    final offline = OfflineService();
    int pending = offline.getPendingCount();

    // Slight delay to show loading if 0
    if (pending == 0) await Future.delayed(const Duration(milliseconds: 500));

    int synced = await offline.syncPendingVotes();

    // Close Loading
    if (context.mounted) Navigator.pop(context);

    // Show Result
    if (context.mounted) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text(pending == 0 ? "Up to Date" : "Sync Complete"),
          content: Text(
            pending == 0
                ? "No offline votes found on this device."
                : "Synced $synced out of $pending votes to the server.",
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text("OK"),
            ),
          ],
        ),
      );
    }
  }

  void _showInfo(BuildContext context, String title, String content) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Close"),
          ),
        ],
      ),
    );
  }
}
