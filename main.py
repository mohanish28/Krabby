"""
Command-line version of the Council system.
For GUI version, run: python main_gui.py
"""
from council import Council
from council.utils.logging import setup_logging, get_logger
from council.utils.validation import validate_input, ValidationError
from config import MODELS, DISCUSSION_ROUNDS
import json
import ollama

# Setup logging
setup_logging(level="INFO")
logger = get_logger("main")

def check_ollama_connection():
    """Check if Ollama is running"""
    try:
        client = ollama.Client()
        models_list = client.list()
        
        # Ollama client.list() returns a dict with 'models' key
        if isinstance(models_list, dict) and 'models' in models_list:
            models = models_list['models']
            # Extract base names (remove :latest, :4b, etc. tags) for matching
            available_models = []
            for model in models:
                # Each model is a dict with 'model' or 'name' key
                model_name = model.get('model') or model.get('name', '')
                if model_name:
                    base_name = model_name.split(':')[0]
                    if base_name not in available_models:
                        available_models.append(base_name)
            
            if available_models:
                print(f"  ✓ Ollama detected: {len(available_models)} models found")
                print(f"  ✓ Ollama models: {available_models}")
                return True, available_models
            else:
                print(f"  ✗ Ollama is running but no models found")
                return True, []
        else:
            print(f"  ✗ Ollama is running but no models found")
            return True, []  # Ollama is running but no models
    except Exception as e:
        print(f"  ✗ Ollama not available: {str(e)}")
        print(f"  Make sure Ollama is running. Start it with: ollama serve")
        return False, []

def check_api_keys():
    """Check which API keys are available"""
    from config import (
        HUGGINGFACE_API_KEY, GROQ_API_KEY, GOOGLE_API_KEY,
        TOGETHER_API_KEY, COHERE_API_KEY
    )
    
    available = {}
    if HUGGINGFACE_API_KEY:
        available["HuggingFace"] = "✓"
    else:
        available["HuggingFace"] = "✗ (Get free key at: https://huggingface.co/settings/tokens)"
    
    if GROQ_API_KEY:
        available["Groq"] = "✓"
    else:
        available["Groq"] = "✗ (Get free key at: https://console.groq.com/keys)"
    
    if GOOGLE_API_KEY:
        available["Google Gemini"] = "✓"
    else:
        available["Google Gemini"] = "✗ (Get free key at: https://makersuite.google.com/app/apikey)"
    
    if TOGETHER_API_KEY:
        available["Together AI"] = "✓"
    else:
        available["Together AI"] = "✗ (Get free key at: https://api.together.xyz/settings/api-keys)"
    
    if COHERE_API_KEY:
        available["Cohere"] = "✓"
    else:
        available["Cohere"] = "✗ (Get free key at: https://dashboard.cohere.com/api-keys)"
    
    return available

def main():
    print("=" * 60)
    print("COUNCIL OF LLM MODELS - PARLIAMENTARY SYSTEM")
    print("=" * 60)
    print()
    
    # Check Ollama
    print("Checking Ollama connection...")
    is_ollama_connected, ollama_models = check_ollama_connection()
    if is_ollama_connected:
        print(f"✓ Ollama is running. Available models: {ollama_models}")
    else:
        print("✗ Ollama is not running (optional - only needed for local models)")
    print()
    
    # Check API keys
    print("Checking API keys...")
    api_status = check_api_keys()
    for service, status in api_status.items():
        print(f"  {service}: {status}")
    print()
    
    # Auto-detect ALL Ollama models and combine with API models
    available_models = []
    skipped_models = []
    
    # 1. Auto-detect ALL Ollama models (not just from config)
    ollama_full_models = []
    if is_ollama_connected:
        try:
            client = ollama.Client()
            models_list = client.list()
            if isinstance(models_list, dict) and 'models' in models_list:
                for model in models_list['models']:
                    model_name = model.get('model') or model.get('name', '')
                    if model_name:
                        ollama_full_models.append(model_name)
                        # Create model config dynamically
                        model_config = {
                            "name": model_name,
                            "provider": "ollama"
                        }
                        available_models.append(model_config)
                        print(f"✓ Auto-detected Ollama model: {model_name}")
        except Exception as e:
            print(f"⚠️ Error getting full Ollama model list: {e}")
    
    # 2. Add API models from config (if they have keys)
    for model_config in MODELS:
        model_name = model_config["name"]
        provider = model_config["provider"]
        
        if provider == "ollama":
            # Skip - we already auto-detected all Ollama models above
            continue
        else:
            # For API models, check if API key exists
            api_key = model_config.get("api_key", "")
            if api_key:
                # Check if not already added (avoid duplicates)
                if not any(m["name"] == model_name and m["provider"] == provider 
                          for m in available_models):
                    available_models.append(model_config)
                    print(f"✓ {provider} model '{model_name}' has API key")
            else:
                skipped_models.append(f"{model_name} (no API key)")
                print(f"✗ {provider} model '{model_name}' - no API key")
    
    if skipped_models:
        print(f"\nSkipped {len(skipped_models)} model(s): {', '.join(skipped_models)}")
    
    if not available_models:
        print("\nERROR: No models are available!")
        print("\nTo get started:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. OR get free API keys (see warnings above)")
        print("3. Add API keys to .env file")
        return
    
    print(f"\nUsing {len(available_models)} available model(s)")
    print("Initializing council...")
    
    # Initialize the council
    try:
        council = Council(available_models, discussion_rounds=DISCUSSION_ROUNDS)
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    print("=" * 60)
    print()
    
    # Get input from user
    input_text = input("Enter your question or topic for the council: ")
    print()
    
    # Validate input
    try:
        input_text = validate_input(input_text, max_length=10000, min_length=1)
    except ValidationError as e:
        print(f"\n❌ Invalid input: {e}")
        print("Please ensure your input is between 1 and 10,000 characters.")
        return
    
    # Run the deliberation process
    logger.info(f"Starting deliberation for input: {input_text[:50]}...")
    try:
        result = council.deliberate(input_text)
    except Exception as e:
        logger.error(f"Deliberation failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return
    
    # Display results
    print("\n" + "=" * 60)
    print("COUNCIL DELIBERATION RESULTS")
    print("=" * 60)
    print()
    
    print("INITIAL OPINIONS:")
    print("-" * 60)
    for i, opinion in enumerate(result["initial_opinions"], 1):
        print(f"\nModel {i} ({opinion['model']}):")
        content = opinion["content"]
        if len(content) > 300:
            print(content[:300] + "...")
        else:
            print(content)
    
    print("\n" + "=" * 60)
    print("VOTING RESULTS:")
    print("-" * 60)
    print(f"Total Votes: {result['results']['total_votes']}")
    print(f"Winning Opinion ID: {result['results']['winner_id']}")
    print(f"Winning Votes: {result['results']['winning_votes']}")
    print("\nVote Breakdown:")
    for op_id, count in result['results']['vote_counts'].items():
        print(f"  {op_id}: {count} vote(s)")
    
    print("\n" + "=" * 60)
    print("FINAL OUTPUT (WINNING OPINION):")
    print("=" * 60)
    print(result["final_output"])
    print()
    
    # Optionally save full results to file
    save = input("Save full results to file? (y/n): ").lower()
    if save == 'y':
        filename = "council_results.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")

if __name__ == "__main__":
    main()

