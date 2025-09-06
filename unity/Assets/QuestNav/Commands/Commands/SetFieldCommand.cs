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
    public class SetFieldCommand : ICommand
    {
        private readonly INetworkTableConnection networkTableConnection;
        private readonly Calibrator calibrator;

        public SetFieldCommand(
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
        public string commandNiceName => "SetField";

        /// <summary>
        /// Executes the pose reset command
        /// </summary>
        public void Execute(ProtobufQuestNavCommand receivedCommand)
        {
            QueuedLogger.Log("Received active tag set request, initiating reset...");

            // Read pose data from network tables
            int fieldId = receivedCommand.FieldIndexPayload.Value;
            calibrator.setActiveField(fieldId);

            
        }
    }
}
