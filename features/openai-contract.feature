Feature: Existing LinguAI caller contract
  The service implements the OpenAI-compatible API called by the existing VPS worker.

  Scenario: A valid request receives a schema-valid teacher label
    Given the selected model is loaded and the caller is authenticated
    And the request has a model identifier, temperature 0, exact system prompt, and exact user payload template
    And the user payload contains only the document ID and teacher sketch without source dataset metadata
    When the caller posts to /v1/chat/completions
    Then the response has choices[0].message.content as a string
    And the string contains exactly one JSON object valid against teacher_label_v1.schema.json
    And the label ID equals the requested document ID
    And the teacher output contains no routing, provenance, explanation, reasoning, or repair fields

  Scenario: The prompt and sketch are forwarded intact
    Given the caller sends the versioned system prompt and a bounded document sketch
    When the serving backend formats its model input
    Then the system prompt text is unchanged
    And the user template delimiters, document ID, and sketch are preserved
    And no source dataset name is added

  Scenario: The model returns prose, reasoning, a fence, invalid JSON, or schema-invalid JSON
    Given raw model output does not meet the teacher response contract
    When the service validates the candidate completion
    Then it does not report a successful teacher label
    And it returns a controlled error or retries within a bounded configured limit
    And it never leaks raw generated text in the public error or logs

  Scenario: The generated label identifies a different document
    Given a request identifies document A
    When the model returns a schema-valid label for document B
    Then the inference fails
    And the service does not replace B with A
    And no successful label is returned

  Scenario: The request names an unsupported model
    Given the API advertises one pinned model identifier
    When an authenticated request names a different model
    Then the service rejects it before GPU inference

  Scenario: The request is malformed or exceeds configured bounds
    Given the messages omit required content or exceed the measured request/token limit
    When request validation runs
    Then inference does not start
    And a controlled non-success response does not echo the document

  Scenario: The serving backend can constrain JSON generation
    Given the selected backend supports schema-constrained decoding
    When that feature is enabled using the committed schema
    Then the public request remains compatible with the existing caller
    And the service still independently parses, schema-validates, and ID-validates output

  Scenario: Backend error and timeout preserve control-plane ownership
    Given a model load error, GPU out-of-memory condition, backend error, or client timeout
    When the service cannot produce a valid completion
    Then it returns a controlled non-success response
    And it does not create a durable job, attempt, or label
