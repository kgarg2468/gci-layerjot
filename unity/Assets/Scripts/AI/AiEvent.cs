using System;

namespace CLABSIApp
{
    [Serializable]
    public class AiEvent
    {
        public string timestampIso;
        public string eventType;
        public string actionCmd;
        public string severity;
        public string message;
        public string procedureId;
        public int stepId;
        public float confidence;
    }
}
