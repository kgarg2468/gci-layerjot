using UnityEngine;

namespace CLABSIApp
{
    public static class ProcedureLoader
    {
        public static ProcedureData Load(string procedureId)
        {
            TextAsset json = Resources.Load<TextAsset>($"Checklists/{procedureId}");
            if (json == null)
            {
                Debug.LogError($"ProcedureLoader: could not find Checklists/{procedureId}");
                return null;
            }
            return JsonUtility.FromJson<ProcedureData>(json.text);
        }
    }
}
