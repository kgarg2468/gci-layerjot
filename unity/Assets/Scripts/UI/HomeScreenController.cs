using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class HomeScreenController : MonoBehaviour
    {
        private void Start()
        {
            Wire("ProceduresButton", OnProceduresClicked);
            Wire("LogButton", OnLogClicked);
            Wire("SettingsButton", OnSettingsClicked);
            Wire("ExitButton", OnExitClicked);
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
                Debug.LogError($"[HomeScreen] missing button '{buttonName}' under {name}");
                return;
            }
            found.onClick.AddListener(action);
        }

        public void OnProceduresClicked()
        {
            Debug.Log("[HomeScreen] Procedures clicked");
            ScreenManager.Instance?.Show("ProceduresPage");
        }

        public void OnLogClicked()
        {
            Debug.Log("[HomeScreen] Log clicked");
            ScreenManager.Instance?.Show("LogPage");
        }

        public void OnSettingsClicked()
        {
            Debug.Log("[HomeScreen] Settings clicked");
            ScreenManager.Instance?.Show("SettingsPage");
        }

        public void OnExitClicked()
        {
            Debug.Log("[HomeScreen] Exit clicked");
            Application.Quit();
        }
    }
}
