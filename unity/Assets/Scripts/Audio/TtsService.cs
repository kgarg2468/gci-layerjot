using System.Collections.Generic;
using UnityEngine;

namespace CLABSIApp
{
    public class TtsService : MonoBehaviour
    {
        public static TtsService Instance { get; private set; }

#if UNITY_ANDROID && !UNITY_EDITOR
        private AndroidJavaObject ttsObject;
        private bool isInitialized;
        private readonly Queue<string> pendingSpeech = new Queue<string>();
#endif

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(this);
                return;
            }
            Instance = this;

#if UNITY_ANDROID && !UNITY_EDITOR
            InitAndroid();
#endif
        }

        public void Speak(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            if (SettingsStore.IsMuted)
            {
                Debug.Log($"[TTS] Muted (skipped): {text}");
                return;
            }

#if UNITY_ANDROID && !UNITY_EDITOR
            if (!isInitialized)
            {
                pendingSpeech.Enqueue(text);
                return;
            }
            try
            {
                ttsObject.Call<int>("speak", text, 0, (AndroidJavaObject)null, "clabsi-step");
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[TTS] speak failed: {ex.Message}");
            }
#else
            Debug.Log($"[TTS] Speaking: {text}");
#endif
        }

        public void Stop()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            pendingSpeech.Clear();
            if (!isInitialized) return;
            try { ttsObject.Call<int>("stop"); }
            catch (System.Exception ex) { Debug.LogError($"[TTS] stop failed: {ex.Message}"); }
#endif
        }

#if UNITY_ANDROID && !UNITY_EDITOR
        private void InitAndroid()
        {
            try
            {
                AndroidJavaClass unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
                AndroidJavaObject context = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");
                ttsObject = new AndroidJavaObject("android.speech.tts.TextToSpeech", context, new TtsInitListener(this));
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[TTS] Android init failed: {ex.Message}");
            }
        }

        public void HandleInit(int status)
        {
            if (status != 0)
            {
                Debug.LogError($"[TTS] init returned non-success status {status}");
                return;
            }
            try
            {
                AndroidJavaClass localeClass = new AndroidJavaClass("java.util.Locale");
                AndroidJavaObject usLocale = localeClass.GetStatic<AndroidJavaObject>("US");
                ttsObject.Call<int>("setLanguage", usLocale);
                isInitialized = true;
                Debug.Log("[TTS] Android TTS initialized");
                while (pendingSpeech.Count > 0) Speak(pendingSpeech.Dequeue());
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[TTS] post-init configuration failed: {ex.Message}");
            }
        }

        private void OnDestroy()
        {
            if (ttsObject != null)
            {
                try
                {
                    ttsObject.Call<int>("stop");
                    ttsObject.Call("shutdown");
                    ttsObject.Dispose();
                }
                catch { }
                ttsObject = null;
            }
        }

        private class TtsInitListener : AndroidJavaProxy
        {
            private readonly TtsService owner;
            public TtsInitListener(TtsService o) : base("android.speech.tts.TextToSpeech$OnInitListener") { owner = o; }

            [UnityEngine.Scripting.Preserve]
            public void onInit(int status)
            {
                owner.HandleInit(status);
            }
        }
#endif
    }
}
