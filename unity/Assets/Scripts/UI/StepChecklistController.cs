using System;
using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class StepChecklistController : MonoBehaviour
    {
        private Text titleText;
        private Text progressText;
        private Text stepTitleText;
        private Text stepInstructionText;
        private Button nextButton;
        private Button backButton;
        private Text nextButtonLabel;

        private ProcedureData currentProcedure;
        private int currentStepIndex;
        private string startedAtIso;
        private string pendingAiSummary;
        private int pendingComplianceScore;
        private int[] pendingMissedStepIds = Array.Empty<int>();

        public bool HasActiveProcedure => currentProcedure != null;
        public string CurrentProcedureId => currentProcedure != null ? currentProcedure.id : null;
        public string CurrentProcedureName => currentProcedure != null ? currentProcedure.name : null;
        public int CurrentStepIndex => currentProcedure != null ? currentStepIndex : -1;
        public int TotalSteps => currentProcedure != null && currentProcedure.steps != null ? currentProcedure.steps.Length : 0;
        public string StartedAtIso => startedAtIso;
        public int CurrentStepId
        {
            get
            {
                StepData step = CurrentStep();
                return step != null ? step.id : -1;
            }
        }
        public string CurrentStepTitle
        {
            get
            {
                StepData step = CurrentStep();
                return step != null ? step.title : null;
            }
        }
        public int[] CompletedStepIds
        {
            get
            {
                if (currentProcedure == null || currentProcedure.steps == null) return Array.Empty<int>();
                int count = Mathf.Clamp(currentStepIndex, 0, currentProcedure.steps.Length);
                int[] completed = new int[count];
                for (int i = 0; i < count; i++) completed[i] = currentProcedure.steps[i].id;
                return completed;
            }
        }

        private void Awake()
        {
            titleText = transform.Find("Title")?.GetComponent<Text>();
            progressText = transform.Find("ProgressIndicator")?.GetComponent<Text>();
            stepTitleText = transform.Find("StepCard/StepTitle")?.GetComponent<Text>();
            stepInstructionText = transform.Find("StepCard/StepInstruction")?.GetComponent<Text>();
            nextButton = transform.Find("BottomBar/NextButton")?.GetComponent<Button>();
            backButton = transform.Find("BottomBar/BackButton")?.GetComponent<Button>();
            nextButtonLabel = transform.Find("BottomBar/NextButton/Label")?.GetComponent<Text>();

            if (nextButton != null) nextButton.onClick.AddListener(OnNext);
            if (backButton != null) backButton.onClick.AddListener(OnBack);
        }

        public void Begin(ProcedureData data)
        {
            if (data == null || data.steps == null || data.steps.Length == 0)
            {
                Debug.LogError("[StepChecklist] Begin called with empty procedure");
                return;
            }
            currentProcedure = data;
            currentStepIndex = 0;
            startedAtIso = DateTime.UtcNow.ToString("o");
            pendingAiSummary = null;
            pendingComplianceScore = 0;
            pendingMissedStepIds = Array.Empty<int>();
            ScreenManager.Instance?.Show("StepChecklistScreen");
            Render();
        }

        public void Advance() => OnNext();

        public void MovePrevious()
        {
            if (currentProcedure == null || currentStepIndex <= 0) return;
            currentStepIndex--;
            Render();
        }

        public void ReadCurrentStep()
        {
            StepData step = CurrentStep();
            if (step == null) return;
            TtsService.Instance?.Speak($"{step.title}. {step.instruction}");
        }

        public void ApplyAiSummary(AiActionParameters parameters, string spokenSummary)
        {
            pendingAiSummary = spokenSummary;
            if (parameters == null) return;
            pendingComplianceScore = parameters.compliance_score;
            pendingMissedStepIds = parameters.missed_step_ids ?? Array.Empty<int>();
        }

        private void OnNext()
        {
            if (currentProcedure == null) return;
            if (currentStepIndex >= currentProcedure.steps.Length - 1)
            {
                Debug.Log($"[StepChecklist] Procedure complete: {currentProcedure.id}");
                ProcedureLogEntry entry = new ProcedureLogEntry
                {
                    procedureId = currentProcedure.id,
                    procedureName = currentProcedure.name,
                    startedAtIso = startedAtIso,
                    completedAtIso = DateTime.UtcNow.ToString("o"),
                    stepsCompleted = currentProcedure.steps.Length,
                    totalSteps = currentProcedure.steps.Length,
                    completedStepIds = AllStepIds(),
                    missedStepIds = pendingMissedStepIds,
                    complianceScore = pendingComplianceScore,
                    aiSummary = pendingAiSummary,
                    aiEvents = ProcedureLogStore.DrainPendingAiEvents()
                };
                ProcedureLogStore.Add(entry);
                AiWebSocketClient.Instance?.SendProcedureComplete(entry);
                TtsService.Instance?.Stop();
                currentProcedure = null;
                ScreenManager.Instance?.Show("ProceduresPage");
                return;
            }
            currentStepIndex++;
            Render();
        }

        private void OnBack()
        {
            Debug.Log("[StepChecklist] Back");
            TtsService.Instance?.Stop();
            currentProcedure = null;
            ScreenManager.Instance?.Show("ProceduresPage");
        }

        private void Render()
        {
            if (currentProcedure == null) return;
            int total = currentProcedure.steps.Length;
            bool isLast = currentStepIndex >= total - 1;
            StepData step = currentProcedure.steps[currentStepIndex];

            if (titleText != null) titleText.text = currentProcedure.name;
            if (progressText != null) progressText.text = $"Step {currentStepIndex + 1} of {total}";
            if (stepTitleText != null) stepTitleText.text = step.title;
            if (stepInstructionText != null) stepInstructionText.text = step.instruction;
            if (nextButtonLabel != null) nextButtonLabel.text = isLast ? "Done" : "Next";

            TtsService.Instance?.Speak($"{step.title}. {step.instruction}");
        }

        private StepData CurrentStep()
        {
            if (currentProcedure == null || currentProcedure.steps == null) return null;
            if (currentStepIndex < 0 || currentStepIndex >= currentProcedure.steps.Length) return null;
            return currentProcedure.steps[currentStepIndex];
        }

        private int[] AllStepIds()
        {
            if (currentProcedure == null || currentProcedure.steps == null) return Array.Empty<int>();
            int[] ids = new int[currentProcedure.steps.Length];
            for (int i = 0; i < currentProcedure.steps.Length; i++) ids[i] = currentProcedure.steps[i].id;
            return ids;
        }
    }
}
