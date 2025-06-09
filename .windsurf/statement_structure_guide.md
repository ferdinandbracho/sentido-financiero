# Mexican Credit Card Statement Structure Guide for AI Scraping

## Overview
This guide is based on the official CONDUSEF regulation that standardizes all Mexican credit card statements. Every bank must follow this exact format, making it possible to create a universal scraper.

## Document Structure

### Page 0 (Optional)
- **Purpose**: Marketing/promotional content
- **Extractable Data**: Mailing address information only
- **AI Search Strategy**: Look for address patterns, ignore promotional content

### Page 1 (Primary Information Page)

#### Section 1: Bank Logo
- **Location**: Top left corner of every page
- **Search Pattern**: Image or text logo identification

#### Section 2: Page Numbers
- **Format**: "Página [X] de [Y]"
- **Location**: Top right corner
- **Search Pattern**: Regex pattern `Página \d+ de \d+`

#### Section 3: Mailing Data Section
Contains:
- **Customer Name**: Full name of primary cardholder
- **Mailing Address**: Complete address for statement delivery
- **Search Patterns**: 
  - Name: First text block after logo
  - Address: Multi-line address format with postal code

#### Section 4: Product Identification
Contains:
- **Card Type/Category**: e.g., "Tarjeta Clásica", "Tarjeta Oro", "Tarjeta Platino"
- **Card/Account Number**: 16-digit number (may be partially masked)
- **RFC**: Tax identification number
- **Optional Fields**:
  - Branch ("Sucursal")
  - Customer ID ("Número de cliente")
  - Barcode/QR code
  - CLABE (bank account code)

#### Section 5: "TU PAGO REQUERIDO ESTE PERIODO" (Payment Required This Period)
**Critical Payment Information**:
- **Period**: Statement period dates
- **Cut-off Date**: "Fecha de corte"
- **Days in Period**: "Número de días en el periodo"
- **Payment Due Date**: "Fecha límite de pago" (BOLD, 10pt Arial minimum)
- **Pay to Avoid Interest**: "Pago para no generar intereses" (BOLD)
- **Minimum Payment + Installments**: "Pago mínimo + compras y cargos diferidos a meses" (BOLD)
- **Minimum Payment**: "Pago mínimo" (BOLD)

#### Section 6: Payment Scenarios Table
Table: "CUÁNTO PAGARÍAS POR TUS COMPRAS REGULARES (NO A MESES)"
- **Columns**:
  1. Payment amount scenarios (minimum, 2x minimum, 5x minimum, full payment)
  2. Months to pay off ("terminarías de pagar en")
  3. Total interest paid ("y pagarías de intereses")

#### Section 7: Summary of Charges and Credits
Table: "RESUMEN DE CARGOS Y ABONOS DEL PERIODO"
- **Previous Balance**: "Adeudo del periodo anterior" (BOLD)
- **Regular Charges**: "Cargos regulares (no a meses)"
- **Installment Purchases**: "Cargos y compras a meses (capital)"
- **Interest Amount**: "Monto de intereses"
- **Commission Amount**: "Monto de comisiones"
- **VAT on Interest/Commissions**: "IVA de intereses y comisiones"
- **Payments and Credits**: "Pagos y abonos" (BOLD, negative amount)
- **Pay to Avoid Interest**: "PAGO PARA NO GENERAR INTERESES" (BOLD)

#### Section 8: Annual Cost Indicators
Table: "INDICADORES DEL COSTO ANUAL DE LA TARJETA"
- **Interest Paid Last 12 Months**: "Monto de intereses pagados en los últimos 12 meses"
- **Total Commissions Last 12 Months**: "Monto de comisiones totales pagadas en los últimos 12 meses"
- **Annual/Admin Fees Last 12 Months**: "Monto de anualidad o comisiones por administración"

#### Section 9: Key Rates
- **CAT**: Annual Total Cost percentage (BOLD)
- **Annual Interest Rate**: "TASA DE INTERÉS ANUAL ORDINARIA [FIJA O VARIABLE]" (BOLD)

