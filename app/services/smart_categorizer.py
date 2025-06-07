import re
import json
import httpx
from typing import List, Dict, Any, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SmartCategorizer:
    """
    Hybrid transaction categorizer using:
    1. Exact keyword matching (fastest)
    2. Smart pattern matching (fast + intelligent) 
    3. LLM categorization (for complex cases)
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model_name = "llama3.2:1b"  # Lightweight model
        self.llm_available = False
        
        # Nivel 1: Reglas exactas (más rápidas)
        self.exact_keywords = {
            # Tiendas de conveniencia
            'oxxo': 'alimentacion',
            'seven': 'alimentacion', 
            '7eleven': 'alimentacion',
            'circle k': 'alimentacion',
            'extra': 'alimentacion',
            
            # Supermercados
            'walmart': 'alimentacion',
            'soriana': 'alimentacion',
            'chedraui': 'alimentacion',
            'costco': 'alimentacion',
            'bodega aurrera': 'alimentacion',
            'superama': 'alimentacion',
            'heb': 'alimentacion',
            
            # Gasolineras
            'pemex': 'gasolineras',
            'shell': 'gasolineras',
            'bp': 'gasolineras',
            'mobil': 'gasolineras',
            'exxon': 'gasolineras',
            'chevron': 'gasolineras',
            
            # Servicios streaming/suscripciones
            'netflix': 'servicios',
            'spotify': 'servicios',
            'amazon prime': 'servicios',
            'disney': 'servicios',
            'hbo': 'servicios',
            'youtube premium': 'servicios',
            
            # Transporte
            'uber': 'transporte',
            'didi': 'transporte',
            'cabify': 'transporte',
            'beat': 'transporte',
            
            # Bancos/Transferencias
            'banamex': 'transferencias',
            'bbva': 'transferencias',
            'santander': 'transferencias',
            'hsbc': 'transferencias',
            'banorte': 'transferencias',
            'scotiabank': 'transferencias',
            'spei': 'transferencias',
            
            # Farmacias
            'farmacia': 'salud',
            'benavides': 'salud',
            'guadalajara': 'salud',
            'del ahorro': 'salud',
            'similares': 'salud',
        }
        
        # Nivel 2: Patrones inteligentes con contexto
        self.smart_patterns = [
            # Restaurantes y comida
            (r'\b(rest|restaurant|restaurante)\b', 'alimentacion'),
            (r'\b(taco|pizza|burger|comida|tacos)\b', 'alimentacion'),
            (r'\b(cafe|coffee|starbucks|caffenio)\b', 'alimentacion'),
            (r'\b(mcdonalds|kfc|subway|dominos)\b', 'alimentacion'),
            (r'\b(sushi|ramen|japanese|chino)\b', 'alimentacion'),
            
            # Salud
            (r'\bdr\s+[a-z]+', 'salud'),  # DR ISRAEL UBERETAGOYEN
            (r'\b(farm|farmacia|guadalajara|benavides)\b', 'salud'),
            (r'\b(hospital|clinica|laboratorio|dental)\b', 'salud'),
            (r'\b(medico|doctor|medicina)\b', 'salud'),
            
            # Gasolina y combustible
            (r'\bgas\s+', 'gasolineras'),  # GAS PARADOR
            (r'\bgasol\b', 'gasolineras'),  # GASOL SERV
            (r'\b(combustible|gasolina|diesel)\b', 'gasolineras'),
            (r'\bserv\s+(gas|gasol)', 'gasolineras'),
            
            # Transporte
            (r'\buber\s+(trip|eats)', 'transporte'),
            (r'\b(taxi|metro|parking|estacionamiento)\b', 'transporte'),
            (r'\b(autobus|camion|pesero)\b', 'transporte'),
            (r'\bstr\*uber', 'transporte'),  # STR*UBER patterns
            
            # Entretenimiento
            (r'\b(cine|cinepolis|cinemex)\b', 'entretenimiento'),
            (r'\b(bar|club|antro|cantina)\b', 'entretenimiento'),
            (r'\b(juegos|casino|poker)\b', 'entretenimiento'),
            (r'\b(concierto|teatro|show)\b', 'entretenimiento'),
            
            # Servicios financieros y pagos
            (r'bmovil\.pago', 'transferencias'),
            (r'\bspei\b', 'transferencias'),
            (r'\b(transferencia|deposito|retiro)\b', 'transferencias'),
            (r'\b(cajero|atm|disposicion)\b', 'transferencias'),
            
            # Intereses/comisiones
            (r'\b(interes|comision|iva|cargo|fee)\b', 'intereses_comisiones'),
            (r'\b(anualidad|membresia|cuota)\b', 'intereses_comisiones'),
            
            # Ropa y tiendas departamentales
            (r'\b(liverpool|palacio|sears|c&a)\b', 'ropa'),
            (r'\b(zara|h&m|forever|pull)\b', 'ropa'),
            
            # Servicios públicos
            (r'\b(cfe|luz|electrica)\b', 'servicios'),
            (r'\b(telmex|telcel|movistar|at&t)\b', 'servicios'),
            (r'\b(sky|izzi|totalplay|megacable)\b', 'servicios'),
            (r'\b(agua|predial|gas natural)\b', 'servicios'),
            
            # Educación
            (r'\b(escuela|universidad|colegio|instituto)\b', 'educacion'),
            (r'\b(curso|capacitacion|libro|libreria)\b', 'educacion'),
            
            # Seguros
            (r'\b(seguro|axa|gnp|qualitas|hdi)\b', 'seguros'),
            (r'\b(poliza|prima|deducible)\b', 'seguros'),
        ]
        
        # Categorías disponibles con descripciones para el LLM
        self.categories_description = {
            'alimentacion': 'Food, groceries, restaurants, convenience stores, supermarkets',
            'gasolineras': 'Gas stations, fuel, gasoline, diesel',
            'servicios': 'Utilities, internet, phone, streaming services, electricity, water', 
            'salud': 'Healthcare, pharmacies, doctors, medical, hospitals, dental',
            'transporte': 'Transportation, uber, taxi, public transport, parking',
            'entretenimiento': 'Entertainment, movies, bars, games, concerts, shows',
            'ropa': 'Clothing, fashion, department stores, shoes, accessories',
            'educacion': 'Education, schools, books, courses, universities',
            'transferencias': 'Bank transfers, payments, ATM, deposits, SPEI',
            'seguros': 'Insurance, policies, premiums, deductibles',
            'intereses_comisiones': 'Interest, fees, bank charges, annual fees',
            'otros': 'Other/Miscellaneous transactions'
        }

    async def setup_model(self) -> bool:
        """Initialize the LLM model"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test if Ollama is available
                response = await client.get(f"{self.ollama_url}/api/version")
                if response.status_code != 200:
                    logger.warning("Ollama server not available")
                    return False
                
                # Check if model exists
                models_response = await client.get(f"{self.ollama_url}/api/tags")
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    model_exists = any(
                        model['name'].startswith(self.model_name) 
                        for model in models_data.get('models', [])
                    )
                    
                    if not model_exists:
                        logger.info(f"Pulling model {self.model_name}...")
                        # Pull model
                        pull_response = await client.post(
                            f"{self.ollama_url}/api/pull",
                            json={"name": self.model_name}
                        )
                        if pull_response.status_code != 200:
                            logger.error("Failed to pull model")
                            return False
                        
                        logger.info("Model downloaded successfully")
                
                # Test the model
                test_response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "stream": False
                    }
                )
                
                if test_response.status_code == 200:
                    logger.info("LLM model is ready")
                    self.llm_available = True
                    return True
                    
        except Exception as e:
            logger.error(f"Error setting up LLM: {e}")
        
        self.llm_available = False
        return False

    async def categorize_transaction(self, description: str, amount: float) -> Tuple[str, float, str]:
        """
        Categorize a transaction using hybrid approach
        Returns: (category, confidence, method_used)
        """
        description_clean = description.lower().strip()
        
        # Nivel 1: Exact keyword match
        for keyword, category in self.exact_keywords.items():
            if keyword in description_clean:
                logger.debug(f"Exact match: '{keyword}' -> {category}")
                return category, 1.0, "exact_match"
        
        # Nivel 2: Smart pattern matching
        for pattern, category in self.smart_patterns:
            if re.search(pattern, description_clean, re.IGNORECASE):
                logger.debug(f"Pattern match: '{pattern}' -> {category}")
                return category, 0.8, "pattern_match"
        
        # Nivel 3: LLM for complex cases (only if available)
        if self.llm_available:
            try:
                return await self._llm_categorize(description, amount)
            except Exception as e:
                logger.error(f"LLM categorization failed: {e}")
        
        # Fallback to "otros" if no matches found
        logger.debug(f"No matches found for: {description}")
        return "otros", 0.3, "fallback"

    async def _llm_categorize(self, description: str, amount: float) -> Tuple[str, float, str]:
        """Use LLM to categorize complex transactions"""
        
        # Create prompt with context
        categories_list = "\n".join([
            f"- {cat}: {desc}" 
            for cat, desc in self.categories_description.items()
        ])
        
        prompt = f"""You are a financial transaction categorizer for Mexican bank statements.

Transaction: "{description}"
Amount: ${amount:,.2f}

Available categories:
{categories_list}

Based on the transaction description and amount, classify this transaction into ONE of the above categories.

Consider Mexican context: stores, banks, and services commonly used in Mexico.

Respond with ONLY the category name (e.g., "alimentacion", "gasolineras", etc.). 
If uncertain, use "otros".

Category:"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.model_name,
                        "messages": [{
                            "role": "user", 
                            "content": prompt
                        }],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Low temperature for consistent results
                            "top_p": 0.9,
                            "num_ctx": 2048
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    predicted_category = result['message']['content'].strip().lower()
                    
                    # Validate the predicted category
                    if predicted_category in self.categories_description:
                        logger.debug(f"LLM categorized '{description}' as '{predicted_category}'")
                        return predicted_category, 0.7, "llm"
                    else:
                        # Try to find closest match
                        for category in self.categories_description.keys():
                            if category in predicted_category:
                                logger.debug(f"LLM fuzzy match: '{predicted_category}' -> '{category}'")
                                return category, 0.6, "llm_fuzzy"
                        
                        logger.warning(f"LLM returned invalid category: {predicted_category}")
                        return "otros", 0.4, "llm_fallback"
                else:
                    logger.error(f"LLM API error: {response.status_code}")
                    return "otros", 0.3, "llm_error"
                    
        except Exception as e:
            logger.error(f"LLM categorization error: {e}")
            return "otros", 0.3, "llm_error"

    async def categorize_transactions(self, transactions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Categorize all transactions and return stats"""
        categorized = []
        
        stats = {
            'exact_match': 0,
            'pattern_match': 0, 
            'llm': 0,
            'llm_fuzzy': 0,
            'fallback': 0,
            'llm_error': 0
        }
        
        total_start_time = datetime.now()
        
        for transaction in transactions:
            description = transaction.get('description', '')
            amount = transaction.get('amount', 0)
            
            # Categorize
            category, confidence, method = await self.categorize_transaction(description, amount)
            
            # Update stats
            if method in stats:
                stats[method] += 1
            else:
                stats['fallback'] += 1
            
            # Add categorization info while preserving original fields
            # Make sure transaction_date is preserved if it exists
            if 'date' in transaction and 'transaction_date' not in transaction:
                transaction['transaction_date'] = transaction['date']
                
            transaction.update({
                'category': category,
                'confidence': confidence,
                'categorization_method': method,
                'is_credit': self._is_credit_transaction(description),
                'is_recurring': self._is_recurring_transaction(description),
                'merchant_name': self._extract_merchant_name(description)
            })
            
            categorized.append(transaction)
        
        total_time = (datetime.now() - total_start_time).total_seconds()
        
        # Calculate additional stats
        confidences = [t.get('confidence', 0) for t in categorized]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        categorization_stats = {
            'methods_used': stats,
            'average_confidence': round(avg_confidence, 3),
            'total_transactions': len(categorized),
            'llm_usage_percentage': round(
                (stats.get('llm', 0) + stats.get('llm_fuzzy', 0)) / len(categorized) * 100, 1
            ) if categorized else 0,
            'processing_time_seconds': round(total_time, 2),
            'llm_available': self.llm_available
        }
        
        logger.info(f"Categorization completed: {categorization_stats}")
        return categorized, categorization_stats

    def _is_credit_transaction(self, description: str) -> bool:
        """Detect if transaction is a credit/payment"""
        credit_patterns = [
            r'\bpago\b',
            r'\babono\b', 
            r'\bdeposito\b',
            r'\btransferencia\s+recibida\b',
            r'bmovil\.pago',
            r'\bcredito\b',
            r'\bingreso\b'
        ]
        
        description_lower = description.lower()
        return any(re.search(pattern, description_lower) for pattern in credit_patterns)

    def _is_recurring_transaction(self, description: str) -> bool:
        """Detect recurring transactions"""
        recurring_keywords = [
            'netflix', 'spotify', 'amazon prime', 'disney', 'hbo',
            'cfe', 'telmex', 'telcel', 'sky', 'izzi', 'totalplay',
            'seguro', 'gym', 'gimnasio', 'renta', 'colegiatura',
            'membresia', 'suscripcion', 'anualidad'
        ]
        
        description_lower = description.lower()
        return any(keyword in description_lower for keyword in recurring_keywords)

    def _extract_merchant_name(self, description: str) -> Optional[str]:
        """Extract clean merchant name from description"""
        if not description:
            return None
        
        # Remove common prefixes/suffixes
        clean_desc = description.upper()
        
        # Remove common noise
        noise_patterns = [
            r'^(STR\*|STRIPE\s*\*|CLIP\s*MX\s*\*)',
            r'\s*;\s*Tarjeta\s+Digital.*$',
            r'\s*\d+$',  # Trailing numbers
            r'^\s*(REST|RESTAURANTE)\s+',  # Restaurant prefixes
        ]
        
        for pattern in noise_patterns:
            clean_desc = re.sub(pattern, '', clean_desc)
        
        # Extract first meaningful part (usually merchant name)
        parts = clean_desc.split()
        if parts:
            # Take first 2-3 words as merchant name
            merchant = ' '.join(parts[:3]).strip()
            return merchant if len(merchant) > 2 else None
        
        return None

    def get_categorization_summary(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of categorized transactions"""
        if not transactions:
            return {}
        
        # Group by category
        category_summary = {}
        total_amount = 0
        
        for transaction in transactions:
            category = transaction.get('category', 'otros')
            amount = transaction.get('amount', 0)
            
            if category not in category_summary:
                category_summary[category] = {
                    'count': 0,
                    'total_amount': 0,
                    'transactions': []
                }
            
            category_summary[category]['count'] += 1
            category_summary[category]['total_amount'] += amount
            category_summary[category]['transactions'].append(transaction)
            total_amount += amount
        
        # Calculate percentages
        for category in category_summary:
            if total_amount != 0:
                percentage = (category_summary[category]['total_amount'] / total_amount) * 100
                category_summary[category]['percentage'] = round(percentage, 2)
            else:
                category_summary[category]['percentage'] = 0
        
        return {
            'total_transactions': len(transactions),
            'total_amount': round(total_amount, 2),
            'categories': category_summary,
            'top_categories': sorted(
                category_summary.items(), 
                key=lambda x: abs(x[1]['total_amount']), 
                reverse=True
            )[:5]
        }
