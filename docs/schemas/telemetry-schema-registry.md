# Telemetry Schema Registry

## Purpose
Provide a canonical, attested registry of telemetry sources, event types, and fields to prevent hallucinated field names in detection logic.

## Registry structure

Each telemetry source entry:
```json
{
  "source_id": "string (unique identifier)",
  "platform": "string (windows/linux/cloud/aks/macos)",
  "source": "string (sysmon/auditd/cloudtrail/k8s_audit/edr_vendor/...)",
  "event_id": "string or integer or null",
  "category": "string (process_creation/network_connection/file_creation/...)",
  "sigma_logsource": {
    "product": "string",
    "category": "string",
    "service": "string or null"
  },
  "fields": [
    {
      "field_name": "string",
      "field_type": "string (string/integer/datetime/array/...)",
      "description": "string",
      "required": "boolean"
    }
  ],
  "supported_modifiers": ["array of Sigma modifiers: contains/endswith/startswith/re/..."]
}
```

## Example entries

### Windows Sysmon Event ID 1 (Process Creation)
```json
{
  "source_id": "sysmon_event_1",
  "platform": "windows",
  "source": "sysmon",
  "event_id": 1,
  "category": "process_creation",
  "sigma_logsource": {
    "product": "windows",
    "category": "process_creation",
    "service": null
  },
  "fields": [
    {
      "field_name": "Image",
      "field_type": "string",
      "description": "Full path of the process executable",
      "required": true
    },
    {
      "field_name": "CommandLine",
      "field_type": "string",
      "description": "Full command line including arguments",
      "required": false
    },
    {
      "field_name": "ParentImage",
      "field_type": "string",
      "description": "Full path of the parent process executable",
      "required": false
    },
    {
      "field_name": "User",
      "field_type": "string",
      "description": "User account that started the process",
      "required": false
    },
    {
      "field_name": "Hashes",
      "field_type": "string",
      "description": "Hash values of the process image",
      "required": false
    }
  ],
  "supported_modifiers": ["contains", "endswith", "startswith", "contains|all", "re"]
}
```

### Linux Auditd Execve
```json
{
  "source_id": "auditd_execve",
  "platform": "linux",
  "source": "auditd",
  "event_id": null,
  "category": "process_creation",
  "sigma_logsource": {
    "product": "linux",
    "category": "process_creation",
    "service": "auditd"
  },
  "fields": [
    {
      "field_name": "exe",
      "field_type": "string",
      "description": "Executable path",
      "required": true
    },
    {
      "field_name": "a0",
      "field_type": "string",
      "description": "First argument",
      "required": false
    },
    {
      "field_name": "uid",
      "field_type": "string",
      "description": "User ID",
      "required": false
    },
    {
      "field_name": "comm",
      "field_type": "string",
      "description": "Command name",
      "required": false
    }
  ],
  "supported_modifiers": ["contains", "endswith", "startswith", "re"]
}
```

### Azure/Cloud - CloudTrail
```json
{
  "source_id": "cloudtrail_event",
  "platform": "cloud",
  "source": "cloudtrail",
  "event_id": null,
  "category": "cloud_api",
  "sigma_logsource": {
    "product": "aws",
    "service": "cloudtrail",
    "category": null
  },
  "fields": [
    {
      "field_name": "eventName",
      "field_type": "string",
      "description": "API action name",
      "required": true
    },
    {
      "field_name": "userIdentity.principalId",
      "field_type": "string",
      "description": "Principal ID of the caller",
      "required": false
    },
    {
      "field_name": "sourceIPAddress",
      "field_type": "string",
      "description": "Source IP address",
      "required": false
    },
    {
      "field_name": "errorCode",
      "field_type": "string",
      "description": "Error code if action failed",
      "required": false
    }
  ],
  "supported_modifiers": ["contains", "endswith", "startswith"]
}
```

### Kubernetes Audit Log
```json
{
  "source_id": "k8s_audit",
  "platform": "aks",
  "source": "k8s_audit",
  "event_id": null,
  "category": "k8s_api",
  "sigma_logsource": {
    "product": "kubernetes",
    "service": "audit",
    "category": null
  },
  "fields": [
    {
      "field_name": "verb",
      "field_type": "string",
      "description": "API verb (create/delete/update/get/list/...)",
      "required": true
    },
    {
      "field_name": "objectRef.resource",
      "field_type": "string",
      "description": "Resource type (pods/secrets/configmaps/...)",
      "required": false
    },
    {
      "field_name": "user.username",
      "field_type": "string",
      "description": "Username of the requester",
      "required": false
    },
    {
      "field_name": "sourceIPs",
      "field_type": "array",
      "description": "Source IP addresses",
      "required": false
    }
  ],
  "supported_modifiers": ["contains", "endswith"]
}
```

## Field attestation methods

### schema_verified
Field exists in official schema documentation or vendor spec.

### sample_verified
Field observed in actual sample logs from the source.

### tool_verified
Field confirmed via query tool (e.g., Kusto `get_table_schema`, `sample_table_data`).

## Usage in Telemetry Scout Agent
1. Load registry entries matching platform and available sources.
2. Filter by ATT&CK data source/data component mapping.
3. Attest only fields present in registry.
4. Return attested field list with attestation method.

## Usage in Detection Architect Agent
1. Validate that all fields in `detection_logic` exist in `required_telemetry.fields`.
2. Reject DetectionSpec if any field is not attested.

## Usage in Rule Writer Agent
1. Only generate Sigma/KQL using fields from DetectionSpec `required_telemetry`.
2. Use `sigma_logsource` mapping from registry for Sigma rule `logsource` section.
3. Use `supported_modifiers` to validate modifier usage.

## Registry maintenance
- Registry should be version-controlled.
- Updates require schema validation and review.
- New sources added via pull request with attestation evidence.
