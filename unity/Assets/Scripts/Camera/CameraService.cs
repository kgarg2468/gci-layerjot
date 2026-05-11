using System;
using System.Runtime.InteropServices;
using UnityEngine;
#if !UNITY_EDITOR && UNITY_ANDROID
using Unity.XR.XREAL;
#endif

namespace CLABSIApp.CameraFeed
{
    /// <summary>
    /// Wraps XREAL's RGB camera polling API. Start/Stop capture and pull the latest frame
    /// as a managed byte[]. Phase 4 consumes this for breach-detection upload.
    /// Editor: no-op stub (returns false from TryAcquireFrame).
    /// </summary>
    public class CameraService : MonoBehaviour
    {
        public static CameraService Instance { get; private set; }

        public bool IsCapturing { get; private set; }
        public Vector2Int LastResolution { get; private set; }
        public ulong LastTimestamp { get; private set; }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
        }

        void OnDestroy()
        {
            if (IsCapturing) StopCapture();
            if (Instance == this) Instance = null;
        }

        public void StartCapture()
        {
            if (IsCapturing) return;
#if !UNITY_EDITOR && UNITY_ANDROID
            ulong handle = XREALPlugin.StartRGBCameraDataCapture();
            if (handle == 0)
            {
                Debug.LogWarning("[CameraService] StartRGBCameraDataCapture returned 0 (failed or no device)");
                return;
            }
            IsCapturing = true;
            Debug.Log("[CameraService] Capture started");
#else
            Debug.Log("[CameraService] Editor stub — no real capture");
#endif
        }

        public void StopCapture()
        {
            if (!IsCapturing) return;
#if !UNITY_EDITOR && UNITY_ANDROID
            XREALPlugin.StopRGBCameraDataCapture();
#endif
            IsCapturing = false;
            Debug.Log("[CameraService] Capture stopped");
        }

        /// <summary>
        /// Acquire and copy the latest frame. Returns false if no frame is ready or capture is off.
        /// Caller receives a freshly allocated byte[] of plane-0 raw data; resolution + timestamp track the frame.
        /// </summary>
        public bool TryAcquireFrame(out byte[] data, out Vector2Int resolution, out ulong timestamp)
        {
            data = null;
            resolution = default;
            timestamp = 0;

#if !UNITY_EDITOR && UNITY_ANDROID
            if (!IsCapturing) return false;

            int frameHandle = 0;
            Vector2Int res = default;
            ulong ts = 0;
            if (!XREALPlugin.TryAcquireLatestImage(ref frameHandle, ref res, ref ts)) return false;
            if (!XREALPlugin.IsRGBCameraDataHandleValid(frameHandle)) return false;

            try
            {
                if (!XREALPlugin.TryGetRGBCameraDataPlane(frameHandle, 0, out IntPtr ptr, out Vector2Int planeSize))
                    return false;

                int byteCount = planeSize.x * planeSize.y;
                if (byteCount <= 0 || ptr == IntPtr.Zero) return false;

                byte[] copy = new byte[byteCount];
                Marshal.Copy(ptr, copy, 0, byteCount);

                data = copy;
                resolution = res;
                timestamp = ts;
                LastResolution = res;
                LastTimestamp = ts;
                return true;
            }
            finally
            {
                XREALPlugin.DisposeRGBCameraDataHandle(frameHandle);
            }
#else
            return false;
#endif
        }
    }
}
