using System;

namespace CLABSIApp
{
    [Serializable]
    public class ProcedureLogEntry
    {
        public string procedureId;
        public string procedureName;
        public string completedAtIso;
        public int stepsCompleted;
        public int totalSteps;
    }
}
