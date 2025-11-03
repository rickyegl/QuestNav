import tkinter as tk
from tkinter import messagebox
import ntcore
import os
import time
import sys
import wpimath.geometry

# Add the generated protobuf code to the path
#sys.path.append(os.path.join(os.path.dirname(__file__), "../questnav-lib/src/generate/main/python"))

import commands_pb2
import data_pb2
import geometry2d_pb2


# Attempt to import Pillow for image manipulation.
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("Pillow library not found. Please install it: pip install Pillow")
    print("The color filter feature will be disabled.")
    Image = None
    ImageTk = None

# --- Configuration ---

NT_TABLE_NAME = "SmartDashboard/QuestNavManager"
QN_TABLE_NAME = "QuestNav"
UPDATE_PERIOD_MS = 500

nt_sim_ip = "127.0.0.1"
nt_robot_ip = "10.66.47.2"
nt_server_ip = nt_sim_ip

# --- AprilTag Data ---
APRILTAG_COORDS = {
    1: (750, 333), 2: (750, 100), 3: (550, 88),  4: (500, 130),
    5: (500, 300), 6: (640, 260), 7: (667, 220), 8: (650, 170),
    9: (580, 170), 10: (555, 220), 11: (580, 265),12: (160, 333),
    13: (160, 100), 14: (400, 140), 15: (400, 300), 16: (350, 350),
    17: (260, 260), 18: (240, 220), 19: (260, 165), 20: (320, 165),
    21: (340, 218), 22: (320, 260)
}

