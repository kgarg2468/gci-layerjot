using UnityEngine;

namespace CLABSIApp
{
    public static class CameraConsentStore
    {
        private const string Key = "camera_consent_granted";

        public static bool IsGranted => PlayerPrefs.GetInt(Key, 0) == 1;

        public static void SetGranted(bool granted)
        {
            PlayerPrefs.SetInt(Key, granted ? 1 : 0);
            PlayerPrefs.Save();
        }
    }
}
