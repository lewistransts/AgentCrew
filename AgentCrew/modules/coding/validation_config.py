# Define the validation prompt template for LLM spec validation
validation_prompt_template = """
You are a senior software architect reviewing a spec prompt that will be give to a Coding Assistant to implement the task. 
Your task is to validate this prompt to make sure each section belows pass given criteria against code analyze below

<ValidationCriteria>
  <Section name="Objectives">
    <Criterion>Are objectives clear, specific and actionable?</Criterion>
    <Criterion>Do objectives cover all key functionality requirements?</Criterion>
    <Criterion>Is each objective technically feasible and well-defined?</Criterion>
    <Criterion>Are there any conflicting or redundant objectives?</Criterion>
    <Criterion>Do objectives align with the overall architecture?</Criterion>
    <Criterion>Are performance expectations or constraints specified where needed?</Criterion>
  </Section>
  
  <Section name="Contexts">
    <Criterion>Are all necessary files listed, including both existing and new files?</Criterion>
    <Criterion>Does each file have a clear, descriptive explanation?</Criterion>
    <Criterion>Are file paths accurate and consistent with project structure?</Criterion>
    <Criterion>Is the relationship between files clearly indicated?</Criterion>
    <Criterion>Are dependencies between files evident from descriptions?</Criterion>
    <Criterion>Are there any missing files that would be needed for implementation?</Criterion>
  </Section>
  
  <Section name="LowLevelTasks">
    <Criterion>Does each task specify CREATE or UPDATE action clearly?</Criterion>
    <Criterion>Is there a logical sequence to the tasks?</Criterion>
    <Criterion>Is each task specific enough for implementation but not overly prescriptive?</Criterion>
    <Criterion>Do tasks collectively fulfill all the objectives?</Criterion>
    <Criterion>Is the level of detail consistent across all tasks?</Criterion>
    <Criterion>Are module dependencies and interactions addressed?</Criterion>
    <Criterion>Are edge cases and error handling mentioned where appropriate?</Criterion>
    <Criterion>Is there a clear mapping between tasks and the files listed in Contexts?</Criterion>
    <Criterion>Do tasks include appropriate validation, testing, or error handling?</Criterion>
    <Criterion>Are there any implementation gaps between tasks?</Criterion>
    <Criterion>Does each implementation point provide enough guidance without being too prescriptive?</Criterion>
  </Section>
  
  <Section name="OverallConsistency">
    <Criterion>Is terminology consistent throughout the spec?</Criterion>
    <Criterion>Do objectives, contexts, and tasks align coherently?</Criterion>
    <Criterion>Are there any contradictions between sections?</Criterion>
    <Criterion>Is the scope clearly defined and maintained throughout?</Criterion>
    <Criterion>Are there any unstated assumptions that should be made explicit?</Criterion>
    <Criterion>Is the testing strategy adequate for the complexity of implementation?</Criterion>
  </Section>
</ValidationCriteria>

<SPEC_PROMPT>
{prompt}
</SPEC_PROMPT>

<CODE_ANALYZE>
{code_analysis}
</CODE_ANALYZE>

Please analyze this specification and provide feedback in the following XML format:
```xml
<SpecificationReview>
  <Issues>
    <Issue>
      <Section>objectives|contexts|LowLevelTasks</Section>
      <Description>Detailed description of the issue</Description>
      <Location>Relevant section or line in the prompt</Location>
    </Issue>
    <!-- Additional Issue elements would be added here -->
  </Issues>

  <Suggestions>
    <Suggestion>
      <Description>Suggestion to improve the specification</Description>
      <Rationale>Why this suggestion would help</Rationale>
    </Suggestion>
    <!-- Additional Suggestion elements would be added here -->
  </Suggestions>

  <OverallAssessment>A brief overall assessment of the specification quality (1-5 scale, where 5 is excellent)</OverallAssessment>
  <IsUsable>true</IsUsable>
</SpecificationReview>
```
"""
