using System;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace CLABSIApp
{
    public class AiWebSocketClient : MonoBehaviour
    {
        public static AiWebSocketClient Instance { get; private set; }

        [SerializeField] private string backendUrl = "ws://127.0.0.1:8000/ws";
        [SerializeField] private bool connectOnStart = true;

        private readonly Queue<AiResponseEnvelope> pendingResponses = new Queue<AiResponseEnvelope>();
        private ClientWebSocket socket;
        private CancellationTokenSource cancellation;
        private bool connecting;

        public bool IsConnected => socket != null && socket.State == WebSocketState.Open;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(this);
                return;
            }

            Instance = this;
        }

        private async void Start()
        {
            if (connectOnStart) await ConnectWithBackoff();
        }

        private void Update()
        {
            while (true)
            {
                AiResponseEnvelope response = null;
                lock (pendingResponses)
                {
                    if (pendingResponses.Count > 0) response = pendingResponses.Dequeue();
                }

                if (response == null) break;
                AiActionExecutor.Instance?.Execute(response);
            }
        }

        public async void SubmitTranscript(string transcript)
        {
            AiContextPayload context = AiContextProvider.Instance != null
                ? AiContextProvider.Instance.Build()
                : new AiContextPayload { session_id = Guid.NewGuid().ToString(), current_screen = "unknown" };

            if (!IsConnected)
            {
                await ConnectWithBackoff();
            }

            if (!IsConnected)
            {
                Enqueue(AiFallbackResponses.Resolve(transcript, context));
                return;
            }

            AiRequestEnvelope envelope = new AiRequestEnvelope
            {
                session_id = context.session_id,
                timestamp = DateTime.UtcNow.ToString("o"),
                payload = new AiRequestPayload
                {
                    transcript = transcript,
                    context = context
                }
            };

            await SendJson(JsonUtility.ToJson(envelope));
        }

        public async void SendCameraFrame(string jpegBase64, AiCameraFrameMetadata metadata = null)
        {
            AiContextPayload context = AiContextProvider.Instance != null ? AiContextProvider.Instance.Build() : null;
            if (!IsConnected) await ConnectWithBackoff();
            if (!IsConnected) return;

            AiCameraFrameEnvelope envelope = new AiCameraFrameEnvelope
            {
                session_id = context != null ? context.session_id : Guid.NewGuid().ToString(),
                timestamp = DateTime.UtcNow.ToString("o"),
                payload = new AiCameraFramePayload
                {
                    image_jpeg_base64 = jpegBase64,
                    context = context,
                    metadata = metadata ?? new AiCameraFrameMetadata()
                }
            };

            await SendJson(JsonUtility.ToJson(envelope));
        }

        public async void SendProcedureComplete(ProcedureLogEntry entry)
        {
            if (entry == null) return;
            AiContextPayload context = AiContextProvider.Instance != null ? AiContextProvider.Instance.Build() : null;
            if (!IsConnected) await ConnectWithBackoff();
            if (!IsConnected) return;

            AiProcedureCompleteEnvelope envelope = new AiProcedureCompleteEnvelope
            {
                session_id = context != null ? context.session_id : Guid.NewGuid().ToString(),
                timestamp = DateTime.UtcNow.ToString("o"),
                payload = new AiProcedureCompletePayload
                {
                    procedure_id = entry.procedureId,
                    procedure_name = entry.procedureName,
                    started_at = entry.startedAtIso,
                    completed_at = entry.completedAtIso,
                    total_steps = entry.totalSteps,
                    completed_step_ids = entry.completedStepIds,
                    ai_events = entry.aiEvents
                }
            };

            await SendJson(JsonUtility.ToJson(envelope));
        }

        public async void Reconnect()
        {
            try
            {
                cancellation?.Cancel();
                if (socket != null)
                {
                    try { await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "reconnect", CancellationToken.None); } catch { }
                    socket.Dispose();
                    socket = null;
                }
            }
            catch { }
            connecting = false;
            await ConnectWithBackoff();
        }

        private async Task ConnectWithBackoff()
        {
            if (IsConnected || connecting) return;
            connecting = true;
            cancellation = new CancellationTokenSource();

            int[] delays = { 0, 1000, 2000, 4000 };
            foreach (int delayMs in delays)
            {
                if (delayMs > 0) await Task.Delay(delayMs);
                try
                {
                    socket?.Dispose();
                    socket = new ClientWebSocket();
                    string url = SettingsStore.BuildBackendUrl(backendUrl);
                    await socket.ConnectAsync(new Uri(url), cancellation.Token);
                    _ = ReceiveLoop();
                    Debug.Log("[AI WS] Connected");
                    connecting = false;
                    return;
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[AI WS] Connect failed: {ex.Message}");
                }
            }

            connecting = false;
        }

        private async Task SendJson(string json)
        {
            if (!IsConnected) return;
            byte[] bytes = Encoding.UTF8.GetBytes(json);
            try
            {
                await socket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, cancellation.Token);
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[AI WS] Send failed: {ex.Message}");
            }
        }

        private async Task ReceiveLoop()
        {
            byte[] buffer = new byte[8192];
            while (IsConnected)
            {
                try
                {
                    WebSocketReceiveResult result = await socket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellation.Token);
                    if (result.MessageType == WebSocketMessageType.Close) break;

                    string json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                    AiResponseEnvelope response = JsonUtility.FromJson<AiResponseEnvelope>(json);
                    Enqueue(response);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"[AI WS] Receive failed: {ex.Message}");
                    break;
                }
            }
        }

        private void Enqueue(AiResponseEnvelope response)
        {
            lock (pendingResponses)
            {
                pendingResponses.Enqueue(response);
            }
        }

        private async void OnDestroy()
        {
            try
            {
                cancellation?.Cancel();
                if (socket != null)
                {
                    await socket.CloseAsync(WebSocketCloseStatus.NormalClosure, "destroy", CancellationToken.None);
                    socket.Dispose();
                }
            }
            catch { }
        }
    }
}
