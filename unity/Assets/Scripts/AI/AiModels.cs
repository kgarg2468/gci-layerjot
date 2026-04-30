using System;

namespace CLABSIApp
{
    [Serializable]
    public class AiRequestEnvelope
    {
        public string type = "ai_request";
        public string session_id;
        public string timestamp;
        public AiRequestPayload payload;
    }

    [Serializable]
    public class AiRequestPayload
    {
        public string transcript;
        public AiContextPayload context;
    }

    [Serializable]
    public class AiContextPayload
    {
        public string session_id;
        public string patient_id;
        public string current_screen;
        public int current_step = -1;
        public bool procedure_active;
        public string procedure_id;
        public string procedure_name;
        public int current_step_id = -1;
        public string current_step_title;
        public int total_steps;
        public int[] completed_step_ids;
        public int[] missed_step_ids;
        public string started_at;
    }

    [Serializable]
    public class AiResponseEnvelope
    {
        public string type;
        public string session_id;
        public string timestamp;
        public string schema_version;
        public string action_cmd;
        public AiActionParameters parameters;
        public string spoken_response;
        public AiResponsePayload payload;
    }

    [Serializable]
    public class AiResponsePayload
    {
        public string intent;
        public string spoken_response;
        public AiLegacyAction action;
        public AiDebugPayload debug;
    }

    [Serializable]
    public class AiLegacyAction
    {
        public string type;
        public AiActionParameters params_;
    }

    [Serializable]
    public class AiDebugPayload
    {
        public string tool_called;
        public string[] tool_calls;
        public int latency_ms;
    }

    [Serializable]
    public class AiActionParameters
    {
        public string severity;
        public string message;
        public string screen;
        public string action_type;
        public string risk;
        public string breach_type;
        public float confidence;
        public bool advisory;
        public string status;
        public string procedure_id;
        public string procedure_name;
        public int current_step_id;
        public int compliance_score;
        public int[] missed_step_ids;
        public int[] completed_step_ids;
        public int total_steps;
        public int elapsed_minutes;
        public int ai_event_count;
        public AiEvent[] ai_events;
        public string[] sources;
    }

    [Serializable]
    public class AiCameraFrameEnvelope
    {
        public string type = "camera_frame";
        public string session_id;
        public string timestamp;
        public AiCameraFramePayload payload;
    }

    [Serializable]
    public class AiCameraFramePayload
    {
        public string image_jpeg_base64;
        public AiContextPayload context;
        public AiCameraFrameMetadata metadata;
    }

    [Serializable]
    public class AiCameraFrameMetadata
    {
        public bool simulated_breach;
        public bool breach_detected;
        public string breach_type;
        public float confidence;
    }

    [Serializable]
    public class AiProcedureCompleteEnvelope
    {
        public string type = "procedure_complete";
        public string session_id;
        public string timestamp;
        public AiProcedureCompletePayload payload;
    }

    [Serializable]
    public class AiProcedureCompletePayload
    {
        public string procedure_id;
        public string procedure_name;
        public string started_at;
        public string completed_at;
        public int total_steps;
        public int[] completed_step_ids;
        public AiEvent[] ai_events;
    }
}