#### Section 10: Comparison Links
- URLs for rate comparison websites
- Standard URLs: condusef.gob.mx and banxico.org.mx

#### Section 11: Important Messages
- **Section**: "MENSAJES IMPORTANTES"
- **Content**: Account modifications, credit changes, etc.
- **Max**: 700 characters

#### Section 12: Credit Usage Level
Table: "NIVEL DE USO DE TU TARJETA"
- **Regular Charges Balance**: "Saldo cargos regulares"
- **Installment Balance**: "Saldo cargos a meses"
- **Total Debt**: "Saldo deudor total" (BOLD)
- **Credit Limit**: "Límite de crédito"
- **Available Credit**: "Crédito disponible"
- **Optional**: Specific credit limits for cash advances, balance transfers

### Page 2+ (Transaction Details and Additional Information)

#### Section 15: Account Number (Repeated)
- **Format**: Same as Section 4, may appear on subsequent pages

#### Section 16: Additional Credit Lines (Optional)
Table: "INFORMACIÓN DE OTRAS LÍNEAS DE CRÉDITO"
Contains details of promotional or additional credit lines if applicable.

#### Section 17: Additional Messages
- **Section**: "MENSAJES ADICIONALES"
- **Max Size**: 1/4 page
- **Content**: Additional important notices

#### Section 18: Benefits Programs (Optional)
- **Section**: "PROGRAMAS DE BENEFICIOS DE LA TARJETA"
- **Content**: Points, miles, cashback programs
- **Max Size**: 1/4 page

#### Section 19: Interest Calculation Details
Table: "SALDO SOBRE EL QUE SE CALCULARON LOS INTERESES DEL PERIODO"
- **Columns**:
  1. Interest type
  2. Base amount for calculation
  3. Days in period
  4. Applied interest rate (BOLD)
  5. Interest amount

#### Section 20: Last Payment Distribution
Table: "DISTRIBUCIÓN DE TU ÚLTIMO PAGO"
Shows how the last payment was allocated across:
- Payments and credits
- Regular purchases
- Installment purchases (no interest)
- Installment purchases (with interest)
- Interest and commissions
- VAT
- Favorable balance

#### Section 21: Free Use Section (Optional)
- **Purpose**: Additional bank information or promotions
- **Max Size**: 1/3 page

#### Section 22: TRANSACTION DETAILS (Most Important for Scraping)
**Section**: "DESGLOSE DE MOVIMIENTOS"

##### Subsection A: No-Interest Installments
**Table**: "COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES"
**Format**: Separate table for main card and each additional card
**Columns**:
1. **Operation Date**: "Fecha de la operación" (DD-MMM-YYYY)
2. **Description**: "Descripción" (includes merchant, RFC if available, foreign currency details)
3. **Original Amount**: "Monto original"
4. **Pending Balance**: "Saldo pendiente"
5. **Required Payment**: "Pago requerido"
6. **Payment Number**: "Núm. de pago"
7. **Applied Rate**: "Tasa de interés aplicable" (0.0% or NA)

##### Subsection B: Interest-Bearing Installments
**Table**: "COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES"
**Format**: Separate table for main card and each additional card
**Columns**:
1. **Operation Date**: "Fecha de la operación"
2. **Description**: "Descripción"
3. **Original Amount**: "Monto original"
4. **Pending Balance**: "Saldo pendiente"
5. **Period Interest**: "Intereses del periodo"
6. **VAT on Interest**: "IVA de intereses del periodo"
7. **Required Payment**: "Pago requerido"
8. **Payment Number**: "Núm. de pago"
9. **Applied Rate**: "Tasa de interés aplicable" (BOLD)

##### Subsection C: Regular Transactions
**Table**: "CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)"
**Format**: Separate table for main card and each additional card
**Columns**:
1. **Operation Date**: "Fecha de la operación"
2. **Charge Date**: "Fecha de cargo"
3. **Movement Description**: "Descripción del movimiento"
4. **Amount**: "Monto" (positive for charges, negative for credits)

