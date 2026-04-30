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

        public bool IsListening
        {
            get
            {
#if UNITY_ANDROID && !UNITY_EDITOR
                return isListening;
#else
                return true;
#endif
            }
        }

        // Phase 2 stub for hands-free operation: auto-restart listening so the user
        // doesn't need to tap a Mic button to issue commands. Phase 4 will replace
        // this with proper Porcupine wake-word gating.
#pragma warning disable CS0414
        [SerializeField] private bool continuousListening = true;
        [SerializeField] private float restartDelaySeconds = 0.4f;
#pragma warning restore CS0414

#if UNITY_ANDROID && !UNITY_EDITOR
        private AndroidJavaObject recognizer;
        private AndroidJavaObject mainActivity;
        private AndroidJavaObject audioManager;
        private bool isListening;
        private volatile string pendingResult;
        private volatile int pendingErrorCode = int.MinValue;
        private volatile bool pendingRestart;
        private int originalNotificationVolume = -1;
        private int originalSystemVolume = -1;

        // android.media.AudioManager stream constants
        private const int STREAM_SYSTEM = 1;
        private const int STREAM_NOTIFICATION = 5;
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

            if (continuousListening) MuteRecognizerBeeps();
#endif
        }

#if UNITY_ANDROID && !UNITY_EDITOR
        private void MuteRecognizerBeeps()
        {
            if (mainActivity == null) return;
            try
            {
                AndroidJavaObject ctx = mainActivity.Call<AndroidJavaObject>("getApplicationContext");
                audioManager = ctx.Call<AndroidJavaObject>("getSystemService", "audio");
                if (audioManager == null) return;

                originalNotificationVolume = audioManager.Call<int>("getStreamVolume", STREAM_NOTIFICATION);
                originalSystemVolume = audioManager.Call<int>("getStreamVolume", STREAM_SYSTEM);
                audioManager.Call("setStreamVolume", STREAM_NOTIFICATION, 0, 0);
                audioManager.Call("setStreamVolume", STREAM_SYSTEM, 0, 0);
                Debug.Log("[Voice] Muted notification + system streams to suppress recognizer beeps");
            }
            catch (System.Exception ex)
            {
                Debug.LogWarning($"[Voice] Could not mute beep streams: {ex.Message}");
            }
        }

        private void RestoreRecognizerBeeps()
        {
            if (audioManager == null) return;
            try
            {
                if (originalNotificationVolume >= 0)
                    audioManager.Call("setStreamVolume", STREAM_NOTIFICATION, originalNotificationVolume, 0);
                if (originalSystemVolume >= 0)
                    audioManager.Call("setStreamVolume", STREAM_SYSTEM, originalSystemVolume, 0);
            }
            catch { }
        }
#endif

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
            if (pendingRestart && continuousListening)
            {
                pendingRestart = false;
                Invoke(nameof(StartListening), restartDelaySeconds);
            }
#endif
        }

#if UNITY_ANDROID && !UNITY_EDITOR
        private void Start()
        {
            if (continuousListening) StartListening();
        }
#endif

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
            if (mainActivity == null) return;

            isListening = true;
            mainActivity.Call("runOnUiThread", new AndroidJavaRunnable(() =>
            {
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

                    recognizer.Call("startListening", intent);
                    Debug.Log("[Voice] Listening...");
                }
                catch (System.Exception ex)
                {
                    Debug.LogError($"[Voice] Listen failed: {ex.Message}");
                    isListening = false;
                }
            }));
        }

        private void OnDestroy()
        {
            RestoreRecognizerBeeps();

            if (recognizer == null || mainActivity == null) return;
            AndroidJavaObject toDestroy = recognizer;
            recognizer = null;
            try
            {
                mainActivity.Call("runOnUiThread", new AndroidJavaRunnable(() =>
                {
                    try { toDestroy.Call("destroy"); toDestroy.Dispose(); } catch { }
                }));
            }
            catch { }
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
            [UnityEngine.Scripting.Preserve] public void onError(int e) { owner.isListening = false; owner.pendingErrorCode = e; owner.pendingRestart = true; }
            [UnityEngine.Scripting.Preserve] public void onPartialResults(AndroidJavaObject p) { }
            [UnityEngine.Scripting.Preserve] public void onEvent(int e, AndroidJavaObject p) { }

            [UnityEngine.Scripting.Preserve]
            public void onResults(AndroidJavaObject results)
            {
                owner.isListening = false;
                owner.pendingRestart = true;
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
