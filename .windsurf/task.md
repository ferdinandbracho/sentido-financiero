# StatementSense Project Tasks & Roadmap

## Project Overview
StatementSense is a full-stack application that uses AI to automatically categorize and analyze bank statement transactions. This file serves as the central planning and task tracking document for the project.

## How to Use This File
1. Keep tasks organized by status (Todo, In Progress, Done)
2. Add new tasks under the appropriate section
3. Move tasks between sections as they progress
4. Include relevant details like priority, assignee, and due dates
5. Update this file regularly to reflect current status

## Current Focus
- [x] ~~Improve transaction categorization accuracy~~ → Replacing with Mistral 7B Implementation
- [x] ~~Optimize PDF parsing performance~~ → Implementing universal AI-based PDF parser
- [ ] Enhance the user interface for better data visualization

## AI Model Migration Project (Ollama → Mistral 7B) 

### Phase 1: Infrastructure Setup (Due: TBD)
- [x] Create Docker Compose configuration for Mistral 7B
  - [x] Configure memory and CPU requirements (initial settings applied)
  - [x] Set up volume mapping for model persistence (verified)
  - [x] Configure networking between services (verified)
- [ ] Create model download and initialization scripts
- [x] Configure API endpoints for Mistral 7B inference (client-side integration in SmartCategorizer complete)
- [ ] Test Docker Compose deployment locally
- [ ] Document Docker Compose setup and requirements

### Phase 2: Universal PDF Parser Design (Due: TBD)

> **CRITICAL REFERENCE**: All PDF parsing implementation MUST reference the standardized structure detailed in `.windsurf/statement_structure_guide.md` which follows the official CONDUSEF regulations for Mexican credit card statements.

- [/] Design universal document structure extraction approach based on CONDUSEF standards
  - [x] Create document type classifier (bank statement vs. other)
  - [/] Leverage standardized section numbering (Sections 1-25) from the structure guide
  - [/] Create document structure detector for key sections:
    - [x] Primary Information (Page 1, Sections 1-12)
    - [x] Transaction Details (Page 2+, Section 22)
    - [/] Summary and Payment Information (Section 5-7)
- [ ] Design prompt engineering strategies for Mistral 7B based on standardized formats
  - [ ] Create prompt templates for structured section identification from CONDUSEF guidelines
  - [ ] Design specialized transaction extraction prompts for each transaction table type:
    - [ ] No-Interest Installments ("COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES")
    - [ ] Interest-Bearing Installments ("COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES")
    - [ ] Regular Transactions ("CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)")
  - [ ] Design metadata extraction prompts for standardized fields (dates, account numbers, etc.)
  - [x] Create date format handler for Spanish month abbreviations (ENE, FEB, MAR, etc.)
- [/] Create evaluation framework for measuring extraction accuracy
  - [/] Define section-specific metrics for extraction accuracy
  - [/] Create test datasets with ground truth based on CONDUSEF sections
  - [/] Implement evaluation pipeline with section validation

### Phase 3: Implementation (Due: TBD)

> **CRITICAL REFERENCE**: Implementation must follow the standardized structure in `.windsurf/statement_structure_guide.md`

- [ ] Create Mistral 7B integration service
  - [x] Implement client wrapper for Mistral 7B API (within SmartCategorizer)
  - [ ] Create connection pooling and request management
  - [ ] Implement error handling and retry logic
  - [ ] Add logging and monitoring
- [ ] Implement universal PDF parser using Mistral 7B
  - [ ] Create document preprocessor for optimal text extraction
    - [ ] Implement table structure detection based on CONDUSEF section definitions
    - [ ] Develop text extraction with spatial awareness for tabular data
  - [ ] Implement structured section extraction following CONDUSEF standards
    - [ ] Primary info extraction (account numbers, dates, payment info)
    - [ ] Transaction tables extraction with column mapping
    - [ ] Summary fields extraction
  - [ ] Create transaction extraction pipeline
    - [ ] Implement separate extractors for each transaction table type
    - [ ] Handle date format conversion (Spanish → standard)
    - [ ] Process amounts with proper sign interpretation
  - [ ] Implement metadata extraction
    - [ ] Extract statement period and key dates
    - [ ] Identify card/account information
    - [ ] Extract payment requirements and deadlines
- [ ] Implement transaction categorization with Mistral 7B
  - [ ] Create enhanced prompt templates for transaction categorization
  - [ ] Implement confidence scoring mechanism
  - [ ] Design and implement fallback strategies for low-confidence predictions
  - [ ] Create specialized handling for standardized transaction descriptions

### Phase 4: Testing and Optimization (Due: TBD)

> **CRITICAL REFERENCE**: Testing must validate against the standardized structure in `.windsurf/statement_structure_guide.md`

