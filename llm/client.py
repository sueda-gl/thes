"""
Async OpenAI client with rate limiting and retry logic.
"""
import asyncio
from typing import Optional, List, Dict, Any
from openai import AsyncAzureOpenAI
from aiolimiter import AsyncLimiter
import config


class LLMClient:
    """Async LLM client for agent decision-making."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        max_concurrent: int = None
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: Azure OpenAI API key (defaults to config)
            model: Model name (defaults to config)
            temperature: Sampling temperature (defaults to config)
            max_tokens: Max tokens per response (defaults to config)
            max_concurrent: Max concurrent requests (defaults to config)
        """
        self.api_key = api_key or config.AZURE_OPENAI_API_KEY
        self.model = model or config.LLM_MODEL
        self.temperature = temperature or config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self.max_concurrent = max_concurrent or config.LLM_MAX_CONCURRENT
        
        # Initialize Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=config.AZURE_API_VERSION,
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT
        )
        
        # Rate limiter
        self.limiter = AsyncLimiter(self.max_concurrent, 1)
        
        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.failed_requests = 0
    
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = None
    ) -> Optional[str]:
        """
        Generate text from prompt with retry logic.
        
        Args:
            prompt: Input prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            max_retries: Max retry attempts (defaults to config)
        
        Returns:
            Generated text or None if all retries fail
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        retries = max_retries if max_retries is not None else config.LLM_MAX_RETRIES
        
        for attempt in range(retries):
            try:
                async with self.limiter:
                    # Add timeout (longer for Azure)
                    response = await asyncio.wait_for(
                        self.client.chat.completions.create(
                            model=self.model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=temp,
                            max_tokens=tokens
                        ),
                        timeout=60.0  # 60 second timeout for Azure
                    )
                    
                    # Track usage (VERIFIED: All tokens counted)
                    if hasattr(response, 'usage') and response.usage:
                        self.total_input_tokens += response.usage.prompt_tokens
                        self.total_output_tokens += response.usage.completion_tokens
                    else:
                        # Safety: Log if usage data missing
                        print(f"⚠️  Warning: Response missing usage data (tokens not counted)")
                    
                    self.total_requests += 1
                    
                    # Extract response text
                    return response.choices[0].message.content
            
            except asyncio.TimeoutError:
                print(f"⚠️  Request timeout (attempt {attempt + 1}/{retries})")
                if attempt < retries - 1:
                    wait_time = (2 ** attempt) * 2
                    print(f"   Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    self.failed_requests += 1
                    print(f"❌ Request failed after {retries} timeout attempts")
                    return None
            
            except Exception as e:
                error_msg = str(e)
                
                # CRITICAL: Detect Azure content filter errors
                # These won't be fixed by retrying the same prompt
                is_content_filter = (
                    'content_filter' in error_msg.lower() or
                    'responsibleaipolicyviolation' in error_msg.lower() or
                    'the response was filtered' in error_msg.lower()
                )
                
                if is_content_filter:
                    # Content filter triggered - retrying same prompt won't help
                    print(f"🛑 Content filter triggered (no retry): {error_msg[:150]}")
                    self.failed_requests += 1
                    return None  # Skip immediately, don't waste retries
                
                # For other errors, retry with backoff
                print(f"⚠️  API Error (attempt {attempt + 1}/{retries}): {error_msg[:100]}")
                
                if attempt < retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 2
                    print(f"   Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted
                    self.failed_requests += 1
                    print(f"❌ LLM request failed after {retries} attempts: {error_msg}")
                    return None
    
    async def generate_batch(
        self,
        prompts: List[str],
        batch_size: Optional[int] = None
    ) -> List[Optional[str]]:
        """
        Generate responses for multiple prompts in batches.
        
        Args:
            prompts: List of prompts
            batch_size: Size of each batch (defaults to max_concurrent)
        
        Returns:
            List of responses (same order as prompts)
        """
        batch_size = batch_size or self.max_concurrent
        results = []
        
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                self.generate(prompt) for prompt in batch
            ])
            results.extend(batch_results)
        
        return results
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total_cost = (
            self.total_input_tokens * config.INPUT_TOKEN_COST +
            self.total_output_tokens * config.OUTPUT_TOKEN_COST
        )
        
        return {
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_input_tokens + self.total_output_tokens,
            'estimated_cost_usd': round(total_cost, 4),
            'success_rate': (
                (self.total_requests - self.failed_requests) / self.total_requests
                if self.total_requests > 0 else 0
            )
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_requests = 0
        self.failed_requests = 0
    
    async def close(self):
        """Close the client."""
        await self.client.close()

