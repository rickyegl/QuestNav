#!/usr/bin/env python3
"""
NetworkTables Debug Script for QuestNav
Tests each NetworkTables interaction from questnav.py individually
"""

import ntcore
import time
import sys
import os

# Add the generated protobuf code to the path
#sys.path.append(os.path.join(os.path.dirname(__file__), "../questnav-lib/src/generate/main/python"))

import commands_pb2
import data_pb2
import geometry2d_pb2
from testResults import TestResults

# Configuration
NT_TABLE_NAME = "SmartDashboard/QuestNavManager"
QN_TABLE_NAME = "QuestNav"
NT_SIM_IP = "127.0.0.1"
NT_ROBOT_IP = "10.66.47.2"
TEST_SERVER = NT_SIM_IP  # Change this to test different servers

class NetworkTablesDebugger:
    def __init__(self, server_ip, results=None):
        self.server_ip = server_ip
        self.inst = None
        self.robotTable = None
        self.headsetTable = None
        self.command_topic = None
        self.device_data_sub = None
        self.results = results or TestResults("NetworkTables Debug")

    def print(self, message=""):
        """Print using results handler if available, otherwise regular print"""
        if self.results:
            self.results.print(message)
        else:
            print(message)

    def test_1_connection(self):
        """Test 1: Connect to NetworkTables server"""
        self.print("\n" + "="*60)
        self.print("TEST 1: Connection to NetworkTables Server")
        self.print("="*60)

        try:
            self.inst = ntcore.NetworkTableInstance.getDefault()
            self.inst.startClient4("debug_dashboard")
            self.inst.setServer(self.server_ip)

            self.print(f"Attempting to connect to: {self.server_ip}")
            self.print("Waiting for connection...")

            # Wait up to 5 seconds for connection
            timeout = 5.0
            start_time = time.time()
            while not self.inst.isConnected() and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.inst.isConnected():
                self.print(f"✓ SUCCESS: Connected to {self.server_ip}")
                return True
            else:
                self.print(f"✗ FAILED: Could not connect to {self.server_ip} within {timeout}s")
                return False

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def test_2_get_table(self):
        """Test 2: Get NetworkTables table"""
        self.print("\n" + "="*60)
        self.print("TEST 2: Get NetworkTables Table")
        self.print("="*60)

        try:
            if not self.inst or not self.inst.isConnected():
                self.print("✗ FAILED: Not connected to server (prerequisite failed)")
                return False

            self.robotTable = self.inst.getTable(NT_TABLE_NAME)
            self.headsetTable = self.inst.getTable(QN_TABLE_NAME)
            self.print(f"Table name: {NT_TABLE_NAME}")
            self.print(f"✓ SUCCESS: Got table reference")
            return True

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def test_3_create_command_publisher(self):
        """Test 3: Create command topic publisher"""
        self.print("\n" + "="*60)
        self.print("TEST 3: Create Command Topic Publisher")
        self.print("="*60)

        try:
            if not self.robotTable:
                self.print("✗ FAILED: Table not initialized (prerequisite failed)")
                return False

            self.command_topic = self.headsetTable.getRawTopic("request").publish("raw")
            self.print(f"Topic: {QN_TABLE_NAME}/request")
            self.print(f"Type: raw")
            self.print(f"✓ SUCCESS: Created command publisher")
            return True

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def test_4_create_device_data_subscriber(self):
        """Test 4: Subscribe to device_data topic"""
        self.print("\n" + "="*60)
        self.print("TEST 4: Subscribe to device_data Topic")
        self.print("="*60)

        try:
            if not self.robotTable:
                self.print("✗ FAILED: Table not initialized (prerequisite failed)")
                return False

            empty_device_data = data_pb2.ProtobufQuestNavDeviceData()
            self.device_data_sub = self.headsetTable.getRawTopic("deviceData").subscribe(
                "questnav.protos.data.ProtobufQuestNavDeviceData",
                empty_device_data.SerializeToString()
            )
            self.print(f"Topic: {QN_TABLE_NAME}/deviceData")
            self.print(f"Type: questnav.protos.data.ProtobufQuestNavDeviceData")
            self.print(f"✓ SUCCESS: Created device_data subscriber")
            return True

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def test_5_read_device_data(self):
        """Test 5: Read device_data"""
        self.print("\n" + "="*60)
        self.print("TEST 5: Read device_data")
        self.print("="*60)

        try:
            if not self.device_data_sub:
                self.print("✗ FAILED: device_data subscriber not initialized")
                return False

            # Wait a bit for data
            time.sleep(0.5)

            device_data_raw = self.device_data_sub.get()
            if device_data_raw:
                device_data = data_pb2.ProtobufQuestNavDeviceData()
                device_data.ParseFromString(device_data_raw)
                #self.print(str(device_data))
                self.print(f"✓ SUCCESS: Received device data")
                self.print(f"  Active tag: {device_data.active_tag}")
                self.print(f"  Active layout: {device_data.active_layout}")
                self.print(f"  Active field: {device_data.active_field}")
                self.print(f"  Currently tracking: {device_data.currently_tracking}")
                self.print(f"  Battery percent: {device_data.battery_percent}%")
                self.print(f"  Tracked anchors: {device_data.tracked_anchors_count}")
                self.print(f"  Untracked anchors: {device_data.untracked_anchors_count}")

                self.print(f"\n  Saved tags count: {len(device_data.saved_tags)}")
                if device_data.saved_tags:
                    self.print(f"  Saved tags (1=saved with UUID, 0=not saved):")
                    saved_tags = [tag_id for tag_id, status in device_data.saved_tags.items() if status == 1]
                    not_saved_tags = [tag_id for tag_id, status in device_data.saved_tags.items() if status == 0]
                    if saved_tags:
                        self.print(f"    Saved: {saved_tags}")
                    if not_saved_tags:
                        self.print(f"    Not saved: {not_saved_tags}")

                self.print(f"\n  Tag status count: {len(device_data.tag_status)}")
                if device_data.tag_status:
                    self.print(f"  Tag status (1=tracked/localized, 0=not tracked):")
                    tracked_tags = [tag_id for tag_id, status in device_data.tag_status.items() if status == 1]
                    untracked_tags = [tag_id for tag_id, status in device_data.tag_status.items() if status == 0]
                    if tracked_tags:
                        self.print(f"    Tracked: {tracked_tags}")
                    if untracked_tags:
                        self.print(f"    Not tracked: {untracked_tags}")

                return True
            else:
                self.print(f"⚠ WARNING: No device data available yet")
                self.print(f"  This may be normal if QuestNav hasn't published data")
                return True  # Not a failure, just no data yet

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def test_6_publish_calibrate_command(self):
        """Test 6: Publish CALIBRATE_TAG command"""
        self.print("\n" + "="*60)
        self.print("TEST 6: Publish CALIBRATE_TAG Command")
        self.print("="*60)

        try:
            if not self.command_topic:
                self.print("✗ FAILED: Command topic not initialized")
                return False

            # Create the main command message
            command = commands_pb2.ProtobufQuestNavCommand()
            command.type = commands_pb2.CALIBRATE_TAG
            command.command_id = int(time.time())

            # Create the calibration payload
            calibration_payload = commands_pb2.CalibrationPayload()

            # Create a test headset pose
            headset_pose = geometry2d_pb2.ProtobufPose2d()
            headset_pose.translation.x = 1.0
            headset_pose.translation.y = 2.0
            headset_pose.rotation.value = 0.5

            calibration_payload.headset_pose.CopyFrom(headset_pose)
            command.calibration_payload.CopyFrom(calibration_payload)

            # Set test tag ID
            test_tag_id = 1
            command.apriltag_index_payload.value = test_tag_id

            # Serialize and publish
            serialized_command = command.SerializeToString()
            self.command_topic.set(serialized_command)

            self.print(f"✓ SUCCESS: Published CALIBRATE_TAG command")
            self.print(f"  Command ID: {command.command_id}")
            self.print(f"  Tag ID: {test_tag_id}")
            self.print(f"  Pose: x={headset_pose.translation.x}, y={headset_pose.translation.y}, rot={headset_pose.rotation.value}")
            return True

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def run_all_tests(self):
        """Run all NetworkTables tests in sequence"""
        self.print("\n" + "#"*60)
        self.print("# NetworkTables Debug Tests for QuestNav")
        self.print(f"# Testing against server: {self.server_ip}")
        self.print("#"*60)

        tests = [
            self.test_1_connection,
            self.test_2_get_table,
            self.test_3_create_command_publisher,
            self.test_4_create_device_data_subscriber,
            self.test_5_read_device_data,
            self.test_6_publish_calibrate_command,
        ]

        for test in tests:
            self.results.start_test(test.__name__)
            try:
                result = test()
                self.results.end_test(test.__name__, result)
            except Exception as e:
                self.print(f"\n✗ CRITICAL ERROR in {test.__name__}: {e}")
                self.results.end_test(test.__name__, False)

        # Summary
        self.print("\n" + "#"*60)
        self.print("# TEST SUMMARY")
        self.print("#"*60)

        passed = sum(1 for _, result, _ in self.results.tests if result)
        total = len(self.results.tests)

        for test_name, result, _ in self.results.tests:
            status = "✓ PASS" if result else "✗ FAIL"
            self.print(f"{status}: {test_name}")

        self.print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            self.print("\n🎉 All tests passed!")
        else:
            self.print(f"\n⚠ {total - passed} test(s) failed")

        return passed == total


def main():
    print("QuestNav NetworkTables Debugger")
    print("================================\n")

    # Allow command-line override of server
    if len(sys.argv) > 1:
        server = sys.argv[1]
    else:
        server = TEST_SERVER

    # Create results handler
    results = TestResults(f"QuestNav NetworkTables Debug - {server}")
    debugger = NetworkTablesDebugger(server, results)

    try:
        success = debugger.run_all_tests()

        # Generate HTML report
        html_file = results.generate_html("nt_debug_results.html")
        print(f"\n{'='*60}")
        print(f"HTML Report generated: {html_file}")
        print(f"{'='*60}")

        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()