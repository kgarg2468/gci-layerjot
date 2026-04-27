using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    [RequireComponent(typeof(Button))]
    public class MicButtonBinder : MonoBehaviour
    {
        private void Awake()
        {
            Button btn = GetComponent<Button>();
            btn.onClick.AddListener(OnClicked);
        }

        private void OnClicked()
        {
            VoiceService.Instance?.StartListening();
        }
    }
}
