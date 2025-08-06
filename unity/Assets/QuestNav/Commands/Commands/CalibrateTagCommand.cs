using QuestNav.Core;
using QuestNav.Network;
using QuestNav.Protos.Generated;
using QuestNav.Utils;
using UnityEngine;
using Wpi.Proto;

namespace QuestNav.Commands.Commands
{
    /// <summary>
    /// Resets the VR camera pose to a specified position
    /// </summary>
    public class CalibrateTagCommand : ICommand
    {
        private readonly INetworkTableConnection networkTableConnection;
        private readonly Calibrator calibrator;

        public CalibrateTagCommand(
            INetworkTableConnection networkTableConnection,
            Calibrator calibrator
        )
        {
            this.networkTableConnection = networkTableConnection;
            this.calibrator = calibrator;
        }

        /// <summary>
        /// The formatted name for PoseResetCommand
        /// </summary>
        public string commandNiceName => "CalibrateTag";

        /// <summary>
        /// Executes the pose reset command
        /// </summary>
        public void Execute(ProtobufQuestNavCommand receivedCommand)
        {
            QueuedLogger.Log("Received active tag set request, initiating reset...");

            // Read pose data from network tables
            double xWorld = receivedCommand.CalibrationPayload.HeadsetPose.Translation.X;
            double yWorld = receivedCommand.CalibrationPayload.HeadsetPose.Translation.Y;
            double yawDeg = receivedCommand.CalibrationPayload.HeadsetPose.Rotation.Value;

            //Pose pose = Conversions.FrcPoseToUnity(new Vector3((float)xWorld, (float)yWorld, 0f), Quaternion.Euler(0f, 0f, (float)yawDeg));
            Pose pose = new Pose(
                new Vector3((float)xWorld, (float)yWorld, 0f),
                Quaternion.Euler(0f, 0f, (float)yawDeg)
            );
            QueuedLogger.Log($"Received calibration data: ({xWorld}, {yWorld}, {yawDeg})");

            calibrator.AnchorTagFromHeadset2DAsync(pose);
        }
    }
}
