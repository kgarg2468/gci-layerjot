using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class ProceduresPageController : MonoBehaviour
    {
        private void Start()
        {
            Wire("InsertButton", () => OnProcedureSelected("insert"));
            Wire("MaintenanceButton", () => OnProcedureSelected("maintenance"));
            Wire("RemoveButton", () => OnProcedureSelected("remove"));
            Wire("BackButton", OnBackClicked);
        }

        private void Wire(string buttonName, UnityAction action)
        {
            Button found = null;
            foreach (Button b in GetComponentsInChildren<Button>(true))
            {
                if (b.gameObject.name == buttonName) { found = b; break; }
            }
            if (found == null)
            {
                Debug.LogError($"[ProceduresPage] missing button '{buttonName}' under {name}");
                return;
            }
            found.onClick.AddListener(action);
        }

        private void OnProcedureSelected(string procedureId)
        {
            Debug.Log($"[ProceduresPage] Selected procedure: {procedureId}");
            ProcedureData data = ProcedureLoader.Load(procedureId);
            if (data == null) return;

            StepChecklistController checklist = FindAnyObjectByType<StepChecklistController>(FindObjectsInactive.Include);
            if (checklist == null)
            {
                Debug.LogError("[ProceduresPage] No StepChecklistController in scene");
                return;
            }
            checklist.Begin(data);
        }

        private void OnBackClicked()
        {
            Debug.Log("[ProceduresPage] Back clicked");
            ScreenManager.Instance?.Show("HomeScreen");
        }
    }
}
