#!/usr/bin/env python3
"""
NetworkTables Debug Script for QuestNav
Tests each NetworkTables interaction from questnav.py individually
"""

import ntcore
import time
import sys
import os
import wpimath.geometry

# Add the generated protobuf code to the path
#sys.path.append(os.path.join(os.path.dirname(__file__), "../questnav-lib/src/generate/main/python"))

from testResults import TestResults

# Configuration
NT_SIM_IP = "127.0.0.1"
NT_ROBOT_IP = "10.66.47.2"
TEST_SERVER = NT_SIM_IP  # Change this to test different servers

class NetworkTablesDebugger:
    def __init__(self, server_ip, results=None):
        self.server_ip = server_ip
        self.inst = None
        self.robot_pose_sub = None
        self.results = results or TestResults("NetworkTables Debug - Robot Pose Only")

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

    def test_2_create_robot_pose_subscriber(self):
        """Test 2: Subscribe to robot_pose_sub topic"""
        self.print("\n" + "="*60)
        self.print("TEST 2: Subscribe to Robot Pose Topic")
        self.print("="*60)

        try:
            if not self.inst or not self.inst.isConnected():
                self.print("✗ FAILED: Not connected to server (prerequisite failed)")
                return False

            self.robot_pose_sub = self.inst.getTable("AdvantageKit/RealOutputs/Drive").getStructTopic("Pose",wpimath.geometry.Pose2d).subscribe(wpimath.geometry.Pose2d())
            self.print(f"Topic: AdvantageKit/RealOutputs/Drive/Pose")
            self.print(f"Type: Pose2d struct")
            self.print(f"✓ SUCCESS: Created robot_pose_sub subscriber")
            self.print(self.robot_pose_sub.get())
            return True

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            return False

    def test_3_read_robot_pose(self):
        """Test 3: Read robot_pose_sub data"""
        self.print("\n" + "="*60)
        self.print("TEST 3: Read Robot Pose Data")
        self.print("="*60)

        try:
            if not self.robot_pose_sub:
                self.print("✗ FAILED: robot_pose_sub subscriber not initialized")
                return False

            # Wait a bit for data
            time.sleep(0.5)

            robot_pose_data = self.robot_pose_sub.get()
            if robot_pose_data:
                self.print(f"Raw data received (Pose2d struct)")
                self.print(f"  Type: {type(robot_pose_data)}")
                self.print(f"  Value: {robot_pose_data}")
                
                # Parse as Pose2d struct
                x = robot_pose_data.X()
                y = robot_pose_data.Y()
                rotation = robot_pose_data.rotation().radians()

                self.print(f"✓ SUCCESS: Received robot pose data")
                self.print(f"  X: {x}")
                self.print(f"  Y: {y}")
                self.print(f"  Rotation: {rotation} radians")
                return True
            else:
                self.print(f"⚠ WARNING: No robot pose data available yet")
                self.print(f"  This may be normal if AdvantageKit hasn't published data")
                self.print(f"  Make sure the robot code is running and publishing to this topic")
                return True  # Not a failure, just no data yet

        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            self.print(traceback.format_exc())
            return False

    def test_4_continuous_read_robot_pose(self):
        """Test 4: Continuously read robot_pose_sub data for 10 seconds"""
        self.print("\n" + "="*60)
        self.print("TEST 4: Continuous Read Robot Pose Data (10 seconds)")
        self.print("="*60)

        try:
            if not self.robot_pose_sub:
                self.print("✗ FAILED: robot_pose_sub subscriber not initialized")
                return False

            self.print("Reading robot pose data continuously for 10 seconds...")
            self.print("Press Ctrl+C to stop early\n")

            start_time = time.time()
            read_count = 0
            last_pose = None

            while (time.time() - start_time) < 10.0:
                robot_pose_data = self.robot_pose_sub.get()
                if robot_pose_data:
                    # Parse as Pose2d struct
                    x = robot_pose_data.X()
                    y = robot_pose_data.Y()
                    rotation = robot_pose_data.rotation().radians()

                    # Only print if pose changed
                    current_pose = (x, y, rotation)
                    if current_pose != last_pose:
                        read_count += 1
                        self.print(f"[{read_count}] X: {x:.3f}, Y: {y:.3f}, Rot: {rotation:.3f} rad")
                        last_pose = current_pose

                time.sleep(0.1)  # Read at 10 Hz

            self.print(f"\n✓ SUCCESS: Read {read_count} pose updates over 10 seconds")
            return True

        except KeyboardInterrupt:
            self.print(f"\n⚠ Stopped by user")
            return True
        except Exception as e:
            self.print(f"✗ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            self.print(traceback.format_exc())
            return False

    def run_all_tests(self):
        """Run all NetworkTables tests in sequence"""
        self.print("\n" + "#"*60)
        self.print("# NetworkTables Debug Tests - Robot Pose Only")
        self.print(f"# Testing against server: {self.server_ip}")
        self.print("#"*60)

        tests = [
            self.test_1_connection,
            self.test_2_create_robot_pose_subscriber,
            self.test_3_read_robot_pose,
            self.test_4_continuous_read_robot_pose,
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
    print("QuestNav NetworkTables Debugger - Robot Pose Only")
    print("=================================================\n")

    # Allow command-line override of server
    if len(sys.argv) > 1:
        server = sys.argv[1]
    else:
        server = TEST_SERVER

    # Create results handler
    results = TestResults(f"QuestNav Robot Pose Debug - {server}")
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