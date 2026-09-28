Feature: Exact model-token admission
  Scenario: Full prompt fits at the boundary
    Given the rendered messages tokenize to 7136 tokens
    And the context is 8192 with 1024 output tokens and 32 safety tokens
    When the request is admitted
    Then the exact 7136 token IDs are sent for generation without reformatting

  Scenario: One token beyond the boundary
    Given the rendered messages tokenize to 7137 tokens
    When the request asks for 1024 output tokens in an 8192 context
    Then the API returns context_length_exceeded before generation
    And no prompt or document is shortened

  Scenario: Model hits its output limit
    Given the backend stops because the output budget is exhausted
    When the response is validated
    Then the API reports output_limit instead of accepting a partial label
