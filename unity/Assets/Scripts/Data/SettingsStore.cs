using UnityEngine;

namespace CLABSIApp
{
    public static class SettingsStore
    {
        private const string MUTE_KEY = "clabsi_mute";

        public static bool IsMuted
        {
            get => PlayerPrefs.GetInt(MUTE_KEY, 0) == 1;
            set
            {
                PlayerPrefs.SetInt(MUTE_KEY, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }
    }
}
