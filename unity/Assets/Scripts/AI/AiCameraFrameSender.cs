using System;
using UnityEngine;

namespace CLABSIApp
{
    public class AiCameraFrameSender : MonoBehaviour
    {
        [SerializeField] private bool consentGranted;

        private void Awake()
        {
            consentGranted = CameraConsentStore.IsGranted;
        }

        public void SetConsentGranted(bool granted)
        {
            consentGranted = granted;
            CameraConsentStore.SetGranted(granted);
        }

        public void SendTexture(Texture2D texture)
        {
            if (!consentGranted || texture == null) return;
            byte[] jpg = texture.EncodeToJPG(60);
            AiWebSocketClient.Instance?.SendCameraFrame(Convert.ToBase64String(jpg));
        }

        public void SendSimulatedBreach(string breachType)
        {
            if (!consentGranted) return;
            AiWebSocketClient.Instance?.SendCameraFrame(
                "simulated",
                new AiCameraFrameMetadata
                {
                    simulated_breach = true,
                    breach_type = string.IsNullOrWhiteSpace(breachType) ? "sterile_field_breach" : breachType,
                    confidence = 0.8f
                });
        }
    }
}
