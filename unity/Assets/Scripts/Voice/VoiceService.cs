using UnityEngine;
using UnityEngine.InputSystem;
#if UNITY_ANDROID && !UNITY_EDITOR
using UnityEngine.Android;
#endif

namespace CLABSIApp
{
    public class VoiceService : MonoBehaviour
    {
        public static VoiceService Instance { get; private set; }

#if UNITY_ANDROID && !UNITY_EDITOR
        private AndroidJavaObject recognizer;
        private AndroidJavaObject mainActivity;
        private bool isListening;
        private volatile string pendingResult;
        private volatile int pendingErrorCode = int.MinValue;
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
            try
            {
                AndroidJavaClass unityPlayer = new AndroidJavaClass("com.unity3d.player.UnityPlayer");
                mainActivity = unityPlayer.GetStatic<AndroidJavaObject>("currentActivity");
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[Voice] Failed to grab Android activity: {ex.Message}");
            }
#endif
        }

        private void Update()
        {
#if UNITY_EDITOR
            if (Keyboard.current == null) return;
            if (Keyboard.current.nKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Next);
            if (Keyboard.current.dKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Done);
            if (Keyboard.current.hKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Home);
            if (Keyboard.current.pKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Procedures);
            if (Keyboard.current.lKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Log);
            if (Keyboard.current.sKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Settings);
            if (Keyboard.current.iKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Insert);
            if (Keyboard.current.mKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Maintenance);
            if (Keyboard.current.rKey.wasPressedThisFrame) VoiceCommandRouter.Dispatch(VoiceCommand.Remove);
#endif

#if UNITY_ANDROID && !UNITY_EDITOR
            if (pendingResult != null)
            {
                string heard = pendingResult;
                pendingResult = null;
                Debug.Log($"[Voice] Heard: '{heard}'");
                VoiceCommandRouter.Dispatch(VoiceCommandRouter.Parse(heard));
            }
            if (pendingErrorCode != int.MinValue)
            {
                int code = pendingErrorCode;
                pendingErrorCode = int.MinValue;
                Debug.LogWarning($"[Voice] Recognition error code {code}");
            }
#endif
        }

        public void StartListening()
        {
#if UNITY_ANDROID && !UNITY_EDITOR
            EnsurePermissionThenListen();
#else
            Debug.Log("[Voice] StartListening (Editor stub — use keyboard: N=Next, D=Done, H=Home, P=Procedures)");
#endif
        }

#if UNITY_ANDROID && !UNITY_EDITOR
        private void EnsurePermissionThenListen()
        {
            if (!Permission.HasUserAuthorizedPermission(Permission.Microphone))
            {
                PermissionCallbacks callbacks = new PermissionCallbacks();
                callbacks.PermissionGranted += _ => Listen();
                callbacks.PermissionDenied += _ => Debug.LogWarning("[Voice] Microphone permission denied");
                Permission.RequestUserPermission(Permission.Microphone, callbacks);
                return;
            }
            Listen();
        }

        private void Listen()
        {
            if (isListening) return;
            try
            {
                if (recognizer == null)
                {
                    AndroidJavaClass srClass = new AndroidJavaClass("android.speech.SpeechRecognizer");
                    recognizer = srClass.CallStatic<AndroidJavaObject>("createSpeechRecognizer", mainActivity);
                    recognizer.Call("setRecognitionListener", new RecognitionListenerProxy(this));
                }

                AndroidJavaObject intent = new AndroidJavaObject("android.content.Intent", "android.speech.action.RECOGNIZE_SPEECH");
                intent.Call<AndroidJavaObject>("putExtra", "android.speech.extra.LANGUAGE_MODEL", "free_form");
                intent.Call<AndroidJavaObject>("putExtra", "android.speech.extra.MAX_RESULTS", 1);

                isListening = true;
                recognizer.Call("startListening", intent);
                Debug.Log("[Voice] Listening...");
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"[Voice] Listen failed: {ex.Message}");
                isListening = false;
            }
        }

        private void OnDestroy()
        {
            if (recognizer != null)
            {
                try { recognizer.Call("destroy"); recognizer.Dispose(); } catch { }
                recognizer = null;
            }
        }

        private class RecognitionListenerProxy : AndroidJavaProxy
        {
            private readonly VoiceService owner;
            public RecognitionListenerProxy(VoiceService o) : base("android.speech.RecognitionListener") { owner = o; }

            [UnityEngine.Scripting.Preserve] public void onReadyForSpeech(AndroidJavaObject p) { }
            [UnityEngine.Scripting.Preserve] public void onBeginningOfSpeech() { }
            [UnityEngine.Scripting.Preserve] public void onRmsChanged(float r) { }
            [UnityEngine.Scripting.Preserve] public void onBufferReceived(AndroidJavaObject b) { }
            [UnityEngine.Scripting.Preserve] public void onEndOfSpeech() { }
            [UnityEngine.Scripting.Preserve] public void onError(int e) { owner.isListening = false; owner.pendingErrorCode = e; }
            [UnityEngine.Scripting.Preserve] public void onPartialResults(AndroidJavaObject p) { }
            [UnityEngine.Scripting.Preserve] public void onEvent(int e, AndroidJavaObject p) { }

            [UnityEngine.Scripting.Preserve]
            public void onResults(AndroidJavaObject results)
            {
                owner.isListening = false;
                try
                {
                    AndroidJavaObject list = results.Call<AndroidJavaObject>("getStringArrayList", "results_recognition");
                    if (list == null) return;
                    int count = list.Call<int>("size");
                    if (count == 0) return;
                    owner.pendingResult = list.Call<string>("get", 0);
                }
                catch (System.Exception ex)
                {
                    Debug.LogError($"[Voice] onResults parse failed: {ex.Message}");
                }
            }
        }
#endif
    }
}
