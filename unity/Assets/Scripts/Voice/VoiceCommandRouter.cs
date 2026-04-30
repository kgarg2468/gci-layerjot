using UnityEngine;

namespace CLABSIApp
{
    public static class VoiceCommandRouter
    {
        public static VoiceCommand Parse(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return VoiceCommand.Unknown;
            string t = text.Trim().ToLowerInvariant();

            if (t.Contains("back") || t.Contains("return") || t.Contains("cancel")) return VoiceCommand.Back;
            if (t.Contains("log")) return VoiceCommand.Log;
            if (t.Contains("setting")) return VoiceCommand.Settings;
            if (t.Contains("insert")) return VoiceCommand.Insert;
            if (t.Contains("maintenance") || t.Contains("maintain")) return VoiceCommand.Maintenance;
            if (t.Contains("remove") || t.Contains("removal")) return VoiceCommand.Remove;
            if (t.Contains("procedure")) return VoiceCommand.Procedures;
            if (t.Contains("home")) return VoiceCommand.Home;
            if (t.Contains("done") || t.Contains("complete") || t.Contains("finish")) return VoiceCommand.Done;
            if (t.Contains("next") || t.Contains("forward") || t.Contains("continue")) return VoiceCommand.Next;
            return VoiceCommand.Unknown;
        }

        public static void Dispatch(VoiceCommand cmd)
        {
            Debug.Log($"[Voice] Command: {cmd}");
            switch (cmd)
            {
                case VoiceCommand.Next:
                case VoiceCommand.Done:
                    {
                        StepChecklistController c = Object.FindAnyObjectByType<StepChecklistController>(FindObjectsInactive.Exclude);
                        if (c != null && c.gameObject.activeInHierarchy) c.Advance();
                        else Debug.Log("[Voice] No active StepChecklist — command ignored");
                    }
                    break;
                case VoiceCommand.Home:
                    ScreenManager.Instance?.Show("HomeScreen");
                    break;
                case VoiceCommand.Procedures:
                    ScreenManager.Instance?.Show("ProceduresPage");
                    break;
                case VoiceCommand.Log:
                    ScreenManager.Instance?.Show("LogPage");
                    break;
                case VoiceCommand.Settings:
                    ScreenManager.Instance?.Show("SettingsPage");
                    break;
                case VoiceCommand.Insert:
                    StartProcedure("insert");
                    break;
                case VoiceCommand.Maintenance:
                    StartProcedure("maintenance");
                    break;
                case VoiceCommand.Remove:
                    StartProcedure("remove");
                    break;
                case VoiceCommand.Back:
                    {
                        StepChecklistController active = Object.FindAnyObjectByType<StepChecklistController>(FindObjectsInactive.Exclude);
                        if (active != null && active.gameObject.activeInHierarchy)
                            ScreenManager.Instance?.Show("ProceduresPage");
                        else
                            ScreenManager.Instance?.Show("HomeScreen");
                    }
                    break;
                case VoiceCommand.Unknown:
                    Debug.Log("[Voice] Unknown command — ignored");
                    break;
            }
        }

        private static void StartProcedure(string procedureId)
        {
            ProcedureData data = ProcedureLoader.Load(procedureId);
            if (data == null) return;
            StepChecklistController ctrl = Object.FindAnyObjectByType<StepChecklistController>(FindObjectsInactive.Include);
            if (ctrl == null)
            {
                Debug.LogError("[Voice] No StepChecklistController in scene");
                return;
            }
            ctrl.Begin(data);
        }
    }
}
