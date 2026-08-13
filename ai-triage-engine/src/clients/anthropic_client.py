import anthropic
import logging

logger = logging.getLogger("triage")


class AnthropicClient:
    """
    Wraps the Claude API for alert triage.

    NOTE: Claude's response can contain multiple content blocks
    (e.g. a ThinkingBlock followed by a TextBlock), not just a single
    text block at index 0. Earlier versions of this client assumed
    response.content[0].text, which crashed with
    "'ThinkingBlock' object has no attribute 'text'" whenever the
    model returned reasoning content before its final answer. Fixed
    by iterating all content blocks and extracting the one with
    type == "text" rather than assuming positional structure.
    """

    def __init__(self, api_key, model, max_tokens=1024):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def get_triage(self, prompt):
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            text = ""
            for block in response.content:
                if block.type == "text":
                    text = block.text
                    break

            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }

            logger.info(f"Claude API call succeeded — "
                        f"input_tokens={usage['input_tokens']}, "
                        f"output_tokens={usage['output_tokens']}")

            return {
                "raw_text": text,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return None
