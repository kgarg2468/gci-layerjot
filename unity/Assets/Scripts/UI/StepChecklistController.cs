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
            ScreenManager.Instance?.Show("StepChecklistScreen");
            Render();
        }

        public void Advance() => OnNext();

        private void OnNext()
        {
            if (currentProcedure == null) return;
            if (currentStepIndex >= currentProcedure.steps.Length - 1)
            {
                Debug.Log($"[StepChecklist] Procedure complete: {currentProcedure.id}");
                ProcedureLogStore.Add(new ProcedureLogEntry
                {
                    procedureId = currentProcedure.id,
                    procedureName = currentProcedure.name,
                    completedAtIso = DateTime.UtcNow.ToString("o"),
                    stepsCompleted = currentProcedure.steps.Length,
                    totalSteps = currentProcedure.steps.Length
                });
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
    }
}