- [ ] Create comprehensive test suite
  - [ ] Unit tests for all components
    - [ ] Test each CONDUSEF section extractor individually
    - [ ] Create specific tests for each transaction table type
    - [ ] Test Spanish date format handling
  - [ ] Integration tests for end-to-end pipeline
    - [ ] Test with sample statements from multiple Mexican banks
    - [ ] Validate against CONDUSEF regulatory requirements
  - [ ] Performance tests for throughput and latency
    - [ ] Benchmark extraction of each standardized section
- [ ] Optimize performance
  - [ ] Implement caching strategies
  - [ ] Optimize batch processing for multiple statements
  - [ ] Fine-tune prompt templates for better accuracy on Mexican financial terminology
  - [ ] Create specialized optimizations for the three transaction table types
- [ ] Implement monitoring and observability
  - [ ] Add performance metrics collection with section-specific extraction success rates
  - [ ] Create dashboards for model performance
  - [ ] Implement alerting for failures
  - [ ] Add validation checks against expected CONDUSEF structure

### Phase 5: Codebase Analysis and Cleanup (Due: TBD)

> **CRITICAL REFERENCE**: Cleanup must align with the standardized structure in `.windsurf/statement_structure_guide.md`

- [ ] Analyze entire codebase for obsolete components
  - [ ] Identify scripts and helpers specific to Ollama/Llama 3.2
  - [ ] Document dependencies to be removed
  - [ ] Mark bank-specific regex patterns that will be replaced by standardized AI extraction
    - [ ] Identify all patterns in `bank_transaction_patterns` and `bank_patterns` dictionaries
    - [ ] Document which CONDUSEF sections each pattern targets
- [ ] Clean up legacy code
  - [ ] Remove bank-specific regex patterns after AI validation against CONDUSEF standards
  - [ ] Clean up unused imports and dependencies
  - [ ] Remove deprecated API endpoints
  - [ ] Consolidate duplicate functionality across bank parsers
  - [ ] Remove hard-coded bank-specific extraction logic
- [ ] Refactor core services
  - [ ] Simplify PDF parser service architecture to align with CONDUSEF sections
  - [ ] Modernize categorization service to leverage Mistral 7B
  - [ ] Implement cleaner separation of concerns with standardized section processors
  - [ ] Create unified extraction pipeline based on document structure standards
- [ ] Code quality improvements
  - [ ] Add comprehensive docstrings referencing CONDUSEF section numbers
  - [ ] Standardize error handling with specific error types per section
  - [ ] Improve logging consistency with standardized section identifiers
  - [ ] Update type hints throughout codebase
  - [ ] Document section extraction confidence metrics

### Phase 6: Deployment and Documentation (Due: TBD)

> **CRITICAL REFERENCE**: Documentation must thoroughly explain the standardized structure in `.windsurf/statement_structure_guide.md`

- [ ] Update API endpoints
  - [ ] Ensure backward compatibility
  - [ ] Add new endpoints for enhanced features based on CONDUSEF section extraction
  - [ ] Update API documentation with references to standardized sections
- [ ] Create comprehensive documentation
  - [ ] Document the standardized extraction approach based on CONDUSEF regulations
  - [ ] Create a developer guide for maintaining the statement structure map
  - [ ] Document supported Mexican bank statement formats
  - [ ] Create troubleshooting guides for each section extraction
  - [ ] Document accuracy expectations for each transaction table type
  - [ ] Create section-by-section extraction verification guides
- [ ] Deploy to production
  - [ ] Create deployment script with proper configuration for Mistral 7B
  - [ ] Set up section-specific monitoring for extraction accuracy
  - [ ] Perform initial validation against the CONDUSEF regulatory standards
  - [ ] Create a validation dashboard for extraction accuracy metrics

## Todo

### High Priority
- [ ] Implement user authentication system
- [ ] Add support for more bank statement formats
- [ ] Create automated tests for core functionality

### Medium Priority
- [ ] Add data export functionality (CSV/Excel)
- [ ] Implement transaction search and filtering
- [ ] Add data visualization for spending patterns

### Low Priority
- [ ] Set up CI/CD pipeline
- [ ] Add dark mode support
- [ ] Implement multi-language support

## In Progress
- [ ] AI Model Migration (Ollama → Mistral 7B) and Universal PDF Parser (Assigned: Ferdinand)

## Completed
- [x] Initial project setup
- [x] Basic PDF parsing functionality
- [x] Transaction categorization with AI (Ollama/Llama 3.2 1B)

## Ideas for Future Updates
- Mobile app development
- Recurring transaction detection
- Budget tracking and alerts
- Integration with accounting software

## Last Updated
2025-06-07 - Phase 1 (Docker Compose for Ollama: resource config, volumes, networking) updated.
