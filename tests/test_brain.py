"""Tests for local brain decisions that do not require an API key."""

import unittest

from core.brain import FridayBrain


class FridayBrainSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_prompt_is_rejected(self):
        brain = FridayBrain(client=object())
        result = await brain.think("   ")
        self.assertEqual(result["status"], "ERROR")

    async def test_risky_prompt_waits_for_confirmation(self):
        brain = FridayBrain(client=object())
        result = await brain.think("Delete the old report")
        self.assertEqual(result["status"], "WAITING_FOR_USER_APPROVAL")
        self.assertEqual(brain.pending_prompt, "Delete the old report")

    async def test_rejected_confirmation_clears_pending_prompt(self):
        brain = FridayBrain(client=object())
        await brain.think("Restart the computer")
        result = await brain.resolve_confirmation(False)
        self.assertEqual(result["status"], "CANCELLED")
        self.assertIsNone(brain.pending_prompt)

    def test_latest_observed_frame_is_attached_to_every_request(self):
        image = object()
        observer = type("Observer", (), {"latest_image": lambda self: image})()
        brain = FridayBrain(client=object(), observer=observer)
        self.assertEqual(brain._message_with_screen("Explain Python decorators"), ["Explain Python decorators", image])


if __name__ == "__main__":
    unittest.main()