class QuestNavManagerDashboard:
    # --- Appearance Configuration ---
    TAG_DISPLAY_SIZE = (50, 50)
    DESATURATION_FACTOR = 0.4
    TAG_ID_FONT_COLOR = "yellow"
    TAG_ID_OUTLINE_COLOR = "black"
    TAG_ID_FONT_SIZE_RATIO = 0.5

    def __init__(self, master):
        self.master = master
        master.title("QuestNav Manager")
        master.geometry("820x520+560+0")
        master.configure(bg="#1a1a2e")

        self.field_bg_photo = None
        self.tag_data = {}
        self.initial_sync_done = False

        # BooleanVar to hold the state of the enabled checkbox
        self.enabled_var = tk.BooleanVar(value=True)

        self._setup_ui()

        self.inst = ntcore.NetworkTableInstance.getDefault()
        self.robotTable = self.inst.getTable(NT_TABLE_NAME)
        self.headsetTable = self.inst.getTable(QN_TABLE_NAME)
        self.command_topic = self.headsetTable.getRawTopic("request").publish("raw")
        self.robot_pose_sub = self.inst.getTable("AdvantageKit/RealOutputs/Drive").getStructTopic("Pose", wpimath.geometry.Pose2d).subscribe(wpimath.geometry.Pose2d())
        empty_device_data = data_pb2.ProtobufQuestNavDeviceData()
        self.device_data_sub = self.headsetTable.getRawTopic("deviceData").subscribe(
            "questnav.protos.data.ProtobufQuestNavDeviceData",
            empty_device_data.SerializeToString()
        )

        self.inst.startClient4("dashboard")
        self.inst.setServer(nt_server_ip)

        self._draw_field_and_tags()
        self.periodic_update()

    def _setup_ui(self):
        control_frame = tk.Frame(self.master, bg="#2a2a3e", padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(control_frame, text="Field Select:", fg="white", bg=control_frame['bg']).pack(side=tk.LEFT, padx=(10, 5))
        self.field_var = tk.StringVar(value="-1")
        tk.Entry(control_frame, textvariable=self.field_var, width=5).pack(side=tk.LEFT)
        tk.Label(control_frame, text="Layout Select:", fg="white", bg=control_frame['bg']).pack(side=tk.LEFT, padx=(20, 5))
        self.layout_var = tk.StringVar(value="-1")
        tk.Entry(control_frame, textvariable=self.layout_var, width=5).pack(side=tk.LEFT)
        apply_button = tk.Button(control_frame, text="Apply", command=self.on_apply_clicked, bg="#39FF14", fg="black", relief=tk.FLAT)
        apply_button.pack(side=tk.LEFT, padx=20)

        # --- ADDED DELETE BUTTON ---
        delete_button = tk.Button(control_frame, text="Delete", command=self.on_delete_clicked, bg="#FF4136", fg="white", relief=tk.FLAT)
        delete_button.pack(side=tk.LEFT, padx=(0, 20))
        # --- END ADDED SECTION ---

        calibrate_button = tk.Button(control_frame, text="Calibrate", command=self.on_calibrate_clicked, bg="#FFA500", fg="black", relief=tk.FLAT)
        calibrate_button.pack(side=tk.RIGHT, padx=10)

        # Enabled/Disabled checkbox
        self.enabled_check = tk.Checkbutton(
            control_frame,
            text="Enabled",
            variable=self.enabled_var,
            command=self.on_enabled_toggle,
            fg="white",
            bg=control_frame['bg'],
            selectcolor="#1a1a2e",
            activebackground=control_frame['bg'],
            activeforeground="white",
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.enabled_check.pack(side=tk.RIGHT, padx=5)

        self.canvas = tk.Canvas(self.master, width=800, height=450, bg="black", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, pady=5)
        self.status_label = tk.Label(self.master, text="Connecting...", bd=1, relief=tk.SUNKEN, anchor=tk.W, fg="white", bg="#333")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _draw_field_and_tags(self):
        try:
            self.field_bg_photo = ImageTk.PhotoImage(file="field.png")
            self.canvas.create_image(0, 0, image=self.field_bg_photo, anchor=tk.NW)
        except Exception as e:
            self.canvas.create_text(400, 225, text=f"Error loading field.png:\n{e}", fill="red", font=("Arial", 14))

        for tag_id, coords in APRILTAG_COORDS.items():
            try:
                img_path = f"apriltags/{tag_id}.png"
                if not os.path.exists(img_path): self._generate_placeholder_tag_image(tag_id)

                with Image.open(img_path) as img:
                    resized_img = img.resize(self.TAG_DISPLAY_SIZE, Image.Resampling.NEAREST)
                    self._draw_id_on_image(resized_img, tag_id, is_active=False)
                    original_photo = ImageTk.PhotoImage(resized_img)

                canvas_tag = f"clickable_tag_{tag_id}"
                canvas_id = self.canvas.create_image(coords[0], coords[1], image=original_photo, tags=canvas_tag)

                self.canvas.tag_bind(canvas_tag, "<Button-1>", lambda event, id=tag_id: self.handle_tag_click(event, id))
                self.canvas.tag_bind(canvas_tag, "<Enter>", self.on_tag_enter)
                self.canvas.tag_bind(canvas_tag, "<Leave>", self.on_tag_leave)

                self.tag_data[tag_id] = {
                    'canvas_id': canvas_id, 'original_photo': original_photo,
                    'filtered_photos': {}, 'current_filter': None
                }
            except Exception as e:
                print(f"Error loading or placing tag {tag_id}: {e}")

    def handle_tag_click(self, event, tag_id):
        """Called when a tag is clicked. Publishes the ID to NetworkTables."""
        if not self.inst.isConnected():
            print(f"Clicked Tag {tag_id}, but not connected to NT server.")
            messagebox.showwarning("Not Connected", "Cannot set active tag. Not connected to NetworkTables.")
            return

        print(f"Clicked Tag {tag_id}. Sending 'CALIBRATE_TAG' on NetworkTables.")
        
        # Create the main command message
        command = commands_pb2.ProtobufQuestNavCommand()
        command.type = commands_pb2.CALIBRATE_TAG
        command.command_id = int(time.time()) # Use timestamp for a unique ID

        # Create the calibration payload
        calibration_payload = commands_pb2.CalibrationPayload()

        # Read robot pose from AdvantageKit/RealOutputs/Drive/Pose
        robot_pose_data = self.robot_pose_sub.get()
        if robot_pose_data:
            # Parse as Pose2d struct
            x = robot_pose_data.X()
            y = robot_pose_data.Y()
            rotation = robot_pose_data.rotation().radians()

            robot_pose = geometry2d_pb2.ProtobufPose2d()
            robot_pose.translation.x = x
            robot_pose.translation.y = y
            robot_pose.rotation.value = rotation
            calibration_payload.headset_pose.CopyFrom(robot_pose)
        else:
            return

        # Assign the payload to the command
        command.calibration_payload.CopyFrom(calibration_payload)
        command.calibration_payload.apriltag_index = tag_id

        # Set the active tag in the payload
        #command.apriltag_index_payload.value = tag_id

        # Serialize the command to a byte string
        serialized_command = command.SerializeToString()

        # Publish the command
        self.command_topic.set(serialized_command)

    def on_tag_enter(self, event):
        """Changes the cursor to a hand to show the tag is clickable."""
        self.canvas.config(cursor="hand2")

    def on_tag_leave(self, event):
        """Changes the cursor back to the default."""
        self.canvas.config(cursor="")

    def _draw_id_on_image(self, image, tag_id, is_active=False):
        if not Image: return
        d = ImageDraw.Draw(image)
        text_to_draw = str(tag_id)
        try:
            font_size = int(self.TAG_DISPLAY_SIZE[1] * self.TAG_ID_FONT_SIZE_RATIO)
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

        text_bbox = d.textbbox((0,0), text_to_draw, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (self.TAG_DISPLAY_SIZE[0] - text_width) / 2
        y = (self.TAG_DISPLAY_SIZE[1] - text_height) / 2 - (text_bbox[1] * 0.5)

        # Choose text color based on active state
        text_color = "white" if is_active else self.TAG_ID_FONT_COLOR

        outline_thickness = 2
        for i in range(-outline_thickness, outline_thickness + 1):
            for j in range(-outline_thickness, outline_thickness + 1):
                 if i != 0 or j != 0:
                    d.text((x + i, y + j), text_to_draw, font=font, fill=self.TAG_ID_OUTLINE_COLOR)
        d.text((x, y), text_to_draw, font=font, fill=text_color)

    def on_calibrate_clicked(self):
        """Called when the Calibrate button is clicked. Sends a command to calibrate the tag."""
        if not self.inst.isConnected():
            messagebox.showwarning("Not Connected", "Cannot start calibration. Not connected to NetworkTables.")
            return

        # Create the main command message
        command = commands_pb2.ProtobufQuestNavCommand()
        command.type = commands_pb2.CALIBRATE_TAG
        command.command_id = int(time.time()) # Use timestamp for a unique ID

        # Create the calibration payload
        calibration_payload = commands_pb2.CalibrationPayload()

        # Create and populate the headset pose
        headset_pose = geometry2d_pb2.ProtobufPose2d()
        headset_pose.translation.x = 0.0  # Replace with actual headset X
        headset_pose.translation.y = 0.0  # Replace with actual headset Y
        headset_pose.rotation.value = 0.0    # Replace with actual headset rotation in radians

        # Assign the pose to the payload
        calibration_payload.headset_pose.CopyFrom(headset_pose)

        # Assign the payload to the command
        command.calibration_payload.CopyFrom(calibration_payload)

        # Serialize the command to a byte string
        serialized_command = command.SerializeToString()

        # Publish the command
        print("Sending CALIBRATE_TAG command...")
        self.command_topic.set(serialized_command)

    # Method to handle the enabled/disabled toggle
    def on_enabled_toggle(self):
        """Called when the Enabled checkbox is toggled. Publishes the value to NetworkTables."""
        if not self.inst.isConnected():
            messagebox.showwarning("Not Connected", "Cannot change 'Enabled' state. Not connected to NetworkTables.")
            # Revert the checkbox to prevent the UI from being out of sync with the server
            last_known_state = self.robotTable.getBoolean("Enabled", self.enabled_var.get())
            self.enabled_var.set(last_known_state)
            return

        is_enabled = self.enabled_var.get()
        print(f"Setting 'Enabled' to {is_enabled} on NetworkTables.")
        self.robotTable.getBooleanTopic("enabled").publish().set(is_enabled)

    def on_apply_clicked(self):
        if not self.inst.isConnected():
            messagebox.showwarning("Not Connected", "Cannot apply changes. Not connected to NT server.")
            return
        try:
            field_index = int(self.field_var.get())
            layout_index = int(self.layout_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Field and Layout must be integer numbers.")
            return

        # self.robotTable.getDoubleTopic("SelectedFieldIndex").publish().set(field_index)
        # self.robotTable.getDoubleTopic("SelectedLayoutIndex").publish().set(layout_index)
        self.robotTable.getBooleanTopic("Changed").publish().set(True)

    # --- ADDED --- Method for the delete button
    def on_delete_clicked(self):
        """Shows a confirmation and then sets 'SetDelete' to 1 on NetworkTables."""
        # 1. Check for connection
        if not self.inst.isConnected():
            messagebox.showwarning("Not Connected", "Cannot delete. Not connected to NetworkTables.")
            return

        # 2. Show confirmation dialog
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the currently selected layout? This cannot be undone."):
            # 3. If user confirms, publish to NetworkTables
            print("Delete confirmed. Setting 'SetDelete' to 1.")
            self.robotTable.getBooleanTopic("SetDelete").publish().set(True)
        else:
            # 4. If user cancels, do nothing (optional: print a message)
            print("Delete action cancelled by user.")
    # --- END ADDED SECTION ---

    def periodic_update(self):
        global nt_robot_ip
        global nt_server_ip
        global nt_sim_ip
        """Main loop called periodically to update connection status and sync data."""
        if self.inst.isConnected():
            self.status_label.config(text=f"Connected to {nt_server_ip}", fg="#39FF14")

            device_data_raw = self.device_data_sub.get()
            if device_data_raw:
                device_data = data_pb2.ProtobufQuestNavDeviceData()
                device_data.ParseFromString(device_data_raw)

                if not self.initial_sync_done:
                    self.sync_inputs_from_nt(device_data)
                    self.initial_sync_done = True

                self.update_tag_colors_from_nt(device_data)
        else:
            self.status_label.config(text=f"Disconnected - trying to connect to {nt_server_ip}", fg="#FF4136")
            self.initial_sync_done = False
            if(nt_server_ip == nt_sim_ip):
                nt_server_ip = nt_robot_ip
            elif(nt_server_ip == nt_robot_ip):
                nt_server_ip = nt_sim_ip
            self.inst.setServer(nt_server_ip)
        self.master.after(UPDATE_PERIOD_MS, self.periodic_update)

    def sync_inputs_from_nt(self, device_data):
        print("Syncing UI with NetworkTables values...")
        # while self.robotTable.getNumber("SelectedFieldIndex", None) is None or self.robotTable.getNumber("SelectedLayoutIndex", None) is None:
        #     print("Waiting for Field/Layout keys to be published on NT server...")
        #     time.sleep(0.1)

        # field_index = int(self.robotTable.getNumber("SelectedFieldIndex", -1))
        # layout_index = int(self.robotTable.getNumber("SelectedLayoutIndex", -1))
        # Sync the enabled state from NT, defaulting to True if not present
        enabled_state = self.robotTable.getBoolean("Enabled", True)

        # self.field_var.set(str(field_index))
        # self.layout_var.set(str(layout_index))
        self.enabled_var.set(enabled_state)

        # print(f"Synced. Field: {field_index}, Layout: {layout_index}, Enabled: {enabled_state}")

    def update_tag_colors_from_nt(self, device_data):
        active_tag_id = device_data.active_tag
        for tag_id, tag_info in self.tag_data.items():
            tag_status = device_data.tag_status.get(tag_id, -1)
            is_saved = (tag_status == 1)  # 1 = tracked/saved
            is_active = (active_tag_id == tag_id)

            # Create filter state tuple: (is_saved, is_active)
            required_filter = (is_saved, is_active)

            if tag_info['current_filter'] != required_filter:
                self.update_tag_visual(tag_id, required_filter)
                tag_info['current_filter'] = required_filter

    def _apply_split_filter_to_image(self, img_path, tag_id, is_saved, is_active):
        """Apply a split-color filter: left half for saved status, right half for tracking status."""
        if not Image: return None
        try:
            with Image.open(img_path).convert("RGBA") as img:
                resized_img = img.resize(self.TAG_DISPLAY_SIZE, Image.Resampling.NEAREST)

                r, g, b, a = resized_img.split()
                l = resized_img.convert('L')
                grey_bleed = l.point(lambda i: int(i * self.DESATURATION_FACTOR))

                # Split the image in half
                width, height = resized_img.size
                mid_x = width // 2

                # Left half: green if saved, red if not saved
                if is_saved:
                    left_img = Image.merge('RGBA', (grey_bleed, g, grey_bleed, a))
                else:
                    left_img = Image.merge('RGBA', (r, grey_bleed, grey_bleed, a))

                # Right half: green if tracking, red if not tracking
                # For this implementation, we'll use the same is_saved for tracking
                # (You can modify this if tracking has a different status)
                if is_saved:  # tracking
                    right_img = Image.merge('RGBA', (grey_bleed, g, grey_bleed, a))
                else:  # not tracking
                    right_img = Image.merge('RGBA', (r, grey_bleed, grey_bleed, a))

                # Create the final combined image
                filtered_img = Image.new('RGBA', self.TAG_DISPLAY_SIZE)
                filtered_img.paste(left_img.crop((0, 0, mid_x, height)), (0, 0))
                filtered_img.paste(right_img.crop((mid_x, 0, width, height)), (mid_x, 0))

                self._draw_id_on_image(filtered_img, tag_id, is_active)
                return ImageTk.PhotoImage(filtered_img)
        except (FileNotFoundError, ValueError) as e:
            print(f"Warning: Could not process/filter image {img_path}: {e}")
            return None

    def update_tag_visual(self, tag_id, filter_state):
        if tag_id not in self.tag_data: return
        tag_info = self.tag_data[tag_id]
        
        is_saved, is_active = filter_state
        
        if filter_state in tag_info['filtered_photos']:
            photo_to_show = tag_info['filtered_photos'][filter_state]
        else:
            img_path = f"apriltags/{tag_id}.png"
            new_photo = self._apply_split_filter_to_image(img_path, tag_id, is_saved, is_active)
            if new_photo:
                tag_info['filtered_photos'][filter_state] = new_photo
                photo_to_show = new_photo
            else: return
        self.canvas.itemconfig(tag_info['canvas_id'], image=photo_to_show)

    def reset_tag_visual(self, tag_id):
        if tag_id in self.tag_data:
            tag_info = self.tag_data[tag_id]
            self.canvas.itemconfig(tag_info['canvas_id'], image=tag_info['original_photo'])

    def _generate_placeholder_tag_image(self, tag_id):
        if not Image: return
        if not os.path.exists("apriltags"): os.makedirs("apriltags")
        img_path = f"apriltags/{tag_id}.png"
        img = Image.new('RGB', self.TAG_DISPLAY_SIZE, color = 'darkgrey')
        self._draw_id_on_image(img, tag_id, is_active=False)
        img.save(img_path)

if __name__ == "__main__":
    if not os.path.exists("field.png"):
        if Image:
            field_img = Image.new('RGB', (800, 450), color='#004d00')
            ImageDraw.Draw(field_img).text((10, 10), "field.png (placeholder)", fill="white")
            field_img.save("field.png")
    root = tk.Tk()
    app = QuestNavManagerDashboard(root)
    root.mainloop()