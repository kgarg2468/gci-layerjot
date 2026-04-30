using UnityEngine;

namespace CLABSIApp.UI
{
    /// <summary>
    /// Wires the WorldSpace Canvas's eventCamera to Camera.main at runtime so the
    /// GraphicRaycaster can hit-test against pointer events on the AR HUD.
    /// </summary>
    [RequireComponent(typeof(Canvas))]
    public class WorldSpaceCanvasSetup : MonoBehaviour
    {
        void Awake()
        {
            var canvas = GetComponent<Canvas>();
            if (canvas.renderMode != RenderMode.WorldSpace) return;
            if (canvas.worldCamera != null) return;

            var cam = Camera.main;
            if (cam == null)
            {
                Debug.LogWarning("[WorldSpaceCanvasSetup] No Camera.main found; skipping eventCamera wiring");
                return;
            }
            canvas.worldCamera = cam;
            Debug.Log($"[WorldSpaceCanvasSetup] Wired Canvas.eventCamera to {cam.name}");
        }
    }
}
