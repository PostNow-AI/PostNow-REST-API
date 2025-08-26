# Credit System Integration with AI Models

This document explains how the credit system is integrated with AI model calls in the Sonora REST API.

## Overview

The credit system automatically validates user credits before AI operations and deducts them after successful completion. Users can choose from multiple AI models with different cost structures.

## How It Works

### 1. Credit Validation Flow

```
User Request → Estimate Tokens → Validate Credits → Execute AI Call → Deduct Credits
```

1. **Estimate Tokens**: Calculate approximate tokens needed for the operation
2. **Validate Credits**: Check if user has sufficient credits
3. **Execute AI Call**: Proceed with the AI operation if credits are sufficient
4. **Deduct Credits**: Remove used credits after successful completion

### 2. AI Model Selection

The system automatically selects the most cost-effective model the user can afford:

- **Cost-based Selection**: Models are sorted by cost per token
- **Credit Validation**: Only models within user's budget are considered
- **Provider Preference**: Users can specify preferred AI providers

## Configuration

### 1. Populate AI Models

Run the management command to populate AI models with their configurations:

```bash
python manage.py populate_ai_models
```

This creates models with different cost structures:

| Model | Provider | Cost per Token | Use Case |
|-------|----------|----------------|----------|
| gemini-1.5-flash | Google | 0.000001 | Fast, cost-effective generation |
| gemini-1.5-pro | Google | 0.000002 | Higher quality, longer context |
| claude-3-haiku | Anthropic | 0.00000025 | Ultra-cheap, basic tasks |
| claude-3-sonnet | Anthropic | 0.000003 | High quality, long context |
| gpt-3.5-turbo | OpenAI | 0.000002 | Balanced quality/cost |
| gpt-4 | OpenAI | 0.00003 | Premium quality, expensive |

### 2. Environment Variables

Ensure these environment variables are set:

```bash
# For Gemini (Google)
GEMINI_API_KEY=your_gemini_api_key

# For OpenAI
OPENAI_API_KEY=your_openai_api_key

# For Anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key
```

## API Endpoints

### 1. Get Available Models

```http
GET /api/ideabank/ai-models/
Authorization: Bearer <token>
```

**Response:**

```json
{
  "models": [
    {
      "name": "gemini-1.5-flash",
      "provider": "Google",
      "cost_per_token": 0.000001,
      "is_active": true,
      "estimated_cost_for_typical_use": 0.002,
      "can_afford": true
    }
  ],
  "user_credit_balance": 100.0,
  "typical_usage_tokens": 2000,
  "credit_currency": "credits"
}
```

### 2. Estimate Campaign Cost

```http
POST /api/ideabank/estimate-cost/
Authorization: Bearer <token>
Content-Type: application/json

{
  "config": {
    "platforms": ["instagram"],
    "objectives": ["awareness"],
    "product_description": "AI-powered marketing tool",
    "value_proposition": "Increase ROI by 300%",
    "campaign_urgency": "high"
  }
}
```

**Response:**

```json
{
  "estimated_tokens": 1850,
  "cost_estimates": [
    {
      "model_name": "gemini-1.5-flash",
      "provider": "Google",
      "estimated_tokens": 1850,
      "estimated_cost": 0.00185,
      "can_afford": true,
      "cost_per_token": 0.000001
    }
  ],
  "user_credit_balance": 100.0,
  "recommended_model": {
    "model_name": "gemini-1.5-flash",
    "can_afford": true
  }
}
```

### 3. Generate Campaign Ideas (with Credit Validation)

```http
POST /api/ideabank/generate-ideas/
Authorization: Bearer <token>
Content-Type: application/json

{
  "platforms": ["instagram"],
  "objectives": ["awareness"],
  "product_description": "AI-powered marketing tool",
  "value_proposition": "Increase ROI by 300%",
  "campaign_urgency": "high",
  "preferred_provider": "Google",
  "persona_age_range": "25-45",
  "persona_gender": "all",
  "persona_income_level": "middle",
  "persona_education_level": "bachelor",
  "persona_occupation": "marketing",
  "persona_interests": ["technology", "marketing"],
  "persona_pain_points": ["low ROI", "time consuming"],
  "persona_goals": ["increase conversions", "save time"],
  "persona_social_media_habits": "daily",
  "persona_purchasing_behavior": "research-driven"
}
```

## Credit Calculation

### Token Estimation

The system uses a conservative token estimation:

```
Estimated Tokens = (Text Length ÷ 4) × 3
```

This accounts for:

- Input tokens (prompt)
- Output tokens (response)
- Buffer for variations

### Cost Calculation

```
Cost = Tokens × Cost per Token
```

**Example:**

- Prompt: 500 characters
- Estimated tokens: (500 ÷ 4) × 3 = 375 tokens
- Using gemini-1.5-flash: 375 × 0.000001 = 0.000375 credits

## Error Handling

### Insufficient Credits

```json
{
  "error": "Insufficient credits for this operation. Please purchase more credits."
}
```

### Model Not Available

```json
{
  "error": "Model 'gpt-4' not found or not active"
}
```

## Best Practices

### 1. Credit Management

- **Monitor Usage**: Check credit balance before operations
- **Estimate Costs**: Use the estimate endpoint to plan usage
- **Choose Wisely**: Select models based on quality needs vs. cost

### 2. Model Selection

- **Budget-Friendly**: Use gemini-1.5-flash for routine tasks
- **High Quality**: Use claude-3-sonnet for complex content
- **Premium**: Use gpt-4 for critical campaigns

### 3. Token Optimization

- **Concise Prompts**: Shorter prompts = fewer tokens
- **Clear Instructions**: Specific prompts reduce response length
- **Batch Operations**: Generate multiple ideas in one call

## Troubleshooting

### Common Issues

1. **Credit Validation Fails**
   - Check user credit balance
   - Verify AI model is active
   - Ensure credit system is properly configured

2. **Model Not Found**
   - Run `python manage.py populate_ai_models`
   - Check database connectivity
   - Verify model names in requests

3. **High Token Costs**
   - Review prompt length
   - Consider using cheaper models
   - Optimize prompt structure

### Debug Information

Enable debug logging to see credit operations:

```python
import logging
logging.getLogger('CreditSystem').setLevel(logging.DEBUG)
```

## Future Enhancements

- **Dynamic Pricing**: Adjust costs based on demand
- **Credit Packages**: Bulk credit purchases
- **Usage Analytics**: Detailed cost breakdowns
- **Model Switching**: Automatic fallback to cheaper models
- **Credit Sharing**: Team credit pools
