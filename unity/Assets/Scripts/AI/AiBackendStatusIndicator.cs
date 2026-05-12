using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class AiBackendStatusIndicator : MonoBehaviour
    {
        [SerializeField] private Text statusText;

        private void Awake()
        {
            if (statusText == null) statusText = GetComponent<Text>();
        }

        private static readonly Color OnlineColor = new Color(0.30f, 0.85f, 0.30f, 1f);
        private static readonly Color OfflineColor = new Color(0.95f, 0.30f, 0.30f, 1f);

        private void Update()
        {
            if (statusText == null) return;
            bool connected = AiWebSocketClient.Instance != null && AiWebSocketClient.Instance.IsConnected;
            statusText.text = connected ? "AI online" : "AI offline";
            statusText.color = connected ? OnlineColor : OfflineColor;
        }
    }
}
