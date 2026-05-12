using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class SettingsPageController : MonoBehaviour
    {
        private Button muteButton;
        private Text muteButtonLabel;
        private Button backButton;
        private Button ipButton;
        private Text ipButtonLabel;
        private TouchScreenKeyboard activeKeyboard;

        private void Awake()
        {
            muteButton = transform.Find("ButtonsPanel/MuteButton")?.GetComponent<Button>();
            muteButtonLabel = transform.Find("ButtonsPanel/MuteButton/Label")?.GetComponent<Text>();
            backButton = transform.Find("ButtonsPanel/BackButton")?.GetComponent<Button>();
            ipButton = transform.Find("ButtonsPanel/IpButton")?.GetComponent<Button>();
            ipButtonLabel = transform.Find("ButtonsPanel/IpButton/Label")?.GetComponent<Text>();

            if (muteButton != null) muteButton.onClick.AddListener(OnMuteToggled);
            if (backButton != null) backButton.onClick.AddListener(OnBack);
            if (ipButton != null) ipButton.onClick.AddListener(OnIpTapped);
        }

        private void OnEnable()
        {
            UpdateMuteLabel();
            UpdateIpLabel();
        }

        private void Update()
        {
            if (activeKeyboard == null) return;

            if (activeKeyboard.status == TouchScreenKeyboard.Status.Done)
            {
                string newIp = (activeKeyboard.text ?? "").Trim();
                activeKeyboard = null;
                if (!string.IsNullOrEmpty(newIp))
                {
                    SettingsStore.BackendIp = newIp;
                    Debug.Log($"[Settings] Backend IP set to '{newIp}', reconnecting...");
                    UpdateIpLabel();
                    AiWebSocketClient.Instance?.Reconnect();
                }
            }
            else if (activeKeyboard.status == TouchScreenKeyboard.Status.Canceled
                  || activeKeyboard.status == TouchScreenKeyboard.Status.LostFocus)
            {
                activeKeyboard = null;
            }
        }

        private void OnMuteToggled()
        {
            SettingsStore.IsMuted = !SettingsStore.IsMuted;
            Debug.Log($"[Settings] Mute set to {SettingsStore.IsMuted}");
            UpdateMuteLabel();
        }

        private void UpdateMuteLabel()
        {
            if (muteButtonLabel != null)
            {
                muteButtonLabel.text = SettingsStore.IsMuted ? "Audio: Muted" : "Audio: On";
            }
        }

        private void OnIpTapped()
        {
            activeKeyboard = TouchScreenKeyboard.Open(
                SettingsStore.BackendIp,
                TouchScreenKeyboardType.URL,
                false, false, false, false,
                "Backend IP (e.g. 192.168.0.104)");
        }

        private void UpdateIpLabel()
        {
            if (ipButtonLabel == null) return;
            string ip = SettingsStore.BackendIp;
            ipButtonLabel.text = string.IsNullOrEmpty(ip) ? "Set Backend IP" : $"IP: {ip}";
        }

        private void OnBack()
        {
            ScreenManager.Instance?.Show("HomeScreen");
        }
    }
}
