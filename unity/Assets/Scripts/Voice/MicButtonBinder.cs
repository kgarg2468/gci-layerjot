using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    [RequireComponent(typeof(Button))]
    public class MicButtonBinder : MonoBehaviour
    {
        static readonly Color ListeningColor = new Color(0.20f, 0.80f, 0.30f, 1f);
        static readonly Color IdleColor = new Color(0.85f, 0.20f, 0.20f, 1f);

        Image _image;

        void Awake()
        {
            Button btn = GetComponent<Button>();
            btn.onClick.AddListener(OnClicked);
            _image = GetComponent<Image>();
        }

        void Update()
        {
            if (_image == null) return;
            bool listening = VoiceService.Instance != null && VoiceService.Instance.IsListening;
            Color target = listening ? ListeningColor : IdleColor;
            if (_image.color != target) _image.color = target;
        }

        void OnClicked()
        {
            VoiceService.Instance?.StartListening();
        }
    }
}
