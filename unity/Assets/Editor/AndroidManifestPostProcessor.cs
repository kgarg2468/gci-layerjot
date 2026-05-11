using System.IO;
using System.Xml;
using UnityEditor.Android;
using UnityEngine;

namespace CLABSIApp.EditorTools
{
    public class AndroidManifestPostProcessor : IPostGenerateGradleAndroidProject
    {
        public int callbackOrder => 1;

        private const string AndroidNs = "http://schemas.android.com/apk/res/android";

        public void OnPostGenerateGradleAndroidProject(string path)
        {
            string manifestPath = Path.Combine(path, "src", "main", "AndroidManifest.xml");
            if (!File.Exists(manifestPath))
            {
                Debug.LogWarning($"[ManifestPostProcessor] Manifest not found at {manifestPath}");
                return;
            }

            XmlDocument doc = new XmlDocument();
            doc.Load(manifestPath);
            XmlElement manifest = doc.DocumentElement;
            if (manifest == null) return;

            bool changed = false;

            string[] requiredPermissions =
            {
                "android.permission.RECORD_AUDIO",
                "android.permission.CAMERA",
            };
            foreach (var permName in requiredPermissions)
            {
                if (HasPermission(manifest, permName)) continue;
                XmlElement perm = doc.CreateElement("uses-permission");
                perm.SetAttribute("name", AndroidNs, permName);
                manifest.InsertBefore(perm, manifest.FirstChild);
                changed = true;
            }

            XmlElement queries = manifest.SelectSingleNode("queries") as XmlElement;
            if (queries == null)
            {
                queries = doc.CreateElement("queries");
                manifest.AppendChild(queries);
                changed = true;
            }

            if (!HasSpeechIntent(queries))
            {
                XmlElement intent = doc.CreateElement("intent");
                XmlElement action = doc.CreateElement("action");
                action.SetAttribute("name", AndroidNs, "android.speech.RecognitionService");
                intent.AppendChild(action);
                queries.AppendChild(intent);
                changed = true;
            }

            if (changed)
            {
                doc.Save(manifestPath);
                Debug.Log("[ManifestPostProcessor] Injected RECORD_AUDIO + CAMERA permissions and SpeechRecognizer query");
            }
        }

        private static bool HasPermission(XmlElement manifest, string permissionName)
        {
            foreach (XmlNode node in manifest.SelectNodes("uses-permission"))
            {
                if (node is XmlElement el && el.GetAttribute("name", AndroidNs) == permissionName) return true;
            }
            return false;
        }

        private static bool HasSpeechIntent(XmlElement queries)
        {
            foreach (XmlNode intentNode in queries.SelectNodes("intent"))
            {
                if (!(intentNode is XmlElement intent)) continue;
                foreach (XmlNode actionNode in intent.SelectNodes("action"))
                {
                    if (actionNode is XmlElement action && action.GetAttribute("name", AndroidNs) == "android.speech.RecognitionService") return true;
                }
            }
            return false;
        }
    }
}
