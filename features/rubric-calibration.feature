Feature: Small explicitly approved rubric calibration
  Model behavior is reviewed on a small approved set before any larger teacher run.

  Background:
    Given the exact turkish_cpt_quality_teacher_v2 system prompt
    And teacher_label_v1.schema.json
    And only a small human-reviewed calibration set explicitly approved for inference

  Scenario: Excellent natural Turkish article
    When the teacher labels a coherent, informative, clean Turkish article
    Then language, coherence, information, cleanliness, structure and utility are high

  Scenario: Valuable text contaminated with boilerplate
    When the teacher labels an informative article with material cookie, menu or markup debris
    Then information remains high while cleanliness is lower
    And boilerplate_ui or markup_extraction is returned when materially present
    And no KEEP or DROP route is emitted

  Scenario: Meaningful code contains no natural-language prose
    When the teacher labels intact Python or C++ source
    Then type is code
    And language may be null
    And information, structure and utility may be high

  Scenario: Meaningful structured, mathematical or reference content
    When the teacher labels an intact table, formula, list, JSON or reference passage
    Then format alone does not force low language, information, structure or utility

  Scenario: Fluent SEO filler
    When the teacher labels fluent but repetitive advertising filler
    Then good language does not force high information or cleanliness
    And relevant material noise flags are present

  Scenario: Natural forum conversation
    When the teacher labels a coherent, useful informal discussion
    Then its informal register alone does not lower utility

  Scenario: Unrelated fragment soup
    When the teacher labels a document joined from unrelated fragments
    Then coherence and utility are low
    And unrelated_merge is flagged when materially present

  Scenario: Valuable document with OCR damage
    When the teacher labels information-rich text with material OCR corruption
    Then information can remain high while language and cleanliness are low
    And encoding_ocr is flagged when materially present

  Scenario: The calibration allowance is exhausted
    Given no approval exists for full-dataset teacher labeling
    When the configured small calibration count has been used
    Then no further model request is started by setup, readiness or calibration tooling
