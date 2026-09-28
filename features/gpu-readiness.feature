Feature: Readiness on the actual rented GPU
  Readiness proves the selected profile can serve bounded requests on this exact host.

  Scenario: SSH and Jupyter work but model serving is not started
    Given the operator can open Jupyter and SSH on the reported 48 GB instance
    When the API process or model is not loaded
    Then liveness may pass when the process responds
    But readiness is unavailable
    And probes create no inference, job, or teacher label

  Scenario: A model is configured but does not fit
    Given actual GPU model/count, free VRAM, pinned revision, context and concurrency are recorded
    When model load or a representative bounded request runs out of memory
    Then readiness remains unavailable
    And the service records a redacted failure without claiming that 48 GB guarantees fit

  Scenario: Readiness succeeds only after bounded inference initialization
    Given a pinned model revision and serving runtime are recorded
    When all required weights and model runtime initialization complete
    Then a non-labeling local readiness check succeeds
    And readiness identifies the configured model/profile
    And the VPS can reach the API through the approved secure route

  Scenario: The current caller deadline is missed
    Given representative requests from the approved document-size range
    When end-to-end p95 latency exceeds the current 20-second caller timeout
    Then the profile is not accepted for live teacher jobs
    And the 20-second timeout, 60-second claim lease, and 30-second heartbeat freshness are reviewed together
    And a caller change is separately tested before accepting the profile

  Scenario: Probes never trigger labeling
    Given the GPU service is starting, restarting, or becoming ready
    When process, model, and network health probes execute
    Then no document dataset is fetched
    And no completion label, labeling attempt, or billable calibration call is created

  Scenario: Concurrency remains within measured memory budget
    Given a tested VRAM budget includes weights, KV cache and runtime overhead
    When simultaneous requests reach the configured limit
    Then the configured work stays within the measured budget
    And excess requests are bounded or rejected with a controlled response
