using UnityEngine;

namespace CLABSIApp
{
    public class ScreenManager : MonoBehaviour
    {
        public static ScreenManager Instance { get; private set; }
        public string CurrentScreenName { get; private set; } = "unknown";

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(this);
                return;
            }
            Instance = this;
        }

        public void Show(string screenName)
        {
            Transform target = transform.Find(screenName);
            if (target == null)
            {
                Debug.LogWarning($"[ScreenManager] No child screen named '{screenName}'");
                return;
            }
            foreach (Transform child in transform)
            {
                if (IsPersistent(child)) continue;
                child.gameObject.SetActive(child == target);
            }
            CurrentScreenName = screenName;
        }

        private static bool IsPersistent(Transform child)
        {
            string n = child.name;
            return n.StartsWith("Ai") || n == "AlertOverlay";
        }
    }
}
