using UnityEngine;

namespace CLABSIApp
{
    public class AiActionExecutor : MonoBehaviour
    {
        public static AiActionExecutor Instance { get; private set; }

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(this);
                return;
            }

            Instance = this;
        }

        public void Execute(AiResponseEnvelope response)
        {
            if (response == null) return;

            string action = response.action_cmd;
            AiActionParameters parameters = response.parameters ?? new AiActionParameters();
            string spoken = !string.IsNullOrWhiteSpace(response.spoken_response)
                ? response.spoken_response
                : response.payload != null ? response.payload.spoken_response : string.Empty;

            RecordEvent(action, parameters, spoken);

            switch (action)
            {
                case "next_step":
                    ActiveChecklist()?.Advance();
                    break;
                case "prev_step":
                    ActiveChecklist()?.MovePrevious();
                    break;
                case "navigate_home":
                    ScreenManager.Instance?.Show("HomeScreen");
                    break;
                case "show_alert":
                case "flag_breach":
                    ShowAlert(parameters, spoken, action);
                    break;
                case "end_procedure":
                    ActiveChecklist()?.ApplyAiSummary(parameters, spoken);
                    ProcedureLogStore.ApplyLatestAiSummary(parameters, spoken);
                    ShowAlert(parameters, spoken, "summary");
                    break;
                case "read_step":
                default:
                    if (!string.IsNullOrWhiteSpace(spoken)) TtsService.Instance?.Speak(spoken);
                    break;
            }
        }

        private StepChecklistController ActiveChecklist()
        {
            StepChecklistController checklist = FindAnyObjectByType<StepChecklistController>(FindObjectsInactive.Exclude);
            return checklist != null && checklist.HasActiveProcedure ? checklist : null;
        }

        private void ShowAlert(AiActionParameters parameters, string spoken, string action)
        {
            string message = !string.IsNullOrWhiteSpace(parameters.message) ? parameters.message : spoken;
            string severity = !string.IsNullOrWhiteSpace(parameters.severity) ? parameters.severity : action;
            AiAlertOverlay.Instance?.Show(message, severity);
            if (!string.IsNullOrWhiteSpace(spoken)) TtsService.Instance?.Speak(spoken);
        }

        private void RecordEvent(string action, AiActionParameters parameters, string spoken)
        {
            if (string.IsNullOrWhiteSpace(action)) return;

            ProcedureLogStore.RecordAiEvent(new AiEvent
            {
                timestampIso = System.DateTime.UtcNow.ToString("o"),
                eventType = action == "flag_breach" ? "breach" : "ai",
                actionCmd = action,
                severity = parameters != null ? parameters.severity : null,
                message = parameters != null && !string.IsNullOrWhiteSpace(parameters.message) ? parameters.message : spoken,
                procedureId = parameters != null ? parameters.procedure_id : null,
                stepId = parameters != null ? parameters.current_step_id : -1,
                confidence = parameters != null ? parameters.confidence : 0f
            });
        }
    }
}
