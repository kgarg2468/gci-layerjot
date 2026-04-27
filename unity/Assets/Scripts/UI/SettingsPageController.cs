using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class SettingsPageController : MonoBehaviour
    {
        private Button muteButton;
        private Text muteButtonLabel;
        private Button backButton;

        private void Awake()
        {
            muteButton = transform.Find("ButtonsPanel/MuteButton")?.GetComponent<Button>();
            muteButtonLabel = transform.Find("ButtonsPanel/MuteButton/Label")?.GetComponent<Text>();
            backButton = transform.Find("ButtonsPanel/BackButton")?.GetComponent<Button>();

            if (muteButton != null) muteButton.onClick.AddListener(OnMuteToggled);
            if (backButton != null) backButton.onClick.AddListener(OnBack);
        }

        private void OnEnable()
        {
            UpdateMuteLabel();
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

        private void OnBack()
        {
            ScreenManager.Instance?.Show("HomeScreen");
        }
    }
}
