using UnityEngine;

namespace CLABSIApp
{
    public class ScreenManager : MonoBehaviour
    {
        public static ScreenManager Instance { get; private set; }

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
                child.gameObject.SetActive(child == target);
            }
        }
    }
}
