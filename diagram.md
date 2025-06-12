graph TD
    A[📱 PDF Upload] --> B[🔍 Duplicate Check]
    B -->|New File| C[💾 Store PDF]
    B -->|Duplicate| D[⚠️ Return Existing]
    
    C --> E[📄 PDF Text Extraction]
    E --> F[🏦 Bank Detection]
    F --> G[🇲🇽 Mexican Format Validation]
    
    G --> H{📋 Template Parser}
    H -->|95% Success| I[⚡ Regex Extraction]
    H -->|5% Fallback| J[🤖 LLM Extraction]
    
    I --> K[✅ Data Validation]
    J --> K
    
    K -->|Valid| L[🎯 Confidence Scoring]
    K -->|Invalid| M[❌ Mark as Failed]
    
    L --> N[💾 Store Statement Data]
    N --> O[🏷️ Mexican Categorization]
    
    O --> P{🔄 Categorization Strategy}
    P -->|Known Mexican Merchant| Q[⚡ Exact Match]
    P -->|Pattern Match| R[📊 Regex Rules]
    P -->|Unknown| S[🤖 LLM Categorize]
    
    Q --> T[💾 Store Transactions]
    R --> T
    S --> T
    
    T --> U[📈 Generate Analysis]
    U --> V[✅ Mark as Processed]
    
    M --> W[📝 Log Processing Error]
    W --> X[🔔 Notify User]
    
    V --> Y[📡 API Endpoints Ready]
    Y --> Z[📱 Frontend Display]
    
    %% Cost Optimization Highlights
    subgraph "💰 Cost Optimization"
        I1[Template Parsing: $0]
        I2[95% statements processed for FREE]
        I3[Only 5% use expensive LLM]
    end
    
    %% Template Extraction Details
    subgraph "🇲🇽 Mexican Template Parser"
        T1[Payment Info Extraction]
        T2[Transaction Table Parsing]
        T3[Balance Summary Extraction]
        T4[Customer Info Extraction]
    end
    
    I --> T1
    I --> T2
    I --> T3
    I --> T4
    
    %% Mexican Regulation Compliance
    subgraph "📜 CONDUSEF Regulation Patterns"
        R1["TU PAGO REQUERIDO ESTE PERIODO"]
        R2["DESGLOSE DE MOVIMIENTOS"]
        R3["DD-MMM-YYYY Date Format"]
        R4["$X,XXX.XX Amount Format"]
    end
    
    T1 --> R1
    T2 --> R2
    T3 --> R3
    T4 --> R4
    
    %% Database Storage
    subgraph "💾 PostgreSQL Storage"
        DB1[(BankStatement)]
        DB2[(Transaction)]
        DB3[(Analysis)]
        DB4[(ProcessingLog)]
    end
    
    N --> DB1
    T --> DB2
    U --> DB3
    W --> DB4