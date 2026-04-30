using System;
using UnityEngine;

namespace CLABSIApp
{
    public static class AiFallbackResponses
    {
        public static AiResponseEnvelope Resolve(string transcript, AiContextPayload context)
        {
            string lowered = (transcript ?? string.Empty).ToLowerInvariant();

            if (lowered.Contains("dose") || lowered.Contains("diagnose"))
            {
                return Build(
                    "show_alert",
                    "I can't provide diagnosis or medication dosing guidance. Please consult the attending physician.",
                    "warning",
                    context);
            }

            if (lowered.Contains("hand hygiene") || lowered.Contains("sterile") || lowered.Contains("breach"))
            {
                return Build(
                    "show_alert",
                    "Confirm hand hygiene and sterile technique before continuing. AI guidance is advisory.",
                    "warning",
                    context);
            }

            return Build(
                "read_step",
                "The AI backend is offline. Continue using the local checklist and verify clinical decisions with the care team.",
                "info",
                context);
        }

        private static AiResponseEnvelope Build(string actionCmd, string spoken, string severity, AiContextPayload context)
        {
            return new AiResponseEnvelope
            {
                type = "ai_response",
                session_id = context != null ? context.session_id : Guid.NewGuid().ToString(),
                timestamp = DateTime.UtcNow.ToString("o"),
                schema_version = "clabsi-ar.v1",
                action_cmd = actionCmd,
                spoken_response = spoken,
                parameters = new AiActionParameters
                {
                    severity = severity,
                    message = spoken,
                    advisory = true,
                    procedure_id = context != null ? context.procedure_id : null,
                    current_step_id = context != null ? context.current_step_id : -1
                }
            };
        }
    }
}
