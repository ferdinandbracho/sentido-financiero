import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ExtractionEvaluationFramework:
    """
    Framework for evaluating the accuracy of PDF data extraction 
    against ground truth data, based on CONDUSEF sections.
    """

    def __init__(self, ground_truth_data: List[Dict[str, Any]]):
        """
        Initializes the framework with ground truth data.
        Ground truth data should be a list of dictionaries, where each dictionary
        represents a statement and its expected extracted values.
        """
        self.ground_truth_data = ground_truth_data
        self.section_metrics = {}

    def _compare_values(self, extracted_value: Any, ground_truth_value: Any) -> bool:
        """Compares an extracted value with a ground truth value. Handles common types."""
        if type(extracted_value) != type(ground_truth_value) and ground_truth_value is not None:
            # Attempt type conversion for common cases (e.g. str to float for amounts)
            try:
                if isinstance(ground_truth_value, float) and isinstance(extracted_value, (str, int)):
                    extracted_value = float(str(extracted_value).replace('$', '').replace(',', ''))
                elif isinstance(ground_truth_value, int) and isinstance(extracted_value, (str, float)):
                    extracted_value = int(float(str(extracted_value).replace('$', '').replace(',', '')))
                # Add more type conversions as needed (e.g., dates)
            except ValueError:
                return False # Cannot convert for comparison
        
        # Normalize strings for comparison (lowercase, strip whitespace)
        if isinstance(extracted_value, str) and isinstance(ground_truth_value, str):
            return extracted_value.lower().strip() == ground_truth_value.lower().strip()
        
        return extracted_value == ground_truth_value

    def evaluate_section(self, section_name: str, extracted_data: Dict[str, Any], ground_truth_section: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a specific section of the extracted data against ground truth.
        Returns a dictionary with accuracy metrics for the section.
        """
        correct_fields = 0
        total_fields = len(ground_truth_section)
        field_accuracies = {}

        if total_fields == 0:
            return {"accuracy": 1.0, "correct_fields": 0, "total_fields": 0, "field_accuracies": {}}

        for field, gt_value in ground_truth_section.items():
            extracted_value = extracted_data.get(field)
            if self._compare_values(extracted_value, gt_value):
                correct_fields += 1
                field_accuracies[field] = {"extracted": extracted_value, "ground_truth": gt_value, "match": True}
            else:
                field_accuracies[field] = {"extracted": extracted_value, "ground_truth": gt_value, "match": False}
                logger.debug(f"Mismatch in section '{section_name}', field '{field}': Extracted='{extracted_value}', GroundTruth='{gt_value}'")

        accuracy = correct_fields / total_fields if total_fields > 0 else 0.0
        self.section_metrics[section_name] = accuracy
        
        return {
            "accuracy": accuracy,
            "correct_fields": correct_fields,
            "total_fields": total_fields,
            "field_accuracies": field_accuracies
        }

    def evaluate_transactions(self, extracted_transactions: List[Dict[str, Any]], ground_truth_transactions: List[Dict[str, Any]], transaction_type: str) -> Dict[str, Any]:
        """
        Evaluates extracted transactions against ground truth transactions.
        This is a complex task. This implementation uses a simplified matching approach.
        A more robust approach would involve fuzzy matching or record linkage techniques.
        """
        # Simplified: Count based matching, then field-level for matched items.
        # Assumes order might not be guaranteed, but tries to find best matches.
        # This is a placeholder for a more sophisticated transaction matching logic.
        
        num_extracted = len(extracted_transactions)
        num_ground_truth = len(ground_truth_transactions)
        
        # For now, just check counts and maybe first/last transaction details if counts match.
        # A proper evaluation requires matching individual transactions.
        count_accuracy = 0
        if num_ground_truth > 0:
            count_accuracy = min(num_extracted, num_ground_truth) / num_ground_truth if num_extracted <= num_ground_truth else num_ground_truth / num_extracted
        elif num_extracted == 0 and num_ground_truth == 0:
            count_accuracy = 1.0

        # Detailed field matching for transactions is complex due to matching problem.
        # Placeholder: If counts match, compare first transaction as a sample.
        sample_field_accuracy = 0
        matched_transactions = 0
        
        # TODO: Implement a more robust transaction matching algorithm (e.g., based on date, amount, description similarity)
        # For now, we'll do a naive field-by-field comparison if counts are similar
        # This is a very basic approach and will not be robust.
        
        # Simple matching based on trying to find an exact match for each ground truth transaction
        # This is computationally intensive for large lists and not very fault-tolerant.
        gt_matched_flags = [False] * num_ground_truth
        
        for i, gt_tx in enumerate(ground_truth_transactions):
            for j, ex_tx in enumerate(extracted_transactions):
                # Attempt to match based on key fields (e.g., date, amount, part of description)
                # This is highly simplified.
                date_match = self._compare_values(ex_tx.get('operation_date'), gt_tx.get('operation_date'))
                amount_match = self._compare_values(ex_tx.get('amount') or ex_tx.get('required_payment'), gt_tx.get('amount') or gt_tx.get('required_payment'))
                # Simple description check (e.g. first N chars or keyword)
                desc_match = False
                if isinstance(ex_tx.get('description'), str) and isinstance(gt_tx.get('description'), str):
                    if ex_tx.get('description').lower().strip()[:10] == gt_tx.get('description').lower().strip()[:10]:
                        desc_match = True
                
                if date_match and amount_match and desc_match and not gt_matched_flags[i]:
                    matched_transactions += 1
                    gt_matched_flags[i] = True
                    # Could add field-level accuracy for matched transactions here
                    break # Assume one-to-one match for simplicity
        
        precision = matched_transactions / num_extracted if num_extracted > 0 else 0
        recall = matched_transactions / num_ground_truth if num_ground_truth > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        self.section_metrics[f"{transaction_type}_transactions_f1"] = f1_score

        return {
            "count_accuracy": count_accuracy,
            "num_extracted": num_extracted,
            "num_ground_truth": num_ground_truth,
            "matched_transactions": matched_transactions,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "notes": "Transaction matching is simplified. F1 score is based on naive matching."
        }

    def run_evaluation(self, extracted_full_data: Dict[str, Any], ground_truth_id: Any) -> Dict[str, Any]:
        """
        Runs the full evaluation pipeline for a single extracted document 
        against its corresponding ground truth.
        """
        # Find the corresponding ground truth data
        current_ground_truth = None
        for gt_item in self.ground_truth_data:
            # Assuming ground_truth_id matches a field like 'statement_id' or 'filename' in ground_truth_data
            if gt_item.get('id') == ground_truth_id or gt_item.get('filename') == ground_truth_id:
                current_ground_truth = gt_item
                break
        
        if not current_ground_truth:
            logger.error(f"No ground truth data found for ID: {ground_truth_id}")
            return {"error": "Ground truth not found"}

        overall_results = {
            "ground_truth_id": ground_truth_id,
            "sections": {},
            "transactions_evaluation": {}
        }

        # Evaluate Primary Information (CONDUSEF Sections 1-12, typically Page 1)
        # Assuming ground truth has a 'primary_info' key similar to extracted_data
        if 'primary_info' in current_ground_truth and 'primary_info' in extracted_full_data:
            overall_results["sections"]["primary_information"] = self.evaluate_section(
                "primary_information",
                extracted_full_data['primary_info'],
                current_ground_truth['primary_info']
            )
        
        # Evaluate Summary and Payment Information (CONDUSEF Sections 5-7)
        if 'summary_info' in current_ground_truth and 'summary_info' in extracted_full_data:
            overall_results["sections"]["summary_and_payment_info"] = self.evaluate_section(
                "summary_and_payment_info",
                extracted_full_data['summary_info'],
                current_ground_truth['summary_info']
            )

        # Evaluate Transactions (CONDUSEF Section 22)
        # This needs to be done per transaction type
        transaction_types = ["regular_transactions", "no_interest_installments", "interest_bearing_installments"]
        for tx_type in transaction_types:
            if tx_type in current_ground_truth.get('transactions', {}) and tx_type in extracted_full_data.get('transactions', {}):
                overall_results["transactions_evaluation"][tx_type] = self.evaluate_transactions(
                    extracted_full_data['transactions'][tx_type],
                    current_ground_truth['transactions'][tx_type],
                    tx_type
                )
        
        # Calculate overall accuracy (simple average of section accuracies for now)
        total_accuracy = 0
        num_evaluated_sections = 0
        for section_result in overall_results["sections"].values():
            total_accuracy += section_result.get("accuracy", 0)
            num_evaluated_sections += 1
        for tx_eval_result in overall_results["transactions_evaluation"].values():
            total_accuracy += tx_eval_result.get("f1_score", 0) # Using F1 for transactions
            num_evaluated_sections +=1
            
        overall_accuracy = total_accuracy / num_evaluated_sections if num_evaluated_sections > 0 else 0
        overall_results["overall_accuracy"] = overall_accuracy
        
        logger.info(f"Evaluation for {ground_truth_id}: Overall Accuracy = {overall_accuracy:.2f}")
        return overall_results

    def get_average_metrics(self, all_evaluation_results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates average metrics across multiple evaluation runs."""
        # Placeholder for aggregating metrics from multiple evaluations
        # e.g., average overall accuracy, average F1 for transactions, etc.
        if not all_evaluation_results: return {}
        
        avg_overall_accuracy = sum(res.get('overall_accuracy', 0) for res in all_evaluation_results) / len(all_evaluation_results)
        # Add more specific averages as needed
        return {"average_overall_accuracy": avg_overall_accuracy}

# Example Usage:
if __name__ == '__main__':
    # Mock ground truth data (simplified)
    mock_gt = [
        {
            "id": "statement1.pdf",
            "primary_info": {
                "account_number": "1234567812345678",
                "statement_period_start": "2023-01-01T00:00:00", # Store as ISO strings or datetime objects
                "payment_due_date": "2023-02-20T00:00:00",
                "pay_to_avoid_interest": 5000.00
            },
            "transactions": {
                "regular_transactions": [
                    {"operation_date": "2023-01-02T00:00:00", "description": "OXXO", "amount": 55.80},
                    {"operation_date": "2023-01-03T00:00:00", "description": "STARBUCKS", "amount": 120.00}
                ],
                "no_interest_installments": []
            }
        }
    ]

    # Mock extracted data (from CondusefParser)
    mock_extracted = {
        "document_type": "credit_card_statement_condusef",
        "primary_info": {
            "account_number": "1234567812345678", # Match
            "statement_period_start": datetime.strptime("2023-01-01", "%Y-%m-%d"), # Match (type diff handled)
            "payment_due_date": datetime.strptime("2023-02-20", "%Y-%m-%d"), # Match
            "pay_to_avoid_interest": 5000.0 # Match (type diff handled)
        },
        "transactions": {
            "regular_transactions": [
                {"operation_date": datetime.strptime("2023-01-02", "%Y-%m-%d"), "description": "OXXO", "amount": 55.80},
                # Missing STARBUCKS transaction
            ],
            "no_interest_installments": [],
            "interest_bearing_installments": []
        },
        "summary_info": {},
        "errors": []
    }

    eval_framework = ExtractionEvaluationFramework(ground_truth_data=mock_gt)
    results = eval_framework.run_evaluation(extracted_full_data=mock_extracted, ground_truth_id="statement1.pdf")
    
    import json
    print("--- Evaluation Results ---")
    print(json.dumps(results, indent=2, default=str)) # Use default=str for datetime objects
