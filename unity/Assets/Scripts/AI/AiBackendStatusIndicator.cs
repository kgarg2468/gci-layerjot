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

        private void Update()
        {
            if (statusText == null) return;
            bool connected = AiWebSocketClient.Instance != null && AiWebSocketClient.Instance.IsConnected;
            statusText.text = connected ? "AI online" : "AI offline";
        }
    }
}
