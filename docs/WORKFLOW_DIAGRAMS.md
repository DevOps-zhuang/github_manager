# AI-Assisted Data Normalization Workflow Diagram

## User Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                      START                                  │
│              User has raw CSV file                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Run AI Normalizer CLI                             │
│  $ python -m invitation.ai_normalizer_cli input.csv         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: CSV Analysis                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Display row/column counts                         │   │
│  │ • Show column names                                 │   │
│  │ • Show null value counts                            │   │
│  │ • Preview sample rows                               │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Collect Transformation Rules                      │
│  User describes transformations in natural language:        │
│  • "Rename EmailAddress to Mail"                           │
│  • "Filter rows where Status equals Active"                │
│  • "Merge FirstName and LastName with space"               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: LLM Processing                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ LLM parses natural language                         │   │
│  │ ├─ Understands intent                               │   │
│  │ ├─ Maps to transformation types                     │   │
│  │ └─ Extracts parameters                              │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────┴───────────┐
         │  Ambiguous?           │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
        YES                      NO
         │                        │
         ▼                        ▼
┌────────────────────┐   ┌────────────────────────────────────┐
│ Show clarification │   │  STEP 5: Display Parsed Rules      │
│ questions          │   │  • Show transformation type         │
│ Ask user to retry  │   │  • Show parameters                  │
└────────┬───────────┘   │  • Ask for confirmation             │
         │               └───────┬────────────────────────────┘
         │                       │
         └───────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: Generate Python Code                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ LLM generates pandas transformation code            │   │
│  │ def transform_data(df):                             │   │
│  │     result = df.copy()                              │   │
│  │     result = result.rename(columns={...})           │   │
│  │     result = result[condition]                      │   │
│  │     return result                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 7: Code Validation                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Check for dangerous operations:                     │   │
│  │ ✗ eval(), exec()                                    │   │
│  │ ✗ file I/O (open, read, write)                     │   │
│  │ ✗ system calls (os.system, subprocess)             │   │
│  │ ✓ Only pandas operations allowed                   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────┴───────────┐
         │  Code safe?           │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
        NO                       YES
         │                        │
         ▼                        ▼
┌────────────────────┐   ┌────────────────────────────────────┐
│ Show validation    │   │  STEP 8: Preview Code              │
│ errors             │   │  Display generated code             │
│ Abort              │   │  Ask user to confirm execution      │
└────────────────────┘   └───────┬────────────────────────────┘
                                 │
                                 ▼
         ┌───────────────────────┴───────────┐
         │  User confirms?                   │
         └───────────┬───────────────────────┘
                     │
         ┌───────────┴───────────┐
        NO                       YES
         │                        │
         ▼                        ▼
┌────────────────────┐   ┌────────────────────────────────────┐
│ Cancel operation   │   │  STEP 9: Execute Transformation    │
│ Exit               │   │  ┌────────────────────────────────┐│
└────────────────────┘   │  │ Run code in sandbox            ││
                         │  │ • Limited namespace (pandas)    ││
                         │  │ • No external access            ││
                         │  │ • Error handling                ││
                         │  └────────────────────────────────┘│
                         └───────┬────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 10: Generate Outputs                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ output_clean.csv:                                   │   │
