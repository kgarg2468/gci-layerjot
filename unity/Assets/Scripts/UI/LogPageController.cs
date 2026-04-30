using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class LogPageController : MonoBehaviour
    {
        private Transform entriesContainer;
        private GameObject entryTemplate;
        private GameObject emptyState;
        private Button backButton;

        private void Awake()
        {
            entriesContainer = transform.Find("EntriesContainer");
            if (entriesContainer != null)
            {
                entryTemplate = entriesContainer.Find("EntryTemplate")?.gameObject;
                if (entryTemplate != null) entryTemplate.SetActive(false);
            }
            emptyState = transform.Find("EmptyState")?.gameObject;
            backButton = transform.Find("BackButton")?.GetComponent<Button>();
            if (backButton != null) backButton.onClick.AddListener(OnBack);
        }

        private void OnEnable()
        {
            Populate();
        }

        private void Populate()
        {
            if (entriesContainer == null) return;

            for (int i = entriesContainer.childCount - 1; i >= 0; i--)
            {
                Transform child = entriesContainer.GetChild(i);
                if (entryTemplate != null && child.gameObject == entryTemplate) continue;
                Destroy(child.gameObject);
            }

            IReadOnlyList<ProcedureLogEntry> entries = ProcedureLogStore.LoadAll();
            if (emptyState != null) emptyState.SetActive(entries.Count == 0);

            if (entryTemplate == null) return;

            for (int i = entries.Count - 1; i >= 0; i--)
            {
                ProcedureLogEntry e = entries[i];
                GameObject clone = Instantiate(entryTemplate, entriesContainer, false);
                clone.name = "LogEntry";
                clone.SetActive(true);
                Text t = clone.GetComponent<Text>();
                if (t != null) t.text = FormatEntry(e);
            }
        }

        private string FormatEntry(ProcedureLogEntry e)
        {
            string when;
            if (DateTime.TryParse(e.completedAtIso, out DateTime dt))
            {
                when = dt.ToLocalTime().ToString("MMM d, yyyy HH:mm");
            }
            else
            {
                when = e.completedAtIso;
            }
            int aiEventCount = e.aiEvents != null ? e.aiEvents.Length : 0;
            string score = e.complianceScore > 0 ? $"  ·  {e.complianceScore}% compliance" : string.Empty;
            string ai = aiEventCount > 0 ? $"  ·  {aiEventCount} AI events" : string.Empty;
            return $"{e.procedureName}\n{when}  ·  {e.stepsCompleted}/{e.totalSteps} steps{score}{ai}";
        }

        private void OnBack()
        {
            ScreenManager.Instance?.Show("HomeScreen");
        }
    }
}