**Important Notes for Transaction Scraping**:
- Foreign currency transactions include original amount, exchange rate, and converted amount
- Virtual/digital card transactions include card type identification
- Credits/payments specify the payment method (cash, check, transfer, etc.)
- All amounts in Mexican Pesos (MXN)
- Chronological order (oldest to newest)

#### Section 23: Unrecognized Charges
**Table**: "CARGOS NO RECONOCIDOS"
**Columns**:
1. **Operation Date**: "Fecha de la operación"
2. **Report Receipt Date**: "Fecha de recepción del reporte"
3. **Charge Description**: "Descripción del cargo"
4. **Status**: "Estatus" (Pending, Concluded-Procedent, Concluded-Improcedent)
5. **Report Folio**: "Folio del reporte"
6. **Amount**: "Monto"

#### Section 24: Customer Service
**Table**: "ATENCIÓN DE QUEJAS"
Standard CONDUSEF complaint information and contact details.

#### Section 25: Debt Restructuring (Optional)
**Section**: "REESTRUCTURA DE TU DEUDA"
Only appears if debt restructuring is active.

#### Section 26: Explanatory Notes
**Table**: "NOTAS ACLARATORIAS"
Numbered explanations for superscript references throughout the document.

#### Section 27: Glossary
**Table**: "GLOSARIO DE TÉRMINOS Y ABREVIATURAS"
Alphabetical list of terms and abbreviations used in the statement.

## AI Scraping Strategy

### Data Extraction Priority
1. **Account Information** (Page 1, Sections 3-4)
2. **Payment Requirements** (Page 1, Section 5)
3. **Balance Summary** (Page 1, Sections 7, 12)
4. **All Transactions** (Page 2+, Section 22)
5. **Interest and Fees** (Page 1, Sections 8-9)

### Search Patterns for Mistral Model

#### Account Identification
```
Pattern: "Número de [tarjeta|cuenta|contrato]"
Extract: 16-digit number (may be partially masked with X)
Location: Page 1, Section 4
```

#### Customer Information
```
Pattern: First text block after bank logo
Extract: Full name and complete address
Location: Page 1, Section 3
```

#### Key Financial Data
```
Patterns:
- "Límite de crédito": Credit limit amount
- "Crédito disponible": Available credit
- "Saldo deudor total": Total debt (BOLD formatting)
- "Pago mínimo": Minimum payment (BOLD formatting)
- "Fecha límite de pago": Due date (BOLD formatting)
```

#### Transaction Tables
```
Table Headers to Identify:
- "COMPRAS Y CARGOS DIFERIDOS A MESES SIN INTERESES"
- "COMPRAS Y CARGOS DIFERIDOS A MESES CON INTERESES"  
- "CARGOS, ABONOS Y COMPRAS REGULARES (NO A MESES)"

Column Extraction Order:
1. Date (always first column)
2. Description (always second column) 
3. Amount (varies by table type)
4. Additional fields per table specification
```

#### Date Format Recognition
```
Standard Format: DD-MMM-YYYY
Examples: "15-ENE-2023", "28-DIC-2022"
Spanish Month Abbreviations: ENE, FEB, MAR, ABR, MAY, JUN, JUL, AGO, SEP, OCT, NOV, DIC
```

#### Amount Format Recognition
```
Format: Mexican Peso amounts with comma as thousands separator
Examples: "$1,500.00", "$25,000.50"
Negative amounts (credits): Typically in parentheses or with minus sign
```

### Error Handling Considerations
- Some sections may be optional and not present
- Table structures are standardized but content varies
- Multiple cards (additional cards) create duplicate table structures
- Foreign currency transactions have extended description formats
- Masked account numbers require partial matching

### Validation Checkpoints
- Total transactions should reconcile with summary amounts
- Payment distribution should equal total payments
- Interest calculations should match detail tables
- All mandatory sections must be present (per regulation)

This structure is legally mandated for ALL Mexican credit card statements, ensuring consistency across all banks and financial institutions.