using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace CLABSIApp
{
    public static class ProcedureLogStore
    {
        private static List<ProcedureLogEntry> cache;

        private static string FilePath => Path.Combine(Application.persistentDataPath, "procedure_log.json");

        public static IReadOnlyList<ProcedureLogEntry> LoadAll()
        {
            if (cache != null) return cache;
            cache = new List<ProcedureLogEntry>();

            if (!File.Exists(FilePath)) return cache;

            try
            {
                string json = File.ReadAllText(FilePath);
                ProcedureLogFile file = JsonUtility.FromJson<ProcedureLogFile>(json);
                if (file != null && file.entries != null) cache.AddRange(file.entries);
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ProcedureLogStore] Failed to load: {ex.Message}");
            }
            return cache;
        }

        public static void Add(ProcedureLogEntry entry)
        {
            if (entry == null) return;
            LoadAll();
            cache.Add(entry);
            Save();
        }

        private static void Save()
        {
            try
            {
                ProcedureLogFile file = new ProcedureLogFile { entries = cache.ToArray() };
                string json = JsonUtility.ToJson(file, true);
                File.WriteAllText(FilePath, json);
                Debug.Log($"[ProcedureLogStore] Saved {cache.Count} entries to {FilePath}");
            }
            catch (Exception ex)
            {
                Debug.LogError($"[ProcedureLogStore] Failed to save: {ex.Message}");
            }
        }

        [Serializable]
        private class ProcedureLogFile
        {
            public ProcedureLogEntry[] entries;
        }
    }
}
