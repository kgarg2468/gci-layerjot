using UnityEngine;
using UnityEngine.UI;

namespace CLABSIApp
{
    public class AiDisclaimerOverlay : MonoBehaviour
    {
        private const string Disclaimer = "AI is advisory - human oversight required";

        [SerializeField] private Text disclaimerText;

        private void Awake()
        {
            if (disclaimerText == null) disclaimerText = GetComponent<Text>();
            if (disclaimerText != null) disclaimerText.text = Disclaimer;
        }
    }
}
