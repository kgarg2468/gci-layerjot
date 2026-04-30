using System;

namespace CLABSIApp
{
    [Serializable]
    public class ProcedureLogEntry
    {
        public string procedureId;
        public string procedureName;
        public string startedAtIso;
        public string completedAtIso;
        public int stepsCompleted;
        public int totalSteps;
        public int[] completedStepIds;
        public int[] missedStepIds;
        public int complianceScore;
        public string aiSummary;
        public AiEvent[] aiEvents;
    }
}
