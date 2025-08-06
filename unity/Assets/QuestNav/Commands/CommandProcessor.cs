using QuestNav.Commands.Commands;
using QuestNav.Protos.Generated;
using QuestNav.Utils;
using UnityEngine;

namespace QuestNav.Commands
{
    /// <summary>
    /// Interface for command processing.
    /// </summary>
    public interface ICommandProcessor
    {
        /// <summary>
        /// Processes commands received from the robot.
        /// </summary>
        void ProcessCommands();
    }

    public class CommandProcessor : ICommandProcessor
    {
        // Command context
        private NetworkTableConnection networkTableConnection;

        // Commands
        private PoseResetCommand poseResetCommand;
        private SetActiveTagCommand setActiveTagCommand;
        private CalibrateTagCommand calibrateTagCommand;
        private DeleteTagCommand deleteTagCommand;

        // Processed command variable
        private uint lastCommandIdProcessed;

        public CommandProcessor(
            NetworkTableConnection networkTableConnection,
            Transform vrCamera,
            Transform vrCameraRoot,
            Transform resetTransform,
            Calibrator calibrator
        )
        {
            // Command context
            this.networkTableConnection = networkTableConnection;

            // Commands
            poseResetCommand = new PoseResetCommand(
                networkTableConnection,
                vrCamera,
                vrCameraRoot,
                resetTransform
            );
            setActiveTagCommand = new SetActiveTagCommand(networkTableConnection, calibrator);
            calibrateTagCommand = new CalibrateTagCommand(networkTableConnection, calibrator);
            deleteTagCommand = new DeleteTagCommand(networkTableConnection, calibrator);
        }

        public void ProcessCommands()
        {
            ProtobufQuestNavCommand receivedCommand = networkTableConnection.GetCommandRequest();
            if (receivedCommand.CommandId != lastCommandIdProcessed)
            {
                switch (receivedCommand.Type)
                {
                    case QuestNavCommandType.CommandTypeUnspecified:
                        break;
                    case QuestNavCommandType.PoseReset:
                        QueuedLogger.Log("Executing Pose Reset Command");
                        poseResetCommand.Execute(receivedCommand);
                        break;
                    case QuestNavCommandType.SetActiveTag:
                        QueuedLogger.Log("Executing Set Active Tag Command");
                        setActiveTagCommand.Execute(receivedCommand);
                        break;
                    case QuestNavCommandType.CalibrateTag:
                        QueuedLogger.Log("Executing Calibrate Tag Command");
                        calibrateTagCommand.Execute(receivedCommand);
                        break;
                    case QuestNavCommandType.DeleteTag:
                        QueuedLogger.Log("Executing Delete Tag Command");
                        deleteTagCommand.Execute(receivedCommand);
                        break;
                    default:
                        QueuedLogger.Log(
                            "Execute called with unknown command type: " + receivedCommand.Type,
                            QueuedLogger.LogLevel.Warning
                        );
                        break;
                }
            }
            // Don't double process
            lastCommandIdProcessed = networkTableConnection.GetCommandRequest().CommandId;
        }
    }
}
