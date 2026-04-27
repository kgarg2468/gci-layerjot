using System;

namespace CLABSIApp
{
    [Serializable]
    public class StepData
    {
        public int id;
        public string title;
        public string instruction;
    }

    [Serializable]
    public class ProcedureData
    {
        public string id;
        public string name;
        public StepData[] steps;
    }
}
