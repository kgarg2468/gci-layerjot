using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class AiAlertOverlay : MonoBehaviour
    {
        public static AiAlertOverlay Instance { get; private set; }

        [SerializeField] private Text messageText;
        [SerializeField] private CanvasGroup canvasGroup;
        [SerializeField] private float visibleSeconds = 5f;

        private float hideAt;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(this);
                return;
            }

            Instance = this;
            if (canvasGroup == null) canvasGroup = GetComponent<CanvasGroup>();
            Hide();
        }

        private void Update()
        {
            if (canvasGroup != null && canvasGroup.alpha > 0f && Time.unscaledTime >= hideAt)
            {
                Hide();
            }
        }

        public void Show(string message, string severity)
        {
            if (messageText != null) messageText.text = message;
            if (canvasGroup != null)
            {
                canvasGroup.alpha = 1f;
                canvasGroup.blocksRaycasts = true;
                canvasGroup.interactable = true;
            }

            hideAt = Time.unscaledTime + visibleSeconds;
            Debug.Log($"[AI Alert:{severity}] {message}");
        }

        private void Hide()
        {
            if (canvasGroup == null) return;
            canvasGroup.alpha = 0f;
            canvasGroup.blocksRaycasts = false;
            canvasGroup.interactable = false;
        }
    }
}