│  │   • Transformed data                                │   │
│  │   • Ready for invitation pipeline                   │   │
│  │                                                      │   │
│  │ output_report.csv:                                  │   │
│  │   • Row count changes                               │   │
│  │   • Column additions/removals                       │   │
│  │   • Applied rules summary                           │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 11: Display Results                                   │
│  • Show success/failure status                              │
│  • Display output file paths                                │
│  • Show row counts                                          │
│  • Preview transformed data                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      END                                    │
│       Files ready for invitation pipeline                   │
└─────────────────────────────────────────────────────────────┘
```

## System Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                         User Input                                │
│              Natural Language Transformation Rules                 │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                      CLI Layer                                    │
│                ai_normalizer_cli.py                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ • Interactive prompts                                      │  │
│  │ • File path management                                     │  │
│  │ • User confirmations                                       │  │
│  │ • Result display                                           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Service Layer                                  │
│              ai_normalization_service.py                          │
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────────────────┐  │
│  │   LLMService     │         │  AINormalizationService      │  │
│  │                  │         │                              │  │
│  │ • API client     │◄────────┤  • CSV analysis              │  │
│  │ • Prompt build   │         │  • Rule parsing              │  │
│  │ • Response parse │         │  • Code validation           │  │
│  │ • Code gen       │         │  • Safe execution            │  │
│  └──────────────────┘         │  • Report generation         │  │
│                               └──────────────────────────────┘  │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                   External Services                               │
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────────────────┐   │
│  │   OpenAI API    │         │         pandas               │   │
│  │   (GPT-4)       │         │    (Data Processing)         │   │
│  └─────────────────┘         └──────────────────────────────┘   │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Output Files                                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  input_clean.csv           input_report.csv                 │ │
│  │  ─────────────────         ────────────────                 │ │
│  │  Mail,Organization,Team    Metric,Value,Details             │ │
│  │  user@example.com,...      Original Row Count,100,...       │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Raw CSV Input
     │
     ├─→ pandas.read_csv() ─→ DataFrame
     │
     ├─→ CSV Analysis ─→ Metadata (rows, columns, types, nulls)
     │                    │
     │                    └─→ Display to User
     │
     ├─→ User Input (Natural Language Rules)
     │         │
     │         └─→ LLM Parsing
     │                  │
     │                  ├─→ Structured TransformationRules
     │                  │        │
     │                  │        └─→ Display to User
     │                  │
     │                  └─→ Clarifications? ─→ Ask User to Retry
     │
     ├─→ LLM Code Generation
     │         │
     │         └─→ Python Code (def transform_data(...))
     │                  │
     │                  ├─→ Validation (Safety Check)
     │                  │        │
     │                  │        ├─→ Pass ─→ Show User
     │                  │        └─→ Fail ─→ Abort
     │                  │
     │                  └─→ User Confirmation
     │                           │
     │                           ├─→ Accept ─→ Execute
     │                           └─→ Reject ─→ Cancel
     │
     ├─→ Sandboxed Execution
     │         │
     │         └─→ Transformed DataFrame
     │                  │
     │                  ├─→ Generate Report (before/after comparison)
     │                  │
     │                  └─→ Write Output Files
     │                           │
     │                           ├─→ _clean.csv (transformed data)
     │                           └─→ _report.csv (audit trail)
     │
     └─→ Success/Failure Feedback ─→ Display to User
```

## Safety Layers

```
User Input
    │
    ▼
┌──────────────────────────────────┐
│ Layer 1: LLM Prompt Engineering  │
│ • Explicit instructions          │
│ • Safe function signature        │
│ • No dangerous imports           │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Layer 2: Code Validation         │
│ • Regex pattern matching         │
│ • Block: eval, exec, open, etc.  │
│ • Require specific function sig  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Layer 3: User Review             │
│ • Display full code              │
│ • Require explicit confirmation  │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Layer 4: Sandboxed Execution     │
│ • Limited namespace              │
│ • Only pandas available          │
│ • No file/network access         │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Layer 5: Error Handling          │
│ • Try-catch all operations       │
│ • Detailed error messages        │
│ • Safe failure modes             │
└──────────────────────────────────┘
```

## Integration with Existing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                   BEFORE (Manual)                           │
│                                                             │
│  1. Receive raw CSV                                         │
│  2. Analyze structure                                       │
│  3. Write Python normalizer class                           │
│  4. Test normalizer                                         │
│  5. Register in customize/                                  │
│  6. Run: python -m invitation.pipeline enterprise raw.csv   │
│  7. Run: python -m invitation.inviter normalized.csv        │
│                                                             │
│  Time: Hours to days (requires programming)                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   AFTER (AI-Assisted)                       │
│                                                             │
│  1. Receive raw CSV                                         │
│  2. Run: python -m invitation.ai_normalizer_cli raw.csv     │
│  3. Describe transformations in plain English               │
│  4. Review and confirm code                                 │
│  5. Get clean.csv and report.csv automatically              │
│  6. Run: python -m invitation.inviter clean.csv             │
│                                                             │
│  Time: Minutes (no programming required)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Use Cases                                │
│                                                             │
│  AI Normalization:                                          │
│  • One-off imports                                          │
│  • Exploring new data formats                               │
│  • Quick prototyping                                        │
│  • Non-technical users                                      │
│                                                             │
│  Traditional Pipeline (customize/):                         │
│  • Regular, repeated imports                                │
│  • Complex business logic                                   │
│  • Production workflows                                     │
│  • Version-controlled transformations                       │
└─────────────────────────────────────────────────────────────┘
```
