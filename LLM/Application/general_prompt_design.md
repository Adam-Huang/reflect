# General prompt design
A prompt can be abstracted into three main components: Basic Attributes(or regard as Inputs) addressing the questions of who you are and what materials you have, Goals addressing where you want to go and what you want to achieve, and Constraints(or regard as Standards) addressing how to get there and what to pay attention to.

Every action we take can be abstracted as follows:
- What do I have,
- What do I want to achieve,
- How do I achieve it.

## Basic Attributes(Inputs from the Objective World)
### Solving the Agent's Positioning Problem(e.g. Who are you?)
- `As a professional database expert, your name is {subject}`
- `作为一个数据库专家，你的名字是{subject}。`

When writing prompts, telling the model 'Your are xxx' serves serveral purposes:
1. **Defining Role and Identity**: By telling the model 'Your are xxx' it can clearfy understand its role and identity in the conversation. This helps the model generate responses that are more aligned with expectatioins. For example, if you tell it 'you are a professional software engineer, it will respond from an engineer's perspective and tone.
2. **Providing Contextual Information**: In complex tasks, simple instructions may not be enough for the model to understand the full context and requirement. Defining its identity provides more contextual information, helping the model better understand the problem and generate appropriate responses.
3. **Guiding Output style**: Different identity imply different tones, word choices, and expressions. Telling the model 'you are xxx' can guide it to generate text styles that match that identity, making the output more natural and aligned with the needs.
4. **Enhancing Controllability**: When the model plays a specific role, its behavior and output become more controllable and predictable. This helps avoid some undesirable reponses or behaviors.

In summary, telling the model 'your are xxx' when writing prompts helps it better understand task requirements, generate expected outputs, and enhance the controllability of the conversation. This is an important technique in prompt engineering.

### Supplementing Domain-Specific Knowledge (What do you have?)
- Description of the database
- Example

## Goals (Desired Output)
Once the functionality is determined, the goal is not likely to change much. 

Possible changes involve splitting a complex task when it is determined that the LLM cannot reliably solve the problem, distributing it to different models. For example, in the development of an NL2SQL application, a decision tree might be uesd to guide the process:
Is this a question I can answer using SQL with known database?
- If yes, 
  - Is the task complex and need splitting or can it be handled as a single task?
    - If it needs splitting, break down the task into smaller queries or components that can be managed separately.
    - If it can be handled as a single task, proceed with generating the SQL query.
  - What kind of chart should be used to display the data?
    - Determine the appropriate visualization (e.g. bar chart, line chart, pie chart) based on the data type and user requirements.
- If no, 
  - Determine if the question requires additional processing:
    - Engage the user for clarification or additional information.
    - Rephrase or refine the question to better understand the requirements.
  - Does it fall outside the scope of SQL capabilities?
    - If it does, consider using alternative methods or models to address the question.

When an LLM is unable to resolve a complex task, such as navigating a detailed decision tree, we can break it down into several simpler tasks. For example:

1. **Data Retrieval Task**: First, identify and extract necessary data from the database. This could involve querying specific tables to gather all relevant information that might be needed for analysis.
2. **Data Analysis Task**: Once the data is retrieved, perform a series of smaller analytical queries to gain insights. This could include calculating averages, identifying trends, or detecting anomalies in the data.
3. **Visualization Task**: Based on the insights gathered, choose the appropriate type of visualization. For instance, if trends over time are identified, a line chart might be suitable. Alternatively, if comparing categories, a bar chart could be more effective.
4. **User Interaction Task**: If any part of the process requires clarification or additional input, engage the user. This might involve asking targeted questions to refine the requirements or adjust the focus of the analysis.
5. **Alternative Method Task**: For aspects of the task that fall outside the capabilities of SQL or standard data processing, consider using other models or machine learning techniques. This might involve using natural language processing for text analysis or employing predictive models for forecasting.

By breaking down the complex tasks into manageable components, each can be addressed with the appropriate tools and techniques, thereby improving the overall effectiveness and reliability of the solution.

### Overall Goal
This is a description that an action's goal, e.g.
- NL2SQL: Your job is to write executable SQL with BASE_SQL, based on user questions with the knowledge from the database.
- 你的工作是基于用户的问题和数据库写出一个可执行的SQL，以支持查询出客户问题中的数据。

### Current Goal
- Solving user specific question, e.g. How has chewing gum performed in the past 3 month?

## Contraints (also known as Standard, Notes)
### General Constraints
For Example, the format of the answer, hoping it can be parsed by subsequent programs.

#Note
- In terms of content, your answer should be a step-by-step explanation of the refined question, including a deep understanding of user requirements and a SQL
- In trems of format, your answer should contain three fields: Overview, StepByStep, and SQL. Please strictly follow the format in the below "Example"

We call this note is Genernal Constraints, because it apply in all of prompt of the actions.

### Specific Constraints
For example:
- Found the relevant strings, pay attention that this xxx found, in our xxx database, we storage as xxx.
- Similar question, user have previously commented on xxx, which needs attentions.

# General DB Maintenance and Management Tool
Based on the above abstraction of prompts, develop a tool for the daily maintenance and update of rules and corpora. There are vector corpora and scalar corpora. It can also be seen as a one-to-one corpus.

## Scalar Corpus Content
1. Domain-specific corpus, which is unvecotrized standard corpus, usually used for diect concatenatioin into the prompt, in the form of `Key: Value`. 
```json
{
    "project": "", 
    "name": "",        // corpora name
    "version": 3,      // corpora version
    "type": "private", // "trigger", "vector"
    "value": "xxx"     // corpora
}
```

2. Trigger Corpus, usually triggered by specific strings in the input(e.g. query), this mapping is usually many-to-one, of course, the "one" may be a fixed rule or a fixed pattern, For example:
  1. `['上个月', '上月', 'last month']` etc., will trigger a rule: 'The user's question involves last month, please pay attention to the combination of `month_string` and `kpi_duration`, do not have `month_string` as last month while the `kpi_duration` is still selected as LM'
  2. `['上海', '申城']` etc., will trigger a pattern: 'String {trigger} found, please note that in the `geo_spatial` field, it corresponds to `Greater_SH`'
here is the storage of Trigger Corpus.
```json
{
    "project": "",
    "name": "",
    "version": 3,
    "type": "trigger", // "private", "vector"
    "value": [
        {
            "triggers": ["上海", "申城"],
            "pattern": "String {trigger} found, please note that in the `geo_spatial` field, it corresponds to `Greater_SH`",
            "alarm": "xxx"
        }
    ]
}
```

3. Vector Database Corpus, this part is a backup of the vector database, used to in scenarios such as updating certain data in the Vector DB, switching Vector DB, switching embedding models.
```json
{
    "project": "",
    "name": "",
    "version": 3,
    "type": "vector", // "private", "trigger"
    "value": {}, // 如下
    "vector_index_column": "query",
}
```
