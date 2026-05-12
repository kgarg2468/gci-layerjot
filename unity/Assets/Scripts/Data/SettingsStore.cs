using UnityEngine;

namespace CLABSIApp
{
    public static class SettingsStore
    {
        private const string MUTE_KEY = "clabsi_mute";
        private const string BACKEND_IP_KEY = "clabsi_backend_ip";
        private const int BACKEND_PORT = 8000;
        private const string BACKEND_PATH = "/ws";

        public static bool IsMuted
        {
            get => PlayerPrefs.GetInt(MUTE_KEY, 0) == 1;
            set
            {
                PlayerPrefs.SetInt(MUTE_KEY, value ? 1 : 0);
                PlayerPrefs.Save();
            }
        }

        public static string BackendIp
        {
            get => PlayerPrefs.GetString(BACKEND_IP_KEY, "");
            set
            {
                PlayerPrefs.SetString(BACKEND_IP_KEY, value ?? "");
                PlayerPrefs.Save();
            }
        }

        public static string BuildBackendUrl(string fallback)
        {
            string ip = BackendIp;
            if (string.IsNullOrWhiteSpace(ip)) return fallback;
            return $"ws://{ip.Trim()}:{BACKEND_PORT}{BACKEND_PATH}";
        }
    }
}
