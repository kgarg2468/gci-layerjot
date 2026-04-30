using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace CLABSIApp.UI
{
    public enum AlertSeverity
    {
        Info,
        Warning,
        Critical
    }

    public class AlertOverlay : MonoBehaviour
    {
        public static AlertOverlay Instance { get; private set; }

        const float DefaultDurationSeconds = 5f;

        GameObject _panel;
        Image _severityBar;
        TMP_Text _messageText;
        Coroutine _dismissCoroutine;

        static readonly Color InfoColor = new Color(0.20f, 0.55f, 0.90f, 1f);
        static readonly Color WarningColor = new Color(0.95f, 0.60f, 0.10f, 1f);
        static readonly Color CriticalColor = new Color(0.85f, 0.20f, 0.20f, 1f);

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;

            _panel = transform.Find("Panel")?.gameObject;
            if (_panel == null) { Debug.LogError("[AlertOverlay] Missing Panel child"); return; }

            _severityBar = _panel.transform.Find("SeverityBar")?.GetComponent<Image>();
            _messageText = _panel.transform.Find("MessageText")?.GetComponent<TMP_Text>();

            _panel.SetActive(false);
        }

        public void ShowAlert(AlertSeverity severity, string message, float durationSeconds = DefaultDurationSeconds)
        {
            if (_panel == null) return;

            if (_severityBar != null) _severityBar.color = ColorFor(severity);
            if (_messageText != null) _messageText.text = message;

            _panel.SetActive(true);

            if (_dismissCoroutine != null) StopCoroutine(_dismissCoroutine);
            _dismissCoroutine = StartCoroutine(DismissAfter(durationSeconds));

            Debug.Log($"[AlertOverlay] {severity}: {message}");
        }

        public void Dismiss()
        {
            if (_dismissCoroutine != null) { StopCoroutine(_dismissCoroutine); _dismissCoroutine = null; }
            if (_panel != null) _panel.SetActive(false);
        }

        IEnumerator DismissAfter(float seconds)
        {
            yield return new WaitForSeconds(seconds);
            Dismiss();
        }

        static Color ColorFor(AlertSeverity severity) => severity switch
        {
            AlertSeverity.Critical => CriticalColor,
            AlertSeverity.Warning => WarningColor,
            _ => InfoColor,
        };
    }
}
