Feature: Secure disposable inference boundary
  The VPS is the durable system of record and the GPU host can be replaced.

  Scenario: A caller sends no valid service credential
    Given the inference service is configured with a nonempty credential
    When a caller omits or misstates its bearer credential
    Then the API denies the request before model inference
    And no document, prompt, generated label or credential appears in the response or logs

  Scenario: The API is reachable from the VPS
    Given the operator has a Jupyter/SSH URL for the GPU instance
    When the control plane configures its teacher base URL
    Then it uses the actual inference API route over authenticated TLS or an approved private encrypted tunnel
    And it does not treat Jupyter as the inference API

  Scenario: The GPU process disappears during an inference
    Given a VPS-owned pending job and a request in flight
    When the GPU process stops or its network route fails
    Then the request times out or returns a controlled non-success response
    And the VPS retains the source document and retryable state
    And the GPU service has no database credentials or direct write path to the VPS

  Scenario: A replacement GPU endpoint is selected
    Given pending jobs remain persisted on the VPS
    When an operator configures a new measured and versioned endpoint
    Then the VPS can retry pending jobs using the new profile
    And previous attempts retain their original model/profile/endpoint fingerprint
    And accepted labels are not silently overwritten

  Scenario: Logs and notebook output are inspected
    Given successful, rejected, and timed-out inference calls
    When service logs, metrics, traces, and notebook output are reviewed
    Then raw document text, complete prompts, API credentials, and generated labels are absent
    And request correlation uses a non-sensitive ID or redacted hash

  Scenario: An oversized or adversarial document is received
    Given an untrusted document sketch reaches the API
    When it exceeds configured size or model-context bounds
    Then it is rejected before model execution without echoing its content
    And the prompt and output validation contract remains active
