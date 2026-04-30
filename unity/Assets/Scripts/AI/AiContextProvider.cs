using System;
using UnityEngine;

namespace CLABSIApp
{
    public class AiContextProvider : MonoBehaviour
    {
        public static AiContextProvider Instance { get; private set; }

        [SerializeField] private string defaultPatientId = "PAT-123";
        private string sessionId;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(this);
                return;
            }

            Instance = this;
            sessionId = Guid.NewGuid().ToString();
        }

        public AiContextPayload Build()
        {
            StepChecklistController checklist = FindAnyObjectByType<StepChecklistController>(FindObjectsInactive.Include);
            string currentScreen = ScreenManager.Instance != null ? ScreenManager.Instance.CurrentScreenName : "unknown";

            AiContextPayload context = new AiContextPayload
            {
                session_id = sessionId,
                patient_id = defaultPatientId,
                current_screen = currentScreen,
                current_step = -1,
                procedure_active = false,
                completed_step_ids = Array.Empty<int>(),
                missed_step_ids = Array.Empty<int>()
            };

            if (checklist != null && checklist.HasActiveProcedure)
            {
                context.current_step = checklist.CurrentStepIndex;
                context.procedure_active = true;
                context.procedure_id = checklist.CurrentProcedureId;
                context.procedure_name = checklist.CurrentProcedureName;
                context.current_step_id = checklist.CurrentStepId;
                context.current_step_title = checklist.CurrentStepTitle;
                context.total_steps = checklist.TotalSteps;
                context.completed_step_ids = checklist.CompletedStepIds;
                context.started_at = checklist.StartedAtIso;
            }

            return context;
        }
    }
}
